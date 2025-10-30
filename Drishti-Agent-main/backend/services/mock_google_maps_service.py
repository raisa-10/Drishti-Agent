"""
Mock Google Maps Service for Development
Provides fallback functionality when Google Maps API is not available
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

class MockGoogleMapsService:
    """Mock implementation of Google Maps Service for development"""
    
    def __init__(self):
        """Initialize mock service with predefined zones"""
        logger.info("Using Mock Google Maps Service")
        
        # Predefined venue zones for testing
        self.predefined_zones = {
            "main_entrance": {
                "zone_id": "zone_001",
                "name": "Main Entrance",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "address": "123 Main St, Los Angeles, CA",
                "type": "entrance",
                "capacity": 500
            },
            "central_plaza": {
                "zone_id": "zone_002", 
                "name": "Central Plaza",
                "latitude": 34.0525,
                "longitude": -118.2440,
                "address": "Central Plaza, Los Angeles, CA",
                "type": "gathering_area",
                "capacity": 1000
            },
            "parking_lot": {
                "zone_id": "zone_003",
                "name": "Parking Lot A",
                "latitude": 34.0520,
                "longitude": -118.2445,
                "address": "Parking Lot A, Los Angeles, CA", 
                "type": "parking",
                "capacity": 200
            },
            "emergency_exit": {
                "zone_id": "zone_004",
                "name": "Emergency Exit B",
                "latitude": 34.0518,
                "longitude": -118.2435,
                "address": "Emergency Exit B, Los Angeles, CA",
                "type": "exit",
                "capacity": 300
            }
        }
        
        # Venue boundary (rough rectangle around venue)
        self.venue_bounds = {
            "north": 34.0530,
            "south": 34.0515,
            "east": -118.2430,
            "west": -118.2450
        }
    
    def get_location_by_zone(self, zone_name: str) -> Optional[Dict]:
        """Get location data for a predefined zone"""
        try:
            zone_key = zone_name.lower().replace(" ", "_")
            return self.predefined_zones.get(zone_key)
        except Exception as e:
            logger.error(f"Failed to get zone location: {e}")
            return None
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """Mock geocoding - returns approximate LA coordinates"""
        try:
            # Check if address matches any predefined zones
            address_lower = address.lower()
            for zone_key, zone_data in self.predefined_zones.items():
                if zone_key in address_lower or zone_data["name"].lower() in address_lower:
                    return zone_data
            
            # Default fallback location (Downtown LA)
            return {
                "latitude": 34.0522,
                "longitude": -118.2437,
                "name": f"Geocoded: {address}",
                "address": address,
                "zone_id": "geocoded_location"
            }
        except Exception as e:
            logger.error(f"Geocoding failed: {e}")
            return None
    
    def reverse_geocode(self, latitude: float, longitude: float) -> str:
        """Convert coordinates back to address"""
        try:
            # Check if coordinates match any predefined zones
            for zone_data in self.predefined_zones.values():
                # Simple distance check (within ~0.001 degrees)
                if (abs(zone_data["latitude"] - latitude) < 0.001 and 
                    abs(zone_data["longitude"] - longitude) < 0.001):
                    return zone_data["address"]
            
            # Default address format
            return f"Coordinates: {latitude:.4f}, {longitude:.4f}"
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
            return "Address not found"
    
    def get_all_zones(self) -> List[Dict]:
        """Get all predefined venue zones"""
        try:
            return list(self.predefined_zones.values())
        except Exception as e:
            logger.error(f"Failed to get all zones: {e}")
            return []
    
    def validate_location_within_venue(self, latitude: float, longitude: float) -> bool:
        """Check if coordinates are within venue boundaries"""
        try:
            return (
                self.venue_bounds["south"] <= latitude <= self.venue_bounds["north"] and
                self.venue_bounds["west"] <= longitude <= self.venue_bounds["east"]
            )
        except Exception as e:
            logger.error(f"Location validation failed: {e}")
            return False
    
    def get_nearest_zone(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Find the nearest predefined zone to given coordinates"""
        try:
            min_distance = float('inf')
            nearest_zone = None
            
            for zone_data in self.predefined_zones.values():
                # Simple Euclidean distance calculation
                distance = (
                    (zone_data["latitude"] - latitude) ** 2 +
                    (zone_data["longitude"] - longitude) ** 2
                ) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_zone = zone_data
            
            return nearest_zone
        except Exception as e:
            logger.error(f"Failed to find nearest zone: {e}")
            return None
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points (simple Euclidean)"""
        try:
            return ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5
        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            return 0.0
    
    def get_route_info(self, origin: Tuple[float, float], destination: Tuple[float, float]) -> Dict:
        """Mock route calculation"""
        try:
            distance = self.calculate_distance(origin[0], origin[1], destination[0], destination[1])
            
            return {
                "distance_km": round(distance * 111, 2),  # Rough conversion to km
                "duration_minutes": round(distance * 111 * 2, 0),  # Rough walking time
                "route_found": True,
                "mode": "walking"
            }
        except Exception as e:
            logger.error(f"Route calculation failed: {e}")
            return {
                "distance_km": 0,
                "duration_minutes": 0,
                "route_found": False,
                "error": str(e)
            }
