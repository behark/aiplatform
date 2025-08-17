"""
Open WebUI Pipeline Integration for Sovereign Agent Platform
This file ensures all 7 agents are available as functions in Open WebUI
"""

from typing import List, Union, Generator, Iterator, Dict, Any, Optional
import asyncio
import json
import requests
from datetime import datetime

try:
    from pydantic import BaseModel
except ImportError:
    # Fallback for systems without pydantic
    class BaseModel:
        pass

class Pipeline:
    """
    Open WebUI Pipeline that integrates all 7 Sovereign Agents
    """
    class Valves(BaseModel):
        # Configuration for the pipeline
        SOVEREIGN_API_BASE: str = "http://localhost:8000"
        ENABLE_ALL_AGENTS: bool = True
        DEBUG_MODE: bool = False

        # Agent endpoints
        CONSCIOUSNESS_ENDPOINT: str = "/consciousness/query"
        MEMORY_ENDPOINT: str = "/memory/operation"
        ORCHESTRATION_ENDPOINT: str = "/orchestration/workflow"
        RETRIEVAL_ENDPOINT: str = "/retrieval/search"
        MONITORING_ENDPOINT: str = "/monitoring/status"
        GOVERNANCE_ENDPOINT: str = "/governance/check"
        PIPELINE_ENDPOINT: str = "/pipeline/process"

    def __init__(self):
        self.name = "Sovereign Agent Platform"
        self.description = "Access to all 7 Sovereign Agents through Open WebUI"
        self.valves = self.Valves()

        # Agent metadata for Open WebUI
        self.agents = {
            "consciousness": {
                "name": "🧠 Advanced Consciousness Agent",
                "description": "Master reasoning with dimensional personalities",
                "keywords": ["analyze", "think", "reason", "consciousness", "intelligence"]
            },
            "memory": {
                "name": "💾 Memory Core Agent",
                "description": "Experience storage and context retrieval",
                "keywords": ["remember", "store", "recall", "memory", "experience"]
            },
            "orchestration": {
                "name": "🔄 Workflow Orchestration Agent",
                "description": "DAG-based task management and coordination",
                "keywords": ["orchestrate", "workflow", "schedule", "manage", "coordinate"]
            },
            "retrieval": {
                "name": "🔍 Information Retrieval Agent",
                "description": "Advanced RAG and semantic search",
                "keywords": ["search", "find", "retrieve", "lookup", "information"]
            },
            "monitoring": {
                "name": "📊 System Monitoring Agent",
                "description": "Real-time performance tracking",
                "keywords": ["monitor", "status", "performance", "metrics", "health"]
            },
            "governance": {
                "name": "🛡️ Governance & Audit Agent",
                "description": "Policy enforcement and compliance",
                "keywords": ["policy", "audit", "compliance", "governance", "security"]
            },
            "pipeline": {
                "name": "⚡ Data Pipeline Agent",
                "description": "Advanced data processing and transformation",
                "keywords": ["process", "transform", "pipeline", "data", "etl"]
            }
        }

    def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Union[str, Generator, Iterator]:
        """
        Main pipeline function - processes user messages through appropriate agents
        """
        try:
            # Determine which agent should handle the request
            selected_agent = self._select_agent(user_message, model_id)

            # Process through the selected agent
            response = self._process_with_agent(selected_agent, user_message, messages, body)

            return response

        except Exception as e:
            return f"❌ Error processing request: {str(e)}\n\nPlease check that your Sovereign Agent Platform is running on {self.valves.SOVEREIGN_API_BASE}"

    def _select_agent(self, user_message: str, model_id: str) -> str:
        """
        Intelligently select which agent should handle the request
        """
        message_lower = user_message.lower()

        # Check for explicit agent selection in model_id
        for agent_id in self.agents.keys():
            if agent_id in model_id.lower():
                return agent_id

        # Smart routing based on keywords in the message
        for agent_id, agent_info in self.agents.items():
            for keyword in agent_info["keywords"]:
                if keyword in message_lower:
                    return agent_id

        # Default to consciousness agent for general queries
        return "consciousness"

    def _process_with_agent(self, agent_id: str, user_message: str, messages: List[dict], body: dict) -> str:
        """
        Process the request through the specified agent
        """
        try:
            # Prepare the request
            agent_data = {
                "query": user_message,
                "context": {
                    "messages": messages,
                    "body": body,
                    "agent_id": agent_id
                }
            }

            # Get agent endpoint
            endpoint_map = {
                "consciousness": self.valves.CONSCIOUSNESS_ENDPOINT,
                "memory": self.valves.MEMORY_ENDPOINT,
                "orchestration": self.valves.ORCHESTRATION_ENDPOINT,
                "retrieval": self.valves.RETRIEVAL_ENDPOINT,
                "monitoring": self.valves.MONITORING_ENDPOINT,
                "governance": self.valves.GOVERNANCE_ENDPOINT,
                "pipeline": self.valves.PIPELINE_ENDPOINT
            }

            endpoint = endpoint_map.get(agent_id, self.valves.CONSCIOUSNESS_ENDPOINT)
            url = f"{self.valves.SOVEREIGN_API_BASE}{endpoint}"

            # Make request to your Sovereign Agent Platform
            response = requests.post(
                url,
                json=agent_data,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                result = response.json()
                return self._format_response(agent_id, result, user_message)
            else:
                return f"❌ Agent {agent_id} returned error: {response.status_code}"

        except requests.exceptions.ConnectionError:
            return f"❌ Cannot connect to Sovereign Agent Platform at {self.valves.SOVEREIGN_API_BASE}\n\nPlease ensure your backend is running with all 7 agents."
        except Exception as e:
            return f"❌ Error processing with {agent_id} agent: {str(e)}"

    def _format_response(self, agent_id: str, result: dict, original_query: str) -> str:
        """
        Format the agent response for Open WebUI
        """
        agent_info = self.agents[agent_id]
        agent_name = agent_info["name"]

        # Extract response content
        if result.get("success"):
            response_data = result.get("response", {})
            if isinstance(response_data, dict):
                text = response_data.get("text", str(response_data))
            else:
                text = str(response_data)
        else:
            text = f"❌ Error: {result.get('error', 'Unknown error')}"

        # Format for Open WebUI
        formatted_response = f"""**{agent_name}** responded to: "{original_query}"

{text}

---
*Processed at {result.get('timestamp', datetime.now().isoformat())}*
"""

        return formatted_response

    def on_startup(self):
        """Called when the pipeline starts"""
        print(f"🚀 Sovereign Agent Platform Pipeline loaded!")
        print(f"📡 Connected to: {self.valves.SOVEREIGN_API_BASE}")
        print(f"🤖 Available agents: {', '.join(self.agents.keys())}")

    def on_shutdown(self):
        """Called when the pipeline shuts down"""
        print("👋 Sovereign Agent Platform Pipeline shutting down")

# Global pipeline instance for Open WebUI
pipeline = Pipeline()

# Function definitions for Open WebUI function calling
def consciousness_query(query: str) -> str:
    """
    🧠 Advanced Consciousness Agent - Master reasoning and personality adaptation

    Args:
        query (str): Your question or problem for advanced analysis

    Returns:
        str: Detailed response with advanced reasoning
    """
    try:
        response = requests.post(
            f"{pipeline.valves.SOVEREIGN_API_BASE}/consciousness/query",
            json={"query": query, "context": {}},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["response"].get("text", str(result["response"]))
            else:
                return f"Error: {result.get('error')}"
        else:
            return f"HTTP Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"

def search_information(query: str) -> str:
    """
    🔍 Information Retrieval Agent - Advanced search and knowledge synthesis

    Args:
        query (str): What you want to search for or retrieve

    Returns:
        str: Retrieved information and sources
    """
    try:
        response = requests.post(
            f"{pipeline.valves.SOVEREIGN_API_BASE}/retrieval/search",
            json={"search_query": query, "filters": {}},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["response"].get("text", str(result["response"]))
            else:
                return f"Error: {result.get('error')}"
        else:
            return f"HTTP Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"

def monitor_system(request: str = "general status") -> str:
    """
    📊 System Monitoring Agent - Real-time performance and health monitoring

    Args:
        request (str): What system metrics or status to check

    Returns:
        str: System monitoring data and metrics
    """
    try:
        response = requests.post(
            f"{pipeline.valves.SOVEREIGN_API_BASE}/monitoring/status",
            json={"metric_request": request, "parameters": {}},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["response"].get("text", str(result["response"]))
            else:
                return f"Error: {result.get('error')}"
        else:
            return f"HTTP Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"

def orchestrate_workflow(description: str) -> str:
    """
    🔄 Workflow Orchestration Agent - Create and manage complex workflows

    Args:
        description (str): Description of the workflow you want to create or execute

    Returns:
        str: Workflow orchestration results
    """
    try:
        response = requests.post(
            f"{pipeline.valves.SOVEREIGN_API_BASE}/orchestration/workflow",
            json={"workflow_request": description, "parameters": {}},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["response"].get("text", str(result["response"]))
            else:
                return f"Error: {result.get('error')}"
        else:
            return f"HTTP Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"

def process_data_pipeline(description: str) -> str:
    """
    ⚡ Data Pipeline Agent - Advanced data processing and transformation

    Args:
        description (str): Description of data processing or pipeline operation needed

    Returns:
        str: Data pipeline processing results
    """
    try:
        response = requests.post(
            f"{pipeline.valves.SOVEREIGN_API_BASE}/pipeline/process",
            json={"pipeline_request": description, "data": {}},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["response"].get("text", str(result["response"]))
            else:
                return f"Error: {result.get('error')}"
        else:
            return f"HTTP Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"

def governance_check(request: str) -> str:
    """
    🛡️ Governance & Audit Agent - Policy enforcement and compliance checking

    Args:
        request (str): Policy or compliance request to check

    Returns:
        str: Governance and audit results
    """
    try:
        response = requests.post(
            f"{pipeline.valves.SOVEREIGN_API_BASE}/governance/check",
            json={"policy_request": request, "context": {}},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["response"].get("text", str(result["response"]))
            else:
                return f"Error: {result.get('error')}"
        else:
            return f"HTTP Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"

def memory_operation(operation: str, data: str = "") -> str:
    """
    💾 Memory Core Agent - Store, retrieve, and manage experiences

    Args:
        operation (str): Memory operation (store, retrieve, search)
        data (str): Data for the memory operation

    Returns:
        str: Memory operation results
    """
    try:
        response = requests.post(
            f"{pipeline.valves.SOVEREIGN_API_BASE}/memory/operation",
            json={"operation": operation, "data": {"content": data}},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                return result["response"].get("text", str(result["response"]))
            else:
                return f"Error: {result.get('error')}"
        else:
            return f"HTTP Error: {response.status_code}"
    except Exception as e:
        return f"Connection error: {str(e)}"
