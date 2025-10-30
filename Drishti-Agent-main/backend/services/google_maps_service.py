
# ===== 1. INSTALL REQUIRED PACKAGES =====
# Add these to your requirements.txt or install via pip:
# pip install googlemaps geopy

# ===== 2. GOOGLE MAPS SERVICE =====
# Create: services/google_maps_service.py

import googlemaps
import logging
from typing import Dict, Optional, Tuple, List
from geopy.distance import geodesic
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class GoogleMapsService:
    """Google Maps integration service for location data"""
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        
        # For hackathon: make API key optional and use offline mode if not available
        if self.api_key:
            try:
                self.gmaps = googlemaps.Client(key=self.api_key)
                self.online_mode = True
                logger.info("✅ Google Maps service initialized in ONLINE mode")
            except Exception as e:
                logger.warning(f"Google Maps API failed, falling back to offline mode: {e}")
                self.gmaps = None
                self.online_mode = False
        else:
            logger.warning("GOOGLE_MAPS_API_KEY not found - using OFFLINE mode with predefined locations")
            self.gmaps = None
            self.online_mode = False
        
        # Define your venue/campus boundaries and key locations
        self.venue_config = {
            "center": {
                "lat": 34.0522,  # Replace with your venue center
                "lng": -118.2437,
                "name": "Main Campus Center"
            },
            "radius_km": 2.0,  # Venue radius in kilometers
            "zones": {
                "main_entrance": {"lat": 34.0525, "lng": -118.2440, "name": "Main Entrance Gate"},
                "plaza": {"lat": 34.0520, "lng": -118.2435, "name": "Central Plaza"},
                "parking_area": {"lat": 34.0518, "lng": -118.2445, "name": "Main Parking Area"},
                "exit_gate": {"lat": 34.0515, "lng": -118.2430, "name": "Exit Gate B"},
                "food_court": {"lat": 34.0522, "lng": -118.2432, "name": "Food Court Area"},
                "auditorium": {"lat": 34.0526, "lng": -118.2438, "name": "Main Auditorium"},
                "emergency_exit": {"lat": 34.0512, "lng": -118.2441, "name": "Emergency Exit C"}
            }
        }
    
    def get_location_by_zone(self, zone_name: str) -> Optional[Dict]:
        """Get predefined zone location"""
        try:
            zone_data = self.venue_config["zones"].get(zone_name.lower())
            if not zone_data:
                logger.warning(f"Zone '{zone_name}' not found in venue config")
                return None
            
            return {
                "latitude": zone_data["lat"],
                "longitude": zone_data["lng"],
                "name": zone_data["name"],
                "zone_id": zone_name,
                "address": self.reverse_geocode(zone_data["lat"], zone_data["lng"])
            }
        except Exception as e:
            logger.error(f"Error getting zone location: {e}")
            return None
    
    def geocode_address(self, address: str) -> Optional[Dict]:
        """Convert address to coordinates"""
        try:
            if not self.online_mode or not self.gmaps:
                # Offline mode: check if address matches any predefined zones
                address_lower = address.lower()
                for zone_name, zone_data in self.venue_config["zones"].items():
                    if zone_name.replace("_", " ") in address_lower or zone_data["name"].lower() in address_lower:
                        return {
                            "latitude": zone_data["lat"],
                            "longitude": zone_data["lng"],
                            "name": zone_data["name"],
                            "address": f"{zone_data['name']} (Offline Mode)",
                            "zone_id": zone_name
                        }
                # Default fallback
                return {
                    "latitude": self.venue_config["center"]["lat"],
                    "longitude": self.venue_config["center"]["lng"],
                    "name": f"Geocoded: {address}",
                    "address": f"{address} (Offline Mode)"
                }
            
            geocode_result = self.gmaps.geocode(address)
            if not geocode_result:
                return None
            
            location = geocode_result[0]['geometry']['location']
            formatted_address = geocode_result[0]['formatted_address']
            
            return {
                "latitude": location['lat'],
                "longitude": location['lng'],
                "name": formatted_address,
                "address": formatted_address,
                "place_id": geocode_result[0].get('place_id')
            }
        except Exception as e:
            logger.error(f"Geocoding failed for '{address}': {e}")
            return None
    
    def reverse_geocode(self, lat: float, lng: float) -> str:
        """Convert coordinates to address"""
        try:
            if not self.online_mode or not self.gmaps:
                # Offline mode: find nearest zone
                nearest_zone = self.get_nearest_zone(lat, lng)
                if nearest_zone:
                    return f"{nearest_zone['name']} (Offline Mode)"
                return f"Location: {lat:.4f}, {lng:.4f} (Offline Mode)"
            
            reverse_geocode_result = self.gmaps.reverse_geocode((lat, lng))
            if reverse_geocode_result:
                return reverse_geocode_result[0]['formatted_address']
            return f"Coordinates: {lat:.4f}, {lng:.4f}"
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
            return f"Location: {lat:.4f}, {lng:.4f}"
    
    def validate_location_within_venue(self, lat: float, lng: float) -> bool:
        """Check if coordinates are within venue boundaries"""
        try:
            center = (self.venue_config["center"]["lat"], self.venue_config["center"]["lng"])
            point = (lat, lng)
            distance_km = geodesic(center, point).kilometers
            
            return distance_km <= self.venue_config["radius_km"]
        except Exception as e:
            logger.error(f"Location validation failed: {e}")
            return False
    
    def get_nearest_zone(self, lat: float, lng: float) -> Optional[Dict]:
        """Find the nearest predefined zone to given coordinates"""
        try:
            target_point = (lat, lng)
            nearest_zone = None
            min_distance = float('inf')
            
            for zone_id, zone_data in self.venue_config["zones"].items():
                zone_point = (zone_data["lat"], zone_data["lng"])
                distance = geodesic(target_point, zone_point).meters
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_zone = {
                        "zone_id": zone_id,
                        "name": zone_data["name"],
                        "latitude": zone_data["lat"],
                        "longitude": zone_data["lng"],
                        "distance_meters": distance
                    }
            
            return nearest_zone
        except Exception as e:
            logger.error(f"Error finding nearest zone: {e}")
            return None
    
    def get_all_zones(self) -> List[Dict]:
        """Get all predefined venue zones"""
        zones = []
        for zone_id, zone_data in self.venue_config["zones"].items():
            zones.append({
                "zone_id": zone_id,
                "name": zone_data["name"],
                "latitude": zone_data["lat"],
                "longitude": zone_data["lng"],
                "address": self.reverse_geocode(zone_data["lat"], zone_data["lng"])
            })
        return zones
    
    def calculate_distance_between_zones(self, zone1: str, zone2: str) -> Optional[float]:
        """Calculate distance between two zones in meters"""
        try:
            zone1_data = self.venue_config["zones"].get(zone1.lower())
            zone2_data = self.venue_config["zones"].get(zone2.lower())
            
            if not zone1_data or not zone2_data:
                return None
            
            point1 = (zone1_data["lat"], zone1_data["lng"])
            point2 = (zone2_data["lat"], zone2_data["lng"])
            
            return geodesic(point1, point2).meters
        except Exception as e:
            logger.error(f"Distance calculation failed: {e}")
            return None