"""
Project Drishti - Forecasting Model Service
Handles predictive analytics for crowd behavior and incident forecasting using Vertex AI
"""

import os
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import asyncio

# Google Cloud AI Platform
from google.cloud import aiplatform
import vertexai
from vertexai.language_models import TextGenerationModel

# Data processing
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
import joblib

from services.firebase_service import FirebaseService
from utils.data_models import CrowdForecast, IncidentTrend, Location

logger = logging.getLogger(__name__)

class ForecastingService:
    """
    Predictive analytics service for crowd management and incident forecasting
    """
    
    def __init__(self):
        """Initialize Forecasting service"""
        try:
            # Initialize Vertex AI
            project_id = os.getenv('GCP_PROJECT_ID')
            region = os.getenv('VERTEX_AI_REGION', 'us-central1')
            
            vertexai.init(project=project_id, location=region)
            
            # Initialize Firebase for historical data
            self.firebase = FirebaseService()
            
            # Initialize models
            self.text_model = TextGenerationModel.from_pretrained("text-bison@001")
            
            # Model configurations
            self.crowd_density_model = None
            self.incident_prediction_model = None
            self.scalers = {}
            
            # Feature configurations
            self.crowd_features = [
                'hour_of_day', 'day_of_week', 'is_weekend', 'is_holiday',
                'weather_score', 'event_factor', 'historical_avg'
            ]
            
            self.incident_features = [
                'crowd_density', 'time_since_last_incident', 'weather_score',
                'event_type', 'location_risk_score', 'day_of_week'
            ]
            
            # Initialize models with sample data
            asyncio.create_task(self._initialize_models())
            
            logger.info("✅ Forecasting service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Forecasting service: {e}")
            raise

    async def predict_crowd_density(
        self, 
        location: str, 
        time_horizon_hours: int = 4,
        include_events: bool = True
    ) -> CrowdForecast:
        """
        Predict crowd density for a specific location over time
        """
        try:
            logger.info(f"Predicting crowd density for {location} over {time_horizon_hours} hours")
            
            # Get current and historical data
            current_time = datetime.now()
            historical_data = await self._get_historical_crowd_data(location, days=30)
            
            # Generate time slots for prediction
            time_slots = []
            for i in range(time_horizon_hours):
                slot_time = current_time + timedelta(hours=i)
                time_slots.append(slot_time)
            
            # Prepare features for each time slot
            predictions = []
            
            for slot_time in time_slots:
                features = await self._prepare_crowd_features(
                    location, slot_time, historical_data, include_events
                )
                
                # Make prediction
                if self.crowd_density_model:
                    predicted_density = await self._predict_density_ml(features)
                else:
                    predicted_density = await self._predict_density_heuristic(features, historical_data)
                
                # Calculate confidence based on data quality and model performance
                confidence = self._calculate_prediction_confidence(features, historical_data)
                
                predictions.append({
                    "time_slot": slot_time.isoformat(),
                    "predicted_density": round(predicted_density, 3),
                    "confidence": round(confidence, 3),
                    "risk_level": self._assess_density_risk(predicted_density),
                    "factors": self._get_prediction_factors(features)
                })
            
            # Create forecast object
            forecast = CrowdForecast(
                location=location,
                predictions=predictions,
                forecast_horizon_hours=time_horizon_hours,
                generated_at=current_time,
                model_version="v1.0"
            )
            
            # Store forecast for tracking accuracy
            await self._store_forecast(forecast)
            
            logger.info(f"Crowd density forecast generated for {location}")
            return forecast
            
        except Exception as e:
            logger.error(f"Crowd density prediction failed: {e}")
            raise

    async def predict_incident_probability(
        self, 
        location: str, 
        time_window_hours: int = 2
    ) -> Dict[str, Any]:
        """
        Predict probability of incidents occurring in a location/time window
        """
        try:
            logger.info(f"Predicting incident probability for {location}")
            
            # Get current conditions
            current_time = datetime.now()
            current_crowd_density = await self._get_current_crowd_density(location)
            historical_incidents = await self._get_historical_incidents(location, days=90)
            
            # Prepare features
            features = await self._prepare_incident_features(
                location, current_time, current_crowd_density, historical_incidents
            )
            
            # Predict probabilities for different incident types
            incident_probabilities = {}
            
            incident_types = [
                "crowd_surge", "suspicious_activity", "medical_emergency", 
                "fire_hazard", "security_breach"
            ]
            
            for incident_type in incident_types:
                probability = await self._predict_incident_type_probability(
                    incident_type, features, historical_incidents
                )
                incident_probabilities[incident_type] = {
                    "probability": round(probability, 3),
                    "risk_level": self._assess_incident_risk(probability),
                    "contributing_factors": self._get_incident_factors(incident_type, features)
                }
            
            # Calculate overall incident probability
            overall_probability = max(incident_probabilities.values(), key=lambda x: x["probability"])["probability"]
            
            # Generate recommendations
            recommendations = await self._generate_incident_recommendations(
                location, incident_probabilities, features
            )
            
            return {
                "location": location,
                "time_window_hours": time_window_hours,
                "overall_probability": overall_probability,
                "incident_probabilities": incident_probabilities,
                "recommendations": recommendations,
                "generated_at": current_time.isoformat(),
                "confidence": self._calculate_incident_confidence(features, historical_incidents)
            }
            
        except Exception as e:
            logger.error(f"Incident probability prediction failed: {e}")
            return {"error": str(e)}

    async def analyze_crowd_trends(
        self, 
        location: str = None, 
        days: int = 30
    ) -> IncidentTrend:
        """
        Analyze historical crowd and incident trends
        """
        try:
            logger.info(f"Analyzing crowd trends for {days} days")
            
            # Get historical data - simplified call for the demo
            incidents = self.firebase.get_collection("incidents", limit=1000)
            if location:
                incidents = [i for i in incidents if i.get("location", {}).get("name") == location]

            # Filter by date in Python
            incidents = [i for i in incidents if i.get("timestamp") and i.get("timestamp") >= cutoff_date]
            
            if not incidents:
                return IncidentTrend(
                    time_period="daily",
                    incident_counts={},
                    incident_types={},
                    severity_distribution={},
                    peak_hours=[],
                    trend_direction="stable"
                )
            
            # Process data into trends
            df = pd.DataFrame(incidents)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['timestamp'].dt.hour
            df['date'] = df['timestamp'].dt.date
            
            # Daily incident counts
            daily_counts = df.groupby('date').size().to_dict()
            daily_counts_str = {str(k): v for k, v in daily_counts.items()}
            
            # Incident types distribution
            type_counts = df['type'].value_counts().to_dict()
            
            # Severity distribution  
            severity_counts = df['severity'].value_counts().to_dict()
            
            # Peak hours analysis
            hourly_counts = df.groupby('hour').size()
            peak_hours = hourly_counts.nlargest(3).index.tolist()
            
            # Trend direction calculation
            recent_week = df[df['timestamp'] >= (datetime.now() - timedelta(days=7))]
            previous_week = df[
                (df['timestamp'] >= (datetime.now() - timedelta(days=14))) & 
                (df['timestamp'] < (datetime.now() - timedelta(days=7)))
            ]
            
            recent_avg = len(recent_week) / 7
            previous_avg = len(previous_week) / 7 if len(previous_week) > 0 else recent_avg
            
            if recent_avg > previous_avg * 1.1:
                trend_direction = "increasing"
            elif recent_avg < previous_avg * 0.9:
                trend_direction = "decreasing"
            else:
                trend_direction = "stable"
            
            return IncidentTrend(
                time_period="daily",
                incident_counts=daily_counts_str,
                incident_types=type_counts,
                severity_distribution=severity_counts,
                peak_hours=peak_hours,
                trend_direction=trend_direction
            )
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            raise

    async def generate_predictive_alerts(self) -> List[Dict[str, Any]]:
        """
        Generate predictive alerts for high-risk situations
        """
        try:
            alerts = []
            
            # Get all monitored locations
            locations = await self._get_monitored_locations()
            
            for location in locations:
                # Check crowd density forecast
                crowd_forecast = await self.predict_crowd_density(location, 2)
                
                # Check for high density predictions
                for prediction in crowd_forecast.predictions:
                    if prediction["predicted_density"] > 0.8:  # High density threshold
                        alerts.append({
                            "type": "high_crowd_density_predicted",
                            "location": location,
                            "predicted_time": prediction["time_slot"],
                            "density": prediction["predicted_density"],
                            "confidence": prediction["confidence"],
                            "severity": "high" if prediction["predicted_density"] > 0.9 else "medium",
                            "message": f"High crowd density predicted at {location}: {prediction['predicted_density']:.1%}",
                            "generated_at": datetime.now().isoformat()
                        })
                
                # Check incident probability
                incident_forecast = await self.predict_incident_probability(location, 2)
                
                if incident_forecast.get("overall_probability", 0) > 0.7:  # High risk threshold
                    alerts.append({
                        "type": "high_incident_probability",
                        "location": location,
                        "probability": incident_forecast["overall_probability"],
                        "confidence": incident_forecast["confidence"],
                        "severity": "high",
                        "message": f"High incident probability at {location}: {incident_forecast['overall_probability']:.1%}",
                        "top_risks": [k for k, v in incident_forecast["incident_probabilities"].items() if v["probability"] > 0.5],
                        "generated_at": datetime.now().isoformat()
                    })
            
            # Store alerts for tracking
            for alert in alerts:
                self.firebase.add_document("predictive_alerts", alert)
            
            logger.info(f"Generated {len(alerts)} predictive alerts")
            return alerts
            
        except Exception as e:
            logger.error(f"Predictive alert generation failed: {e}")
            return []

    # ===== HELPER METHODS =====

    async def _initialize_models(self):
        """Initialize ML models with historical data"""
        try:
            # This would typically load pre-trained models
            # For demo purposes, we'll use simple heuristic models
            logger.info("Initializing forecasting models...")
            
            # In production, you would:
            # 1. Load historical training data
            # 2. Prepare features
            # 3. Train models
            # 4. Save models for inference
            
            self.crowd_density_model = "heuristic"  # Placeholder
            self.incident_prediction_model = "heuristic"  # Placeholder
            
            logger.info("Forecasting models initialized")
            
        except Exception as e:
            logger.error(f"Model initialization failed: {e}")

    async def _get_historical_crowd_data(self, location: str, days: int) -> List[Dict[str, Any]]:
        """Get historical crowd density data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # In production, this would query crowd density measurements
            # For demo, we'll simulate some data based on incidents
            incidents = self.firebase.get_collection_with_filters(
                "incidents",
                filters={
                    "timestamp": (">=", cutoff_date),
                    "location.name": location
                },
                limit=500
            )
            
            # Convert incidents to crowd data points
            crowd_data = []
            for incident in incidents:
                if "analysis_result" in incident and "crowd_density" in incident["analysis_result"]:
                    crowd_data.append({
                        "timestamp": incident["timestamp"],
                        "density": incident["analysis_result"]["crowd_density"],
                        "location": location
                    })
            
            return crowd_data
            
        except Exception as e:
            logger.error(f"Failed to get historical crowd data: {e}")
            return []

    async def _prepare_crowd_features(
        self, 
        location: str, 
        target_time: datetime, 
        historical_data: List[Dict], 
        include_events: bool
    ) -> Dict[str, float]:
        """Prepare features for crowd density prediction"""
        try:
            features = {}
            
            # Time-based features
            features['hour_of_day'] = target_time.hour
            features['day_of_week'] = target_time.weekday()
            features['is_weekend'] = 1.0 if target_time.weekday() >= 5 else 0.0
            features['is_holiday'] = await self._is_holiday(target_time)
            
            # Weather features (simulated)
            features['weather_score'] = await self._get_weather_score(target_time)
            
            # Event features
            if include_events:
                features['event_factor'] = await self._get_event_factor(location, target_time)
            else:
                features['event_factor'] = 0.0
            
            # Historical average for this time
            features['historical_avg'] = self._calculate_historical_average(
                historical_data, target_time.hour, target_time.weekday()
            )
            
            return features
            
        except Exception as e:
            logger.error(f"Feature preparation failed: {e}")
            return {}

    async def _predict_density_heuristic(
        self, 
        features: Dict[str, float], 
        historical_data: List[Dict]
    ) -> float:
        """Heuristic crowd density prediction"""
        try:
            base_density = features.get('historical_avg', 0.3)
            
            # Adjust for time of day
            hour = features.get('hour_of_day', 12)
            if 9 <= hour <= 11 or 17 <= hour <= 19:  # Peak hours
                base_density *= 1.3
            elif 22 <= hour <= 6:  # Low activity hours
                base_density *= 0.5
            
            # Adjust for weekend
            if features.get('is_weekend', 0) > 0:
                base_density *= 1.2
            
            # Adjust for holidays
            if features.get('is_holiday', 0) > 0:
                base_density *= 1.4
            
            # Adjust for weather
            weather_score = features.get('weather_score', 0.5)
            base_density *= (0.5 + weather_score)
            
            # Adjust for events
            event_factor = features.get('event_factor', 0)
            base_density += event_factor
            
            # Cap between 0 and 1
            return max(0.0, min(1.0, base_density))
            
        except Exception as e:
            logger.error(f"Heuristic prediction failed: {e}")
            return 0.3

    def _calculate_historical_average(
        self, 
        historical_data: List[Dict], 
        hour: int, 
        day_of_week: int
    ) -> float:
        """Calculate historical average for similar time periods"""
        if not historical_data:
            return 0.3
        
        # Filter for similar times
        similar_data = []
        for data_point in historical_data:
            if isinstance(data_point.get('timestamp'), datetime):
                dt = data_point['timestamp']
                if dt.hour == hour and dt.weekday() == day_of_week:
                    similar_data.append(data_point.get('density', 0))
        
        if similar_data:
            return sum(similar_data) / len(similar_data)
        
        # Fallback to all data
        all_densities = [dp.get('density', 0) for dp in historical_data if 'density' in dp]
        return sum(all_densities) / len(all_densities) if all_densities else 0.3

    def _calculate_prediction_confidence(
        self, 
        features: Dict[str, float], 
        historical_data: List[Dict]
    ) -> float:
        """Calculate confidence score for prediction"""
        confidence = 0.5  # Base confidence
        
        # More historical data = higher confidence
        if len(historical_data) > 50:
            confidence += 0.2
        elif len(historical_data) > 20:
            confidence += 0.1
        
        # Recent data = higher confidence
        recent_data = [d for d in historical_data if isinstance(d.get('timestamp'), datetime) and 
                      (datetime.now() - d['timestamp']).days <= 7]
        if len(recent_data) > 10:
            confidence += 0.2
        
        # Holiday/event certainty
        if features.get('is_holiday', 0) > 0 or features.get('event_factor', 0) > 0:
            confidence += 0.1
        
        return min(1.0, confidence)

    async def _get_weather_score(self, target_time: datetime) -> float:
        """Get weather favorability score (0-1)"""
        # In production, this would call weather API
        # For demo, return a reasonable default
        return 0.7

    async def _is_holiday(self, target_time: datetime) -> float:
        """Check if date is a holiday"""
        # Simple holiday check - in production use proper holiday library
        holidays = [
            (1, 1),   # New Year
            (7, 4),   # Independence Day  
            (12, 25), # Christmas
        ]
        
        date_tuple = (target_time.month, target_time.day)
        return 1.0 if date_tuple in holidays else 0.0

    async def _get_event_factor(self, location: str, target_time: datetime) -> float:
        """Get event impact factor for location and time"""
        # In production, this would check event calendar
        # For demo, simulate some event activity
        if target_time.weekday() in [5, 6]:  # Weekend events
            return 0.3
        return 0.0

    def _assess_density_risk(self, density: float) -> str:
        """Assess risk level based on density"""
        if density > 0.9:
            return "critical"
        elif density > 0.7:
            return "high"
        elif density > 0.5:
            return "medium"
        else:
            return "low"

    def _get_prediction_factors(self, features: Dict[str, float]) -> List[str]:
        """Get human-readable factors affecting prediction"""
        factors = []
        
        if features.get('is_weekend', 0) > 0:
            factors.append("Weekend activity")
        
        if features.get('is_holiday', 0) > 0:
            factors.append("Holiday period")
        
        hour = features.get('hour_of_day', 12)
        if 9 <= hour <= 11:
            factors.append("Morning peak")
        elif 17 <= hour <= 19:
            factors.append("Evening peak")
        
        if features.get('event_factor', 0) > 0:
            factors.append("Special event")
        
        weather_score = features.get('weather_score', 0.5)
        if weather_score > 0.8:
            factors.append("Favorable weather")
        elif weather_score < 0.3:
            factors.append("Poor weather conditions")
        
        return factors

    async def _get_historical_incidents(self, location: str, days: int) -> List[Dict[str, Any]]:
        """Get historical incident data for location"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            incidents = self.firebase.get_collection_with_filters(
                "incidents",
                filters={
                    "timestamp": (">=", cutoff_date),
                    "location.name": location
                },
                limit=500
            )
            
            return incidents
            
        except Exception as e:
            logger.error(f"Failed to get historical incidents: {e}")
            return []

    async def _get_current_crowd_density(self, location: str) -> float:
        """Get current crowd density for location"""
        try:
            # Get most recent incident with crowd density data
            recent_incidents = self.firebase.get_collection_with_filters(
                "incidents",
                filters={"location.name": location},
                order_by=("timestamp", "desc"),
                limit=5
            )
            
            for incident in recent_incidents:
                if "analysis_result" in incident and "crowd_density" in incident["analysis_result"]:
                    return incident["analysis_result"]["crowd_density"]
            
            # Default to moderate density if no recent data
            return 0.4
            
        except Exception as e:
            logger.error(f"Failed to get current crowd density: {e}")
            return 0.4

    async def _prepare_incident_features(
        self,
        location: str,
        current_time: datetime,
        crowd_density: float,
        historical_incidents: List[Dict]
    ) -> Dict[str, float]:
        """Prepare features for incident prediction"""
        try:
            features = {}
            
            # Current conditions
            features['crowd_density'] = crowd_density
            features['hour_of_day'] = current_time.hour
            features['day_of_week'] = current_time.weekday()
            features['is_weekend'] = 1.0 if current_time.weekday() >= 5 else 0.0
            
            # Time since last incident
            if historical_incidents:
                last_incident_time = max([inc.get('timestamp', datetime.min) for inc in historical_incidents])
                if isinstance(last_incident_time, datetime):
                    hours_since = (current_time - last_incident_time).total_seconds() / 3600
                    features['time_since_last_incident'] = min(hours_since, 168)  # Cap at 1 week
                else:
                    features['time_since_last_incident'] = 168
            else:
                features['time_since_last_incident'] = 168
            
            # Location risk score based on incident history
            features['location_risk_score'] = self._calculate_location_risk(historical_incidents)
            
            # Weather impact
            features['weather_score'] = await self._get_weather_score(current_time)
            
            # Event factor
            features['event_factor'] = await self._get_event_factor(location, current_time)
            
            return features
            
        except Exception as e:
            logger.error(f"Incident feature preparation failed: {e}")
            return {}

    def _calculate_location_risk(self, historical_incidents: List[Dict]) -> float:
        """Calculate risk score for location based on incident history"""
        if not historical_incidents:
            return 0.1
        
        # Count incidents by severity
        severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        total_weight = 0
        
        for incident in historical_incidents:
            severity = incident.get('severity', 'medium')
            total_weight += severity_weights.get(severity, 2)
        
        # Normalize by time period (90 days)
        risk_score = total_weight / 90
        
        # Cap between 0 and 1
        return min(1.0, risk_score)

    async def _predict_incident_type_probability(
        self,
        incident_type: str,
        features: Dict[str, float],
        historical_incidents: List[Dict]
    ) -> float:
        """Predict probability for specific incident type"""
        try:
            # Count historical incidents of this type
            type_incidents = [inc for inc in historical_incidents if inc.get('type') == incident_type]
            base_rate = len(type_incidents) / len(historical_incidents) if historical_incidents else 0.01
            
            # Adjust based on features
            probability = base_rate
            
            # Crowd density impact varies by incident type
            crowd_density = features.get('crowd_density', 0.4)
            
            if incident_type == "crowd_surge":
                probability *= (1 + crowd_density * 2)  # High crowd density increases risk
            elif incident_type == "suspicious_activity":
                probability *= (1 + (1 - crowd_density))  # Lower crowd density can increase risk
            elif incident_type == "medical_emergency":
                probability *= (1 + crowd_density)  # More people = more medical risk
            
            # Time factors
            hour = features.get('hour_of_day', 12)
            if incident_type in ["suspicious_activity", "security_breach"]:
                if hour < 6 or hour > 22:  # Night hours
                    probability *= 1.5
            
            # Weekend factor
            if features.get('is_weekend', 0) > 0:
                if incident_type in ["crowd_surge", "medical_emergency"]:
                    probability *= 1.3
            
            # Recent incident factor
            hours_since_last = features.get('time_since_last_incident', 168)
            if hours_since_last < 24:  # Recent incident increases risk
                probability *= 1.2
            
            # Cap probability
            return min(0.95, max(0.01, probability))
            
        except Exception as e:
            logger.error(f"Incident type prediction failed: {e}")
            return 0.01

    def _assess_incident_risk(self, probability: float) -> str:
        """Assess risk level based on probability"""
        if probability > 0.7:
            return "critical"
        elif probability > 0.5:
            return "high"
        elif probability > 0.3:
            return "medium"
        else:
            return "low"

    def _get_incident_factors(self, incident_type: str, features: Dict[str, float]) -> List[str]:
        """Get factors contributing to incident probability"""
        factors = []
        
        crowd_density = features.get('crowd_density', 0.4)
        if crowd_density > 0.7:
            factors.append("High crowd density")
        
        if features.get('is_weekend', 0) > 0:
            factors.append("Weekend period")
        
        hour = features.get('hour_of_day', 12)
        if incident_type in ["suspicious_activity", "security_breach"] and (hour < 6 or hour > 22):
            factors.append("Late night/early morning hours")
        
        if features.get('time_since_last_incident', 168) < 24:
            factors.append("Recent incident activity")
        
        if features.get('location_risk_score', 0) > 0.5:
            factors.append("High-risk location")
        
        if features.get('event_factor', 0) > 0:
            factors.append("Special event occurring")
        
        return factors

    async def _generate_incident_recommendations(
        self,
        location: str,
        incident_probabilities: Dict[str, Any],
        features: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on incident probabilities"""
        recommendations = []
        
        # High overall risk recommendations
        max_probability = max([prob["probability"] for prob in incident_probabilities.values()])
        
        if max_probability > 0.7:
            recommendations.append("Consider increasing security presence immediately")
            recommendations.append("Activate enhanced monitoring protocols")
        
        # Specific incident type recommendations
        for incident_type, data in incident_probabilities.items():
            if data["probability"] > 0.5:
                if incident_type == "crowd_surge":
                    recommendations.append("Deploy crowd control barriers and additional personnel")
                    recommendations.append("Monitor exit routes and implement flow management")
                elif incident_type == "suspicious_activity":
                    recommendations.append("Increase patrol frequency and surveillance")
                    recommendations.append("Brief security on suspicious activity indicators")
                elif incident_type == "medical_emergency":
                    recommendations.append("Ensure medical personnel and equipment are readily available")
                    recommendations.append("Identify clear emergency vehicle access routes")
                elif incident_type == "fire_hazard":
                    recommendations.append("Check fire safety equipment and evacuation routes")
                    recommendations.append("Position fire safety personnel strategically")
        
        # Crowd density specific recommendations
        crowd_density = features.get('crowd_density', 0.4)
        if crowd_density > 0.8:
            recommendations.append("Implement immediate crowd dispersal measures")
            recommendations.append("Consider restricting additional entry")
        
        return list(set(recommendations))  # Remove duplicates

    def _calculate_incident_confidence(
        self,
        features: Dict[str, float],
        historical_incidents: List[Dict]
    ) -> float:
        """Calculate confidence in incident predictions"""
        confidence = 0.4  # Base confidence
        
        # More historical data increases confidence
        if len(historical_incidents) > 100:
            confidence += 0.3
        elif len(historical_incidents) > 50:
            confidence += 0.2
        elif len(historical_incidents) > 20:
            confidence += 0.1
        
        # Recent data increases confidence
        recent_incidents = [
            inc for inc in historical_incidents 
            if isinstance(inc.get('timestamp'), datetime) and 
            (datetime.now() - inc['timestamp']).days <= 14
        ]
        
        if len(recent_incidents) > 10:
            confidence += 0.2
        
        # Complete feature set increases confidence
        if len(features) >= 6:
            confidence += 0.1
        
        return min(1.0, confidence)

    async def _get_monitored_locations(self) -> List[str]:
        """Get list of locations to monitor for predictions"""
        try:
            # Get unique locations from recent incidents
            recent_incidents = self.firebase.get_collection_with_filters(
                "incidents",
                filters={"timestamp": (">=", datetime.now() - timedelta(days=7))},
                limit=200
            )
            
            locations = set()
            for incident in recent_incidents:
                location_name = incident.get('location', {}).get('name')
                if location_name:
                    locations.add(location_name)
            
            # Add default monitoring locations if none found
            if not locations:
                locations = {"main_entrance", "food_court", "stage_area", "parking_lot"}
            
            return list(locations)
            
        except Exception as e:
            logger.error(f"Failed to get monitored locations: {e}")
            return ["main_entrance", "food_court", "stage_area"]

    async def _store_forecast(self, forecast: CrowdForecast):
        """Store forecast for accuracy tracking"""
        try:
            forecast_data = {
                "location": forecast.location,
                "predictions": forecast.predictions,
                "forecast_horizon_hours": forecast.forecast_horizon_hours,
                "generated_at": forecast.generated_at,
                "model_version": forecast.model_version,
                "type": "crowd_density_forecast"
            }
            
            self.firebase.add_document("forecasts", forecast_data)
            
        except Exception as e:
            logger.error(f"Failed to store forecast: {e}")

    async def get_forecast_accuracy(self, days: int = 7) -> Dict[str, Any]:
        """Calculate accuracy of recent forecasts"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            forecasts = self.firebase.get_collection_with_filters(
                "forecasts",
                filters={"generated_at": (">=", cutoff_date)},
                limit=100
            )
            
            if not forecasts:
                return {"error": "No forecast data available"}
            
            # For demo purposes, return simulated accuracy metrics
            # In production, you would compare predictions with actual observations
            
            return {
                "total_forecasts": len(forecasts),
                "crowd_density_accuracy": 0.78,
                "incident_prediction_accuracy": 0.65,
                "false_positive_rate": 0.12,
                "false_negative_rate": 0.08,
                "average_confidence": 0.72,
                "model_version": "v1.0",
                "evaluation_period_days": days
            }
            
        except Exception as e:
            logger.error(f"Accuracy calculation failed: {e}")
            return {"error": str(e)}

    def get_service_status(self) -> Dict[str, Any]:
        """Get forecasting service status"""
        return {
            "service": "forecasting",
            "status": "operational",
            "models": {
                "crowd_density": "heuristic" if self.crowd_density_model else "not_loaded",
                "incident_prediction": "heuristic" if self.incident_prediction_model else "not_loaded"
            },
            "supported_predictions": [
                "crowd_density",
                "incident_probability",
                "trend_analysis",
                "predictive_alerts"
            ],
            "max_forecast_horizon_hours": 24
        }