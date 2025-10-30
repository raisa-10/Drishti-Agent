"""
Project Drishti - Vertex AI Gemini Agent Service
Handles conversational AI using Vertex AI Gemini for situational analysis and recommendations
"""
import os
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting, HarmCategory, HarmBlockThreshold
from google.cloud import aiplatform
from google.auth import default
logger = logging.getLogger(__name__)
class VertexAIGeminiAgentService:
    """
    Intelligent conversational agent for crowd management and emergency response using Vertex AI
    """
    
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        """Initialize Vertex AI Gemini Agent service"""
        try:
            # Get project ID from environment or parameter
            self.project_id = project_id or os.getenv('GCP_PROJECT_ID') # Corrected env var name
            self.location = location or os.getenv('GOOGLE_CLOUD_REGION', 'us-central1')
            
            if not self.project_id:
                # Try to get from default credentials
                try:
                    credentials, project = default()
                    self.project_id = project
                except Exception as e:
                    logger.error(f"Could not determine project ID: {e}")
                    raise ValueError("Project ID must be provided via parameter, environment variable, or default credentials")
            
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            
            # Initialize AI Platform (for additional features if needed)
            aiplatform.init(project=self.project_id, location=self.location)
            
            # Safety settings
            safety_settings = [
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
                ),
            ]
            
            # Initialize the model with generation config
            self.generation_config = {
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1000,
            }
            
            self.model = GenerativeModel(
                model_name="gemini-2.0-flash-001",
                safety_settings=safety_settings,
                generation_config=self.generation_config
            )
            
            # Initialize conversation history
            self.conversation_history = {}
            
            # System prompts for different scenarios
            self.system_prompts = {
                "crowd_management": self._get_crowd_management_prompt(),
                "emergency_response": self._get_emergency_response_prompt(),
                "situation_analysis": self._get_situation_analysis_prompt(),
                "general_assistant": self._get_general_assistant_prompt()
            }
            
            logger.info(f"✅ Vertex AI Gemini Agent service initialized for project: {self.project_id} in {self.location}")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Vertex AI Gemini Agent: {e}")
            raise
    async def generate_contextual_response(
        self, 
        user_message: str, 
        context_data: Dict[str, Any] = None,
        session_id: str = "default",
        conversation_type: str = "general_assistant"
    ) -> str:
        """
        Generate contextual response based on current system state and user query
        """
        try:
            logger.info(f"Generating response for: {user_message[:50]}...")
            
            # Get conversation history
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            
            # Build context prompt
            context_prompt = self._build_context_prompt(context_data, conversation_type)
            
            # Combine system prompt, context, and user message
            full_prompt = f"""
{self.system_prompts.get(conversation_type, self.system_prompts['general_assistant'])}
CURRENT CONTEXT:
{context_prompt}
CONVERSATION HISTORY:
{self._format_conversation_history(session_id)}
USER MESSAGE: {user_message}
Please provide a helpful, contextual response as the Drishti AI Assistant.
"""
            
            # Generate response using Vertex AI
            response = self.model.generate_content(
                contents=[full_prompt],
                generation_config=self.generation_config
            )
            
            if response.candidates and len(response.candidates) > 0:
                generated_text = response.candidates[0].content.parts[0].text
                
                # Update conversation history
                self.conversation_history[session_id].append({
                    "user": user_message,
                    "assistant": generated_text,
                    "timestamp": datetime.now().isoformat(),
                    "context_type": conversation_type
                })
                
                # Keep only last 10 exchanges
                if len(self.conversation_history[session_id]) > 10:
                    self.conversation_history[session_id] = self.conversation_history[session_id][-10:]
                
                logger.info("Response generated successfully")
                return generated_text
            else:
                logger.warning("No response generated from Vertex AI Gemini")
                return "I apologize, but I'm having trouble generating a response right now. Please try again."
                
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return "I'm experiencing technical difficulties. Please contact the system administrator if this persists."
    async def analyze_situation(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a specific incident and provide recommendations
        """
        try:
            analysis_prompt = f"""
As the Drishti AI Assistant, analyze this incident and provide actionable recommendations:
INCIDENT DATA:
{json.dumps(incident_data, indent=2, default=str)}
Please provide:
1. Situation Assessment (severity, immediate risks)
2. Recommended Actions (specific steps to take)
3. Resource Requirements (units needed, equipment)
4. Timeline (estimated response/resolution time)
5. Potential Escalation Scenarios
Format your response as a structured analysis.
"""
            
            response = self.model.generate_content(
                contents=[analysis_prompt],
                generation_config=self.generation_config
            )
            
            if response.candidates and len(response.candidates) > 0:
                analysis_text = response.candidates[0].content.parts[0].text
                
                # Parse structured response (simplified)
                return {
                    "analysis": analysis_text,
                    "timestamp": datetime.now().isoformat(),
                    "confidence": 0.85,
                    "recommendations": self._extract_recommendations(analysis_text)
                }
            
            return {"error": "Failed to generate analysis"}
            
        except Exception as e:
            logger.error(f"Situation analysis failed: {e}")
            return {"error": str(e)}
    async def generate_incident_summary(self, incidents: List[Dict[str, Any]]) -> str:
        """
        Generate executive summary of current incidents
        """
        try:
            if not incidents:
                return "No active incidents at this time. All systems are operating normally."
            
            summary_prompt = f"""
As the Drishti AI Assistant, create an executive summary of the current incident situation:
ACTIVE INCIDENTS:
{json.dumps(incidents, indent=2, default=str)}
Provide a concise executive summary including:
- Overall situation status
- Number of incidents by type and severity
- Key concerns requiring immediate attention
- Resource allocation status
- Recommended priorities
Keep the summary professional and action-oriented.
"""
            
            response = self.model.generate_content(
                contents=[summary_prompt],
                generation_config=self.generation_config
            )
            
            if response.candidates and len(response.candidates) > 0:
                return response.candidates[0].content.parts[0].text
            
            return "Unable to generate incident summary at this time."
            
        except Exception as e:
            logger.error(f"Incident summary generation failed: {e}")
            return f"Error generating summary: {str(e)}"
    async def suggest_dispatch_strategy(
        self, 
        incident: Dict[str, Any], 
        available_units: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Suggest optimal dispatch strategy for an incident
        """
        try:
            dispatch_prompt = f"""
As the Drishti AI Assistant, recommend the optimal dispatch strategy:
INCIDENT:
{json.dumps(incident, indent=2, default=str)}
AVAILABLE UNITS:
{json.dumps(available_units, indent=2, default=str)}
Analyze and recommend:
1. Which units to dispatch (with reasons)
2. Priority order and staging
3. Estimated response times
4. Special considerations
5. Backup/escalation options
Provide specific unit IDs and clear rationale.
"""
            
            response = self.model.generate_content(
                contents=[dispatch_prompt],
                generation_config=self.generation_config
            )
            
            if response.candidates and len(response.candidates) > 0:
                strategy_text = response.candidates[0].content.parts[0].text
                
                return {
                    "strategy": strategy_text,
                    "recommended_units": self._extract_unit_recommendations(strategy_text, available_units),
                    "estimated_response_time": self._estimate_response_time(incident, available_units),
                    "confidence": 0.8
                }
            
            return {"error": "Failed to generate dispatch strategy"}
            
        except Exception as e:
            logger.error(f"Dispatch strategy generation failed: {e}")
            return {"error": str(e)}
    async def analyze_with_multimodal(
        self, 
        text_prompt: str, 
        image_data: bytes = None, 
        image_mime_type: str = "image/jpeg"
    ) -> str:
        """
        Analyze using multimodal capabilities (text + image)
        """
        try:
            contents = [text_prompt]
            
            if image_data:
                # Create image part
                image_part = Part.from_data(
                    data=image_data,
                    mime_type=image_mime_type
                )
                contents.append(image_part)
            
            response = self.model.generate_content(
                contents=contents,
                generation_config=self.generation_config
            )
            
            if response.candidates and len(response.candidates) > 0:
                return response.candidates[0].content.parts[0].text
            
            return "Unable to analyze the provided content."
            
        except Exception as e:
            logger.error(f"Multimodal analysis failed: {e}")
            return f"Error during analysis: {str(e)}"
    def _build_context_prompt(self, context_data: Dict[str, Any] = None, conversation_type: str = "general") -> str:
        """Build context prompt from current system state"""
        if not context_data:
            return "No specific context data available."
        
        context_parts = []
        
        # Recent incidents
        if "recent_incidents" in context_data:
            incidents = context_data["recent_incidents"]
            if incidents:
                context_parts.append(f"Recent Incidents ({len(incidents)}):")
                for incident in incidents[:5]:  # Last 5 incidents
                    context_parts.append(f"- {incident.get('type', 'Unknown')}: {incident.get('description', 'No description')[:100]}")
            else:
                context_parts.append("No recent incidents.")
        
        # System status
        if "system_status" in context_data:
            context_parts.append(f"System Status: {context_data['system_status']}")
        
        # Current time
        if "timestamp" in context_data:
            context_parts.append(f"Current Time: {context_data['timestamp']}")
        
        # Active alerts
        if "active_alerts" in context_data:
            alerts = context_data["active_alerts"]
            if alerts:
                context_parts.append(f"Active Alerts: {len(alerts)} alerts requiring attention")
        
        # Available units
        if "available_units" in context_data:
            context_parts.append(f"Available Security Units: {context_data['available_units']}")
        
        return "\n".join(context_parts) if context_parts else "Normal operational status."
    def _format_conversation_history(self, session_id: str) -> str:
        """Format conversation history for context"""
        if session_id not in self.conversation_history:
            return "No previous conversation."
        
        history = self.conversation_history[session_id][-3:]  # Last 3 exchanges
        formatted = []
        
        for exchange in history:
            formatted.append(f"User: {exchange['user']}")
            formatted.append(f"Assistant: {exchange['assistant'][:200]}...")
        
        return "\n".join(formatted) if formatted else "No previous conversation."
    def _extract_recommendations(self, analysis_text: str) -> List[str]:
        """Extract actionable recommendations from analysis"""
        # Simple extraction - in production, you might use more sophisticated NLP
        recommendations = []
        lines = analysis_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'must', 'action']):
                if len(line) > 10 and len(line) < 200:
                    recommendations.append(line)
        
        return recommendations[:5]  # Top 5 recommendations
    def _extract_unit_recommendations(self, strategy_text: str, available_units: List[Dict]) -> List[str]:
        """Extract recommended unit IDs from strategy text"""
        recommended = []
        unit_ids = [unit.get('id', '') for unit in available_units]
        
        # Look for unit IDs mentioned in the strategy text
        for unit_id in unit_ids:
            if unit_id and unit_id.lower() in strategy_text.lower():
                recommended.append(unit_id)
        
        # If no specific units mentioned, recommend based on incident type
        if not recommended and available_units:
            # Default to closest/most suitable units (simplified logic)
            recommended = [unit.get('id') for unit in available_units[:2] if unit.get('status') == 'available']
        
        return recommended
    def _estimate_response_time(self, incident: Dict[str, Any], available_units: List[Dict]) -> int:
        """Estimate response time in minutes"""
        # Simplified estimation - in production, would use actual distance/routing
        base_time = 5  # Base response time
        
        # Adjust based on incident severity
        severity = incident.get('severity', 'medium')
        if severity == 'critical':
            base_time = 3
        elif severity == 'high':
            base_time = 4
        elif severity == 'low':
            base_time = 8
        
        # Adjust based on available units
        if not available_units:
            base_time += 10
        elif len(available_units) < 2:
            base_time += 3
        
        return base_time
    def _get_crowd_management_prompt(self) -> str:
        """System prompt for crowd management scenarios"""
        return """
You are the Drishti AI Assistant, an expert in crowd management and public safety. Your role is to:
1. Analyze crowd dynamics and density patterns
2. Identify potential crowd surge risks
3. Recommend crowd flow management strategies
4. Suggest preventive measures for large gatherings
5. Provide real-time guidance during crowd incidents
Key principles:
- Safety is the top priority
- Prevention is better than reaction
- Clear, actionable communication
- Consider venue layout and exit strategies
- Account for crowd psychology and behavior patterns
Always provide specific, implementable recommendations with clear rationale.
"""
    def _get_emergency_response_prompt(self) -> str:
        """System prompt for emergency response scenarios"""
        return """
You are the Drishti AI Assistant, specialized in emergency response coordination. Your responsibilities include:
1. Rapid situation assessment and risk evaluation
2. Resource allocation and dispatch optimization  
3. Incident command coordination
4. Evacuation planning and execution
5. Multi-agency response coordination
Emergency response priorities:
- Life safety first
- Incident stabilization
- Property protection
- Environmental protection
- Post-incident recovery
Provide clear, time-sensitive recommendations with specific actions, timelines, and resource requirements.
"""
    def _get_situation_analysis_prompt(self) -> str:
        """System prompt for situational analysis"""
        return """
You are the Drishti AI Assistant, expert in situational awareness and threat assessment. You excel at:
1. Multi-source information synthesis
2. Pattern recognition and trend analysis
3. Risk assessment and threat prioritization
4. Predictive analysis and scenario planning
5. Decision support and recommendation generation
Analysis framework:
- What is happening? (Current state)
- Why is it happening? (Root causes)
- What could happen next? (Projections)
- What should be done? (Recommendations)
- What resources are needed? (Requirements)
Provide comprehensive yet concise analysis with clear action items.
"""
    def _get_general_assistant_prompt(self) -> str:
        """System prompt for general assistance"""
        return """
You are the Drishti AI Assistant, an intelligent command center assistant for crowd management and public safety operations. You help security commanders and operators by:
1. Providing real-time situational awareness
2. Answering questions about incidents, units, and system status
3. Offering expert guidance on security protocols
4. Assisting with decision-making and resource allocation
5. Explaining system capabilities and data interpretation
Your communication style is:
- Professional and authoritative
- Clear and concise
- Action-oriented
- Contextually aware
- Supportive of human decision-makers
You have access to real-time data about:
- Active incidents and alerts
- Security unit locations and status
- System performance metrics
- Historical incident patterns
- Standard operating procedures
Always prioritize safety and provide practical, implementable advice.
"""
    async def handle_emergency_query(self, query: str, emergency_context: Dict[str, Any]) -> str:
        """Handle urgent emergency queries with priority response"""
        try:
            emergency_prompt = f"""
EMERGENCY QUERY - PRIORITY RESPONSE REQUIRED
Query: {query}
Emergency Context:
{json.dumps(emergency_context, indent=2, default=str)}
This is an emergency situation requiring immediate, actionable guidance. Provide:
1. Immediate actions to take (next 2-3 minutes)
2. Critical safety considerations
3. Resource mobilization needs
4. Communication requirements
5. Follow-up actions
Be direct, specific, and time-conscious in your response.
"""
            
            response = self.model.generate_content(
                contents=[emergency_prompt],
                generation_config={**self.generation_config, "temperature": 0.3}  # Lower temperature for emergency
            )
            
            if response.candidates and len(response.candidates) > 0:
                return f"🚨 EMERGENCY RESPONSE:\n\n{response.candidates[0].content.parts[0].text}"
            
            return "🚨 EMERGENCY: Unable to generate response. Please contact emergency services immediately."
            
        except Exception as e:
            logger.error(f"Emergency query handling failed: {e}")
            return "🚨 EMERGENCY: System error. Please contact emergency services immediately."
    async def generate_shift_briefing(self, shift_data: Dict[str, Any]) -> str:
        """Generate briefing for incoming shift"""
        try:
            briefing_prompt = f"""
Generate a comprehensive shift briefing for incoming security personnel:
SHIFT DATA:
{json.dumps(shift_data, indent=2, default=str)}
Include:
1. Previous shift summary
2. Current active situations
3. Key areas of concern
4. Equipment status
5. Weather/environmental factors
6. Special instructions or alerts
7. Contact information and escalation procedures
Keep it concise but comprehensive - suitable for verbal briefing.
"""
            
            response = self.model.generate_content(
                contents=[briefing_prompt],
                generation_config=self.generation_config
            )
            
            if response.candidates and len(response.candidates) > 0:
                return response.candidates[0].content.parts[0].text
            
            return "Unable to generate shift briefing at this time."
            
        except Exception as e:
            logger.error(f"Shift briefing generation failed: {e}")
            return f"Error generating briefing: {str(e)}"
    async def analyze_crowd_patterns(self, crowd_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze crowd movement and density patterns"""
        try:
            pattern_prompt = f"""
Analyze these crowd patterns and provide insights:
CROWD DATA:
{json.dumps(crowd_data, indent=2, default=str)}
Provide analysis on:
1. Density trends and hotspots
2. Movement patterns and flow issues
3. Potential congestion points
4. Risk factors and early warnings
5. Optimization recommendations
Focus on actionable insights for crowd management.
"""
            
            response = self.model.generate_content(
                contents=[pattern_prompt],
                generation_config=self.generation_config
            )
            
            if response.candidates and len(response.candidates) > 0:
                analysis_text = response.candidates[0].content.parts[0].text
                
                return {
                    "analysis": analysis_text,
                    "risk_level": self._assess_crowd_risk(crowd_data),
                    "recommendations": self._extract_recommendations(analysis_text),
                    "timestamp": datetime.now().isoformat()
                }
            
            return {"error": "Failed to analyze crowd patterns"}
            
        except Exception as e:
            logger.error(f"Crowd pattern analysis failed: {e}")
            return {"error": str(e)}
    def _assess_crowd_risk(self, crowd_data: List[Dict[str, Any]]) -> str:
        """Assess overall crowd risk level"""
        if not crowd_data:
            return "low"
        
        # Simple risk assessment based on density values
        max_density = max([item.get('density', 0) for item in crowd_data], default=0)
        
        if max_density > 0.8:
            return "critical"
        elif max_density > 0.6:
            return "high"
        elif max_density > 0.4:
            return "medium"
        else:
            return "low"
    def clear_conversation_history(self, session_id: str = None):
        """Clear conversation history for a session or all sessions"""
        if session_id:
            if session_id in self.conversation_history:
                del self.conversation_history[session_id]
                logger.info(f"Cleared conversation history for session {session_id}")
        else:
            self.conversation_history.clear()
            logger.info("Cleared all conversation history")
    def get_conversation_stats(self) -> Dict[str, Any]:
        """Get conversation statistics"""
        total_sessions = len(self.conversation_history)
        total_exchanges = sum(len(history) for history in self.conversation_history.values())
        
        return {
            "total_sessions": total_sessions,
            "total_exchanges": total_exchanges,
            "active_sessions": [sid for sid, history in self.conversation_history.items() if history],
            "service_status": "operational",
            "project_id": self.project_id,
            "location": self.location
        }
    async def test_connection(self) -> Dict[str, Any]:
        """Test Vertex AI Gemini connection"""
        try:
            test_response = self.model.generate_content(
                contents=["Hello, this is a connection test."],
                generation_config={"temperature": 0.1, "max_output_tokens": 50}
            )
            
            if test_response.candidates and len(test_response.candidates) > 0:
                return {
                    "status": "connected",
                    "model": "gemini-2.0-flash-001",
                    "project_id": self.project_id,
                    "location": self.location,
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "No response from Vertex AI Gemini"
                }
                
        except Exception as e:
            logger.error(f"Vertex AI connection test failed: {e}")
            return {
                "status": "error",
                "message": str(e),
                "project_id": self.project_id,
                "location": self.location
            }
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model_name": "gemini-2.0-flash-001",
            "provider": "vertex_ai",
            "project_id": self.project_id,
            "location": self.location,
            "generation_config": self.generation_config,
            "capabilities": [
                "text_generation",
                "multimodal_analysis",
                "conversation_history",
                "safety_filtering"
            ]
        }
    def set_generation_config(self, **kwargs):
        """Update generation configuration"""
        self.generation_config.update(kwargs)
        logger.info(f"Updated generation config: {self.generation_config}")
    async def batch_analyze(self, prompts: List[str]) -> List[str]:
        """Analyze multiple prompts in batch"""
        results = []
        
        for prompt in prompts:
            try:
                response = self.model.generate_content(
                    contents=[prompt],
                    generation_config=self.generation_config
                )
                
                if response.candidates and len(response.candidates) > 0:
                    results.append(response.candidates[0].content.parts[0].text)
                else:
                    results.append("No response generated")
                    
            except Exception as e:
                logger.error(f"Batch analysis failed for prompt: {e}")
                results.append(f"Error: {str(e)}")
        
        return results
    
    async def generate_zone_status_briefing(self, zone_name: str, incidents: List[Dict], units: List[Dict]) -> str:
        """Generates a detailed status briefing for a specific zone."""
        try:
            briefing_prompt = f"""
            You are 'Aegis', a senior AI security analyst. The commander has requested a status report for '{zone_name}'.
            Synthesize the provided data into a comprehensive but concise briefing.

            **CURRENT DATA FOR '{zone_name.upper()}':**

            **Active Incidents in Zone ({len(incidents)}):**
            {json.dumps(incidents, indent=2, default=str) if incidents else "No active incidents."}

            **Security Units in Zone ({len(units)}):**
            {json.dumps(units, indent=2, default=str) if units else "No units currently in this zone."}

            **YOUR TASK:**
            1.  **Provide a "Current Status" assessment:** (e.g., "All Clear," "Elevated Alert," "Active Incident Response").
            2.  **Write a "Detailed Summary":** Briefly explain what is happening in the zone. If there are no incidents, state that the zone is operating normally.
            3.  **List "Recommended Actions":** If there is an active incident, suggest what the commander should do next. If the zone is clear, suggest standard monitoring procedures. Be proactive.

            Keep the tone professional, direct, and authoritative.
            """

            response = self.model.generate_content(
                contents=[briefing_prompt],
                generation_config=self.generation_config
            )
            
            if response.candidates and len(response.candidates) > 0:
                return response.candidates[0].content.parts[0].text
            else:
                return "Unable to generate status report - no response from AI model."
                
        except Exception as e:
            logger.error(f"Failed to generate zone status briefing for {zone_name}: {e}")
            return "Unable to generate status report due to a system error."