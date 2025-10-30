"""
Project Drishti - Dispatch Logic Service
Handles intelligent dispatch of security units using Google Maps API for routing
"""

import os
import logging
import asyncio
import httpx
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import math

from services.firebase_service import FirebaseService
from utils.data_models import DispatchResponse, SeverityLevel, UnitStatus, Location

logger = logging.getLogger(__name__)

class DispatchService:
    """
    Intelligent dispatch system for security units with optimal routing
    """
    
    def __init__(self):
        """Initialize Dispatch service"""
        try:
            # Google Maps API configuration
            self.maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
            if not self.maps_api_key:
                logger.warning("Google Maps API key not found - distance calculations will be estimated")
            
            # Initialize Firebase service for data operations
            self.firebase = FirebaseService()
            
            # Dispatch configuration
            self.max_dispatch_distance_km = 10  # Maximum dispatch distance
            self.priority_response_times = {
                SeverityLevel.CRITICAL: 3,  # minutes
                SeverityLevel.HIGH: 5,
                SeverityLevel.MEDIUM: 8,
                SeverityLevel.LOW: 15
            }
            
            # Unit type capabilities
            self.unit_capabilities = {
                "patrol": ["general_response", "crowd_control"],
                "supervisor": ["incident_command", "crowd_control", "general_response"],
                "medical": ["medical_emergency", "first_aid"],
                "fire": ["fire_hazard", "evacuation"],
                "k9": ["suspicious_activity", "search"],
                "tactical": ["security_breach", "high_risk_response"]
            }
            
            logger.info("✅ Dispatch service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Dispatch service: {e}")
            raise

    async def dispatch_units(
        self,
        incident_id: str,
        unit_ids: List[str] = None,
        priority: SeverityLevel = SeverityLevel.MEDIUM,
        instructions: Optional[str] = None,
        auto_select: bool = False
    ) -> DispatchResponse:
        """
        Dispatch security units to an incident
        """
        try:
            logger.info(f"Dispatching units for incident {incident_id}")
            
            # Get incident details
            incident = self.firebase.get_document("incidents", incident_id)
            if not incident:
                raise ValueError(f"Incident {incident_id} not found")
            
            # Auto-select units if not specified
            if not unit_ids or auto_select:
                unit_ids = await self._auto_select_units(incident, priority)
            
            if not unit_ids:
                return DispatchResponse(
                    dispatch_id="",
                    units_dispatched=[],
                    estimated_arrival_times={},
                    total_response_time=0,
                    status="failed",
                    errors=["No suitable units available for dispatch"]
                )
            
            # Generate dispatch ID
            dispatch_id = f"dispatch_{incident_id}_{int(datetime.now().timestamp())}"
            
            # Get unit details and calculate routes
            dispatch_results = []
            estimated_times = {}
            
            for unit_id in unit_ids:
                unit_result = await self._dispatch_single_unit(
                    unit_id, incident, dispatch_id, priority, instructions
                )
                dispatch_results.append(unit_result)
                
                if unit_result["success"]:
                    estimated_times[unit_id] = unit_result["estimated_arrival"]
            
            # Record dispatch in database
            dispatch_record = {
                "dispatch_id": dispatch_id,
                "incident_id": incident_id,
                "units_requested": unit_ids,
                "units_dispatched": [r["unit_id"] for r in dispatch_results if r["success"]],
                "priority": priority.value,
                "instructions": instructions,
                "timestamp": self.firebase.get_server_timestamp(),
                "status": "dispatched",
                "estimated_arrival_times": estimated_times
            }
            
            self.firebase.add_document("dispatches", dispatch_record)
            
            # Compile response
            successful_units = [r["unit_id"] for r in dispatch_results if r["success"]]
            errors = [r["error"] for r in dispatch_results if not r["success"]]
            
            status = "dispatched" if successful_units else "failed"
            if successful_units and errors:
                status = "partial"
            
            # --- NEW CORRECTED CODE ---

            # Round the estimated times to the nearest whole number (integer)
            rounded_estimated_times = {unit_id: round(t) for unit_id, t in estimated_times.items()}
            total_response_time = round(min(estimated_times.values())) if estimated_times else 0
            
            logger.info(f"Dispatch completed: {len(successful_units)}/{len(unit_ids)} units dispatched")
            
            return DispatchResponse(
                dispatch_id=dispatch_id,
                units_dispatched=successful_units,
                estimated_arrival_times=rounded_estimated_times, # Sending rounded integers
                total_response_time=total_response_time,        # Sending a rounded integer
                status=status,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Dispatch failed for incident {incident_id}: {e}")
            return DispatchResponse(
                dispatch_id="",
                units_dispatched=[],
                estimated_arrival_times={},
                total_response_time=0,
                status="failed",
                errors=[str(e)]
            )

    async def _auto_select_units(
        self, 
        incident: Dict[str, Any], 
        priority: SeverityLevel
    ) -> List[str]:
        """
        Automatically select best units for incident response
        """
        try:
            # Get all available units
            available_units = self.firebase.get_collection_with_filters(
                "security_units",
                filters={"status": UnitStatus.AVAILABLE.value}
            )
            
            if not available_units:
                logger.warning("No available units for auto-selection")
                return []
            
            # Score units based on suitability
            unit_scores = []
            incident_location = Location(**incident["location"])
            incident_type = incident.get("type", "general")
            
            for unit in available_units:
                score = await self._calculate_unit_score(
                    unit, incident_location, incident_type, priority
                )
                unit_scores.append((unit["id"], score, unit))
            
            # Sort by score (highest first)
            unit_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Select units based on incident severity
            num_units_needed = self._determine_units_needed(incident_type, priority)
            selected_units = [unit_id for unit_id, score, unit in unit_scores[:num_units_needed]]
            
            logger.info(f"Auto-selected {len(selected_units)} units: {selected_units}")
            return selected_units
            
        except Exception as e:
            logger.error(f"Auto unit selection failed: {e}")
            return []

    async def _calculate_unit_score(
        self,
        unit: Dict[str, Any],
        incident_location: Location,
        incident_type: str,
        priority: SeverityLevel
    ) -> float:
        """
        Calculate suitability score for a unit
        """
        try:
            score = 0.0
            
            # Distance score (closer is better)
            unit_location = Location(**unit["location"])
            distance_km = await self._calculate_distance(unit_location, incident_location)
            
            if distance_km <= self.max_dispatch_distance_km:
                distance_score = (self.max_dispatch_distance_km - distance_km) / self.max_dispatch_distance_km
                score += distance_score * 40  # 40% weight for distance
            else:
                return 0.0  # Too far away
            
            # Capability score
            unit_type = unit.get("type", "patrol")
            unit_capabilities = self.unit_capabilities.get(unit_type, ["general_response"])
            
            if incident_type in unit_capabilities or "general_response" in unit_capabilities:
                score += 30  # 30% weight for capability match
            
            # Equipment score
            unit_equipment = unit.get("equipment", [])
            incident_equipment_needs = self._get_equipment_needs(incident_type)
            
            equipment_matches = len(set(unit_equipment) & set(incident_equipment_needs))
            if incident_equipment_needs:
                equipment_score = equipment_matches / len(incident_equipment_needs)
                score += equipment_score * 20  # 20% weight for equipment
            
            # Experience/rank score
            unit_rank = unit.get("rank", "officer")
            rank_scores = {"supervisor": 10, "senior": 7, "officer": 5, "trainee": 2}
            score += rank_scores.get(unit_rank, 5)  # 10% weight for experience
            
            return score
            
        except Exception as e:
            logger.error(f"Unit scoring failed: {e}")
            return 0.0

    async def _dispatch_single_unit(
        self,
        unit_id: str,
        incident: Dict[str, Any],
        dispatch_id: str,
        priority: SeverityLevel,
        instructions: Optional[str]
    ) -> Dict[str, Any]:
        """
        Dispatch a single unit to an incident
        """
        try:
            # Get unit details
            unit = self.firebase.get_document("security_units", unit_id)
            if not unit:
                return {
                    "unit_id": unit_id,
                    "success": False,
                    "error": f"Unit {unit_id} not found"
                }
            
            # Check if unit is available
            if unit.get("status") != UnitStatus.AVAILABLE.value:
                return {
                    "unit_id": unit_id,
                    "success": False,
                    "error": f"Unit {unit_id} is not available (status: {unit.get('status')})"
                }
            
            # Calculate route and estimated arrival
            unit_location = Location(**unit["location"])
            incident_location = Location(**incident["location"])
            
            route_info = await self._calculate_route(unit_location, incident_location)
            
            # Update unit status
            unit_update = {
                "status": UnitStatus.DISPATCHED.value,
                "current_assignment": incident["id"],
                "dispatch_id": dispatch_id,
                "dispatch_timestamp": self.firebase.get_server_timestamp(),
                "last_updated": self.firebase.get_server_timestamp()
            }
            
            self.firebase.update_document("security_units", unit_id, unit_update)
            
            # Create dispatch notification
            await self._send_dispatch_notification(
                unit, incident, route_info, instructions
            )
            
            logger.info(f"Unit {unit_id} dispatched successfully")
            
            return {
                "unit_id": unit_id,
                "success": True,
                "estimated_arrival": route_info["duration_minutes"],
                "distance_km": route_info["distance_km"],
                "route": route_info.get("route_points", [])
            }
            
        except Exception as e:
            logger.error(f"Single unit dispatch failed for {unit_id}: {e}")
            return {
                "unit_id": unit_id,
                "success": False,
                "error": str(e)
            }

    async def _calculate_route(
        self, 
        origin: Location, 
        destination: Location
    ) -> Dict[str, Any]:
        """
        Calculate route between two locations using Google Maps API
        """
        try:
            if not self.maps_api_key:
                # Fallback to straight-line distance calculation
                return await self._estimate_route(origin, destination)
            
            # Use Google Maps Directions API
            async with httpx.AsyncClient() as client:
                url = "https://maps.googleapis.com/maps/api/directions/json"
                params = {
                    "origin": f"{origin.latitude},{origin.longitude}",
                    "destination": f"{destination.latitude},{destination.longitude}",
                    "mode": "driving",
                    "traffic_model": "best_guess",
                    "departure_time": "now",
                    "key": self.maps_api_key
                }
                
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if data["status"] == "OK" and data["routes"]:
                    route = data["routes"][0]
                    leg = route["legs"][0]
                    
                    return {
                        "distance_km": leg["distance"]["value"] / 1000,
                        "duration_minutes": leg["duration"]["value"] / 60,
                        "duration_in_traffic_minutes": leg.get("duration_in_traffic", {}).get("value", leg["duration"]["value"]) / 60,
                        "route_points": self._decode_polyline(route["overview_polyline"]["points"]),
                        "instructions": [step["html_instructions"] for step in leg["steps"]]
                    }
                else:
                    logger.warning(f"Maps API error: {data.get('status', 'Unknown error')}")
                    return await self._estimate_route(origin, destination)
                    
        except Exception as e:
            logger.error(f"Route calculation failed: {e}")
            return await self._estimate_route(origin, destination)

    async def _estimate_route(self, origin: Location, destination: Location) -> Dict[str, Any]:
        """
        Estimate route using straight-line distance (fallback)
        """
        distance_km = await self._calculate_distance(origin, destination)
        
        # Estimate driving time (assuming 30 km/h average in urban areas)
        duration_minutes = (distance_km / 30) * 60
        
        return {
            "distance_km": distance_km,
            "duration_minutes": duration_minutes,
            "duration_in_traffic_minutes": duration_minutes * 1.2,  # Add 20% for traffic
            "route_points": [],
            "instructions": [f"Proceed to destination ({distance_km:.1f} km)"]
        }

    async def _calculate_distance(self, loc1: Location, loc2: Location) -> float:
        """
        Calculate straight-line distance between two locations using Haversine formula
        """
        try:
            # Convert latitude and longitude from degrees to radians
            lat1, lon1, lat2, lon2 = map(
                math.radians, 
                [loc1.latitude, loc1.longitude, loc2.latitude, loc2.longitude]
            )
            
            # Haversine formula
            dlat = lat2 - lat1 
            dlon = lon2 - lon1 
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            
            # Radius of earth in kilometers
            r = 6371
            
            return c * r
            
        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            return 999.9  # Return high value on error

    def _decode_polyline(self, polyline_str: str) -> List[Dict[str, float]]:
        """
        Decode Google Maps polyline string to coordinates
        """
        try:
            index = 0
            lat = 0
            lng = 0
            coordinates = []
            
            while index < len(polyline_str):
                b = 0
                shift = 0
                result = 0
                
                while True:
                    b = ord(polyline_str[index]) - 63
                    index += 1
                    result |= (b & 0x1f) << shift
                    shift += 5
                    if b < 0x20:
                        break
                
                dlat = ~(result >> 1) if result & 1 else result >> 1
                lat += dlat
                
                shift = 0
                result = 0
                
                while True:
                    b = ord(polyline_str[index]) - 63
                    index += 1
                    result |= (b & 0x1f) << shift
                    shift += 5
                    if b < 0x20:
                        break
                
                dlng = ~(result >> 1) if result & 1 else result >> 1
                lng += dlng
                
                coordinates.append({
                    "latitude": lat / 1e5,
                    "longitude": lng / 1e5
                })
            
            return coordinates
            
        except Exception as e:
            logger.error(f"Polyline decoding failed: {e}")
            return []

    async def _send_dispatch_notification(
        self,
        unit: Dict[str, Any],
        incident: Dict[str, Any],
        route_info: Dict[str, Any],
        instructions: Optional[str]
    ):
        """
        Send dispatch notification to unit
        """
        try:
            notification_data = {
                "type": "dispatch",
                "unit_id": unit["id"],
                "incident_id": incident["id"],
                "incident_type": incident.get("type", "Unknown"),
                "incident_location": incident["location"],
                "severity": incident.get("severity", "medium"),
                "estimated_arrival": route_info["duration_minutes"],
                "distance": route_info["distance_km"],
                "instructions": instructions or "Respond to incident as assigned",
                "timestamp": self.firebase.get_server_timestamp()
            }
            
            # Store notification
            self.firebase.add_document("unit_notifications", notification_data)
            
            # In production, this would send push notification to unit's device
            logger.info(f"Dispatch notification sent to unit {unit['id']}")
            
        except Exception as e:
            logger.error(f"Failed to send dispatch notification: {e}")

    def _determine_units_needed(self, incident_type: str, priority: SeverityLevel) -> int:
        """
        Determine number of units needed based on incident type and priority
        """
        base_units = {
            "crowd_surge": 3,
            "suspicious_activity": 2,
            "fire_hazard": 4,
            "medical_emergency": 2,
            "security_breach": 3,
            "emergency_situation": 2
        }
        
        num_units = base_units.get(incident_type, 2)
        
        # Adjust based on priority
        if priority == SeverityLevel.CRITICAL:
            num_units += 2
        elif priority == SeverityLevel.HIGH:
            num_units += 1
        elif priority == SeverityLevel.LOW:
            num_units = max(1, num_units - 1)
        
        return min(num_units, 5)  # Cap at 5 units

    def _get_equipment_needs(self, incident_type: str) -> List[str]:
        """
        Get equipment needs based on incident type
        """
        equipment_needs = {
            "crowd_surge": ["barriers", "megaphone", "first_aid"],
            "suspicious_activity": ["radio", "flashlight", "camera"],
            "fire_hazard": ["fire_extinguisher", "radio", "evacuation_kit"],
            "medical_emergency": ["first_aid", "defibrillator", "stretcher"],
            "security_breach": ["radio", "flashlight", "restraints"]
        }
        
        return equipment_needs.get(incident_type, ["radio"])

    async def get_dispatch_status(self, dispatch_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current status of a dispatch
        """
        try:
            dispatch = self.firebase.get_document("dispatches", dispatch_id)
            
            if dispatch:
                # Get current unit statuses
                unit_statuses = {}
                for unit_id in dispatch.get("units_dispatched", []):
                    unit = self.firebase.get_document("security_units", unit_id)
                    if unit:
                        unit_statuses[unit_id] = {
                            "status": unit.get("status"),
                            "location": unit.get("location"),
                            "last_updated": unit.get("last_updated")
                        }
                
                dispatch["unit_statuses"] = unit_statuses
                return dispatch
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get dispatch status: {e}")
            return None

    async def cancel_dispatch(self, dispatch_id: str, reason: str = "Manual cancellation") -> bool:
        """
        Cancel an active dispatch
        """
        try:
            dispatch = self.firebase.get_document("dispatches", dispatch_id)
            
            if not dispatch:
                logger.warning(f"Dispatch {dispatch_id} not found for cancellation")
                return False
            
            if dispatch.get("status") not in ["dispatched", "en_route"]:
                logger.warning(f"Cannot cancel dispatch {dispatch_id} with status {dispatch.get('status')}")
                return False
            
            # Update dispatch status
            self.firebase.update_document("dispatches", dispatch_id, {
                "status": "cancelled",
                "cancellation_reason": reason,
                "cancelled_timestamp": self.firebase.get_server_timestamp()
            })
            
            # Return units to available status
            for unit_id in dispatch.get("units_dispatched", []):
                unit_update = {
                    "status": UnitStatus.AVAILABLE.value,
                    "current_assignment": None,
                    "dispatch_id": None,
                    "last_updated": self.firebase.get_server_timestamp()
                }
                self.firebase.update_document("security_units", unit_id, unit_update)
                
                # Send cancellation notification
                await self._send_cancellation_notification(unit_id, dispatch_id, reason)
            
            logger.info(f"Dispatch {dispatch_id} cancelled successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cancel dispatch {dispatch_id}: {e}")
            return False

    async def _send_cancellation_notification(self, unit_id: str, dispatch_id: str, reason: str):
        """Send cancellation notification to unit"""
        try:
            notification_data = {
                "type": "dispatch_cancelled",
                "unit_id": unit_id,
                "dispatch_id": dispatch_id,
                "reason": reason,
                "message": f"Dispatch {dispatch_id} has been cancelled: {reason}",
                "timestamp": self.firebase.get_server_timestamp()
            }
            
            self.firebase.add_document("unit_notifications", notification_data)
            logger.info(f"Cancellation notification sent to unit {unit_id}")
            
        except Exception as e:
            logger.error(f"Failed to send cancellation notification: {e}")

    async def update_unit_location(self, unit_id: str, new_location: Location) -> bool:
        """Update unit location (called by unit GPS tracking)"""
        try:
            unit_update = {
                "location": new_location.dict(),
                "last_updated": self.firebase.get_server_timestamp()
            }
            
            self.firebase.update_document("security_units", unit_id, unit_update)
            
            # If unit is dispatched, check if arrived at destination
            unit = self.firebase.get_document("security_units", unit_id)
            if unit and unit.get("status") == UnitStatus.DISPATCHED.value:
                await self._check_unit_arrival(unit_id, unit, new_location)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update unit location: {e}")
            return False

    async def _check_unit_arrival(self, unit_id: str, unit: Dict[str, Any], current_location: Location):
        """Check if dispatched unit has arrived at incident location"""
        try:
            assignment_id = unit.get("current_assignment")
            if not assignment_id:
                return
            
            # Get incident location
            incident = self.firebase.get_document("incidents", assignment_id)
            if not incident:
                return
            
            incident_location = Location(**incident["location"])
            distance = await self._calculate_distance(current_location, incident_location)
            
            # Consider arrived if within 100 meters
            if distance < 0.1:  # 100 meters = 0.1 km
                await self._mark_unit_arrived(unit_id, assignment_id)
                
        except Exception as e:
            logger.error(f"Arrival check failed for unit {unit_id}: {e}")

    async def _mark_unit_arrived(self, unit_id: str, incident_id: str):
        """Mark unit as arrived at incident"""
        try:
            # Update unit status
            unit_update = {
                "status": "on_scene",
                "arrival_timestamp": self.firebase.get_server_timestamp(),
                "last_updated": self.firebase.get_server_timestamp()
            }
            self.firebase.update_document("security_units", unit_id, unit_update)
            
            # Update incident with arrival
            incident_update = {
                "units_on_scene": self.firebase.firestore.ArrayUnion([unit_id]),
                "last_updated": self.firebase.get_server_timestamp()
            }
            self.firebase.update_document("incidents", incident_id, incident_update)
            
            # Log arrival
            arrival_log = {
                "unit_id": unit_id,
                "incident_id": incident_id,
                "event_type": "unit_arrived",
                "timestamp": self.firebase.get_server_timestamp()
            }
            self.firebase.add_document("dispatch_logs", arrival_log)
            
            logger.info(f"Unit {unit_id} marked as arrived at incident {incident_id}")
            
        except Exception as e:
            logger.error(f"Failed to mark unit arrival: {e}")

    async def get_available_units(self, location: Optional[Location] = None, max_distance_km: float = None) -> List[Dict[str, Any]]:
        """Get available units, optionally filtered by location"""
        try:
            available_units = self.firebase.get_collection_with_filters(
                "security_units",
                filters={"status": UnitStatus.AVAILABLE.value}
            )
            
            if location and max_distance_km:
                # Filter by distance
                filtered_units = []
                for unit in available_units:
                    unit_location = Location(**unit["location"])
                    distance = await self._calculate_distance(location, unit_location)
                    
                    if distance <= max_distance_km:
                        unit["distance_km"] = distance
                        filtered_units.append(unit)
                
                # Sort by distance
                filtered_units.sort(key=lambda x: x["distance_km"])
                return filtered_units
            
            return available_units
            
        except Exception as e:
            logger.error(f"Failed to get available units: {e}")
            return []

    async def get_dispatch_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get dispatch performance analytics"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Get recent dispatches
            recent_dispatches = self.firebase.get_collection_with_filters(
                "dispatches",
                filters={"timestamp": (">=", cutoff_date)},
                limit=1000
            )
            
            if not recent_dispatches:
                return {"error": "No dispatch data available"}
            
            # Calculate metrics
            total_dispatches = len(recent_dispatches)
            successful_dispatches = len([d for d in recent_dispatches if d.get("status") == "dispatched"])
            cancelled_dispatches = len([d for d in recent_dispatches if d.get("status") == "cancelled"])
            
            # Average response times
            response_times = []
            for dispatch in recent_dispatches:
                if dispatch.get("estimated_arrival_times"):
                    times = list(dispatch["estimated_arrival_times"].values())
                    if times:
                        response_times.append(min(times))
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Units utilization
            all_units = self.firebase.get_collection("security_units")
            total_units = len(all_units)
            busy_units = len([u for u in all_units if u.get("status") != UnitStatus.AVAILABLE.value])
            
            utilization_rate = (busy_units / total_units * 100) if total_units > 0 else 0
            
            return {
                "period_days": days,
                "total_dispatches": total_dispatches,
                "successful_dispatches": successful_dispatches,
                "cancelled_dispatches": cancelled_dispatches,
                "success_rate": (successful_dispatches / total_dispatches * 100) if total_dispatches > 0 else 0,
                "average_response_time_minutes": round(avg_response_time, 2),
                "current_utilization_rate": round(utilization_rate, 2),
                "total_units": total_units,
                "available_units": total_units - busy_units,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get dispatch analytics: {e}")
            return {"error": str(e)}

    def get_service_status(self) -> Dict[str, Any]:
        """Get dispatch service status"""
        return {
            "service": "dispatch",
            "status": "operational",
            "maps_api_enabled": bool(self.maps_api_key),
            "max_dispatch_distance_km": self.max_dispatch_distance_km,
            "priority_response_times": {k.value: v for k, v in self.priority_response_times.items()},
            "supported_unit_types": list(self.unit_capabilities.keys())
        }