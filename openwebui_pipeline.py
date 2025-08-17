"""
Open WebUI Pipeline for Sovereign Agent Platform
Exposes all 7 sovereign agents as functions in Open WebUI
"""

from typing import List, Union, Generator, Iterator, Dict, Any
import asyncio
import json
from datetime import datetime

from pydantic import BaseModel
import requests

from webui_integration import orchestrator, initialize_platform

class Pipeline:
    class Valves(BaseModel):
        """Pipeline configuration valves"""
        platform_url: str = "http://localhost:8000"
        auto_initialize: bool = True
        debug_mode: bool = False

    def __init__(self):
        self.name = "Sovereign Agent Platform"
        self.valves = self.Valves()
        self.initialized = False

    async def on_startup(self):
        """Initialize the platform on startup"""
        if self.valves.auto_initialize and not self.initialized:
            try:
                await initialize_platform()
                self.initialized = True
                print("✅ Sovereign Agent Platform initialized successfully")
            except Exception as e:
                print(f"❌ Failed to initialize platform: {e}")

    async def on_shutdown(self):
        """Cleanup on shutdown"""
        print("🔄 Shutting down Sovereign Agent Platform")

    def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Union[str, Generator, Iterator]:
        """Main pipeline processing function"""
        if not self.initialized:
            return "❌ Platform not initialized. Please restart the pipeline."

        # Extract agent selection from the message or use consciousness agent as default
        agent_id = self._extract_agent_id(user_message)

        # Process the request
        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                orchestrator.process_request(agent_id, user_message, {"messages": messages, "body": body})
            )
            loop.close()

            if result.get("success"):
                return self._format_response(result, agent_id)
            else:
                return f"❌ Error: {result.get('error', 'Unknown error')}"

        except Exception as e:
            return f"❌ Pipeline error: {str(e)}"

    def _extract_agent_id(self, message: str) -> str:
        """Extract which agent should handle the request"""
        message_lower = message.lower()

        # Agent selection keywords
        agent_keywords = {
            "consciousness_agent": ["consciousness", "think", "reason", "personality", "adapt"],
            "memory_agent": ["memory", "remember", "recall", "store", "experience"],
            "orchestration_agent": ["orchestrate", "workflow", "schedule", "manage", "coordinate"],
            "retrieval_agent": ["search", "find", "retrieve", "lookup", "document"],
            "monitoring_agent": ["monitor", "status", "alert", "performance", "health"],
            "governance_agent": ["policy", "audit", "compliance", "govern", "track"],
            "pipeline_agent": ["pipeline", "process", "data", "transform", "validate"]
        }

        for agent_id, keywords in agent_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return agent_id

        # Default to consciousness agent
        return "consciousness_agent"

    def _format_response(self, result: Dict[str, Any], agent_id: str) -> str:
        """Format the agent response for Open WebUI"""
        agent_info = orchestrator.agent_configs.get(agent_id, {})
        agent_name = getattr(agent_info, 'name', agent_id)

        response_content = result.get("response", "No response")

        # Format based on response type
        if isinstance(response_content, dict):
            if "text" in response_content:
                formatted_response = response_content["text"]
            else:
                formatted_response = json.dumps(response_content, indent=2)
        else:
            formatted_response = str(response_content)

        return f"""
🤖 **{agent_name}** responded:

{formatted_response}

---
*Processed at {result.get('timestamp', datetime.now().isoformat())}*
        """.strip()

# Function tools for each agent
class Functions:
    def __init__(self):
        pass

    def get_agent_status(self) -> dict:
        """
        Get the status and information of all sovereign agents.

        Returns:
            dict: Status information for all agents
        """
        if not orchestrator.agents:
            return {"error": "Platform not initialized"}

        return orchestrator.get_agent_info()

    async def consciousness_query(self, query: str, context: dict = None) -> dict:
        """
        Send a query to the Advanced Consciousness Agent for reasoning and personality-adapted responses.

        Args:
            query (str): The query to process
            context (dict): Additional context for the query

        Returns:
            dict: Response from the consciousness agent
        """
        return await orchestrator.process_request("consciousness_agent", query, context or {})

    async def memory_operation(self, operation: str, data: dict = None) -> dict:
        """
        Perform memory operations like storing experiences or retrieving context.

        Args:
            operation (str): The memory operation (store, retrieve, search)
            data (dict): Data for the operation

        Returns:
            dict: Result of the memory operation
        """
        query = f"Memory operation: {operation}"
        if data:
            query += f" with data: {json.dumps(data)}"

        return await orchestrator.process_request("memory_agent", query, data or {})

    async def orchestrate_workflow(self, workflow_request: str, parameters: dict = None) -> dict:
        """
        Orchestrate workflows and manage task scheduling.

        Args:
            workflow_request (str): Description of the workflow to execute
            parameters (dict): Workflow parameters

        Returns:
            dict: Workflow execution result
        """
        return await orchestrator.process_request("orchestration_agent", workflow_request, parameters or {})

    async def retrieve_information(self, search_query: str, filters: dict = None) -> dict:
        """
        Retrieve information using advanced RAG and semantic search.

        Args:
            search_query (str): The search query
            filters (dict): Additional search filters

        Returns:
            dict: Retrieved information and context
        """
        return await orchestrator.process_request("retrieval_agent", search_query, filters or {})

    async def monitor_system(self, metric_request: str, parameters: dict = None) -> dict:
        """
        Monitor system performance and get alerts.

        Args:
            metric_request (str): What metrics to monitor or retrieve
            parameters (dict): Monitoring parameters

        Returns:
            dict: System monitoring data
        """
        return await orchestrator.process_request("monitoring_agent", metric_request, parameters or {})

    async def governance_check(self, policy_request: str, context: dict = None) -> dict:
        """
        Perform governance checks and audit operations.

        Args:
            policy_request (str): The governance or policy request
            context (dict): Additional context for the check

        Returns:
            dict: Governance check result
        """
        return await orchestrator.process_request("governance_agent", policy_request, context or {})

    async def process_pipeline(self, pipeline_request: str, data: dict = None) -> dict:
        """
        Process data through pipelines and perform data transformations.

        Args:
            pipeline_request (str): Description of the pipeline operation
            data (dict): Data to process

        Returns:
            dict: Pipeline processing result
        """
        return await orchestrator.process_request("pipeline_agent", pipeline_request, data or {})
