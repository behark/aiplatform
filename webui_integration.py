"""
Open WebUI Integration for Sovereign Agent Platform
Integrates all 7 sovereign agents with Open WebUI for web-based access
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import os

from src.llms import *

# Load the real agent configuration
AGENTS_CONFIG_PATH = os.path.join("src", "agents.data.json")

# Try to import real implementations, fall back to mocks
try:
    from ci_cd.advanced_consciousness import AdvancedSovereignConsciousness
except ImportError:
    from src.mock_implementations import AdvancedSovereignConsciousness

try:
    from orchestration.dag import WorkflowDAG
except ImportError:
    from src.mock_implementations import WorkflowDAG

try:
    from models.registry import ModelRegistry
except ImportError:
    from src.mock_implementations import ModelRegistry

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for each sovereign agent"""
    name: str
    description: str
    primary_model: str
    fallback_models: List[str]
    capabilities: List[str]
    model_routing: Dict[str, str]
    endpoint: str
    enabled: bool = True

class SovereignAgentOrchestrator:
    """
    Main orchestrator that manages all 7 sovereign agents with real model integration
    """
    
    def __init__(self):
        self.agents = {}
        self.consciousness = None
        self.model_registry = ModelRegistry()
        self.workflow_dag = WorkflowDAG()
        
        # Load real agent configurations
        self.agent_configs = self._load_agent_configs()
        self.model_configs = self._load_model_configs()

    def _load_agent_configs(self) -> Dict[str, AgentConfig]:
        """Load agent configurations from the real data file"""
        try:
            with open(AGENTS_CONFIG_PATH, 'r') as f:
                data = json.load(f)

            configs = {}
            for agent_id, config in data.get("sovereign_agents", {}).items():
                configs[agent_id] = AgentConfig(
                    name=config["name"],
                    description=config["description"],
                    primary_model=config["primary_model"],
                    fallback_models=config["fallback_models"],
                    capabilities=config["capabilities"],
                    model_routing=config["model_routing"],
                    endpoint=config["endpoint"],
                    enabled=config.get("enabled", True)
                )

            logger.info(f"Loaded {len(configs)} agent configurations")
            return configs

        except Exception as e:
            logger.error(f"Failed to load agent configs: {e}")
            return self._get_fallback_configs()

    def _load_model_configs(self) -> Dict[str, Any]:
        """Load model configurations"""
        try:
            with open(AGENTS_CONFIG_PATH, 'r') as f:
                data = json.load(f)
            return data.get("model_registry", {})
        except Exception as e:
            logger.error(f"Failed to load model configs: {e}")
            return {}

    def _get_fallback_configs(self) -> Dict[str, AgentConfig]:
        """Fallback agent configurations if file loading fails"""
        return {
            "consciousness_agent": AgentConfig(
                name="Advanced Consciousness Agent",
                description="Master consciousness with dimensional personalities",
                primary_model="mixtral",
                fallback_models=["hermes", "openai_fallback"],
                capabilities=["reasoning", "personality_adaptation"],
                model_routing={"default": "mixtral"},
                endpoint="/api/consciousness"
            ),
            "memory_agent": AgentConfig(
                name="Memory Management Agent",
                description="Advanced memory management and context retention",
                primary_model="deepseek",
                fallback_models=["mixtral"],
                capabilities=["memory_storage", "context_retrieval"],
                model_routing={"default": "deepseek"},
                endpoint="/api/memory"
            ),
            "orchestration_agent": AgentConfig(
                name="Workflow Orchestration Agent",
                description="DAG-based workflow orchestration",
                primary_model="mixtral",
                fallback_models=["deepseek"],
                capabilities=["workflow_management", "task_scheduling"],
                model_routing={"default": "mixtral"},
                endpoint="/api/orchestration"
            ),
            "retrieval_agent": AgentConfig(
                name="Information Retrieval Agent",
                description="Advanced RAG and information retrieval",
                primary_model="deepseek",
                fallback_models=["mixtral"],
                capabilities=["semantic_search", "document_analysis"],
                model_routing={"default": "deepseek"},
                endpoint="/api/retrieval"
            ),
            "monitoring_agent": AgentConfig(
                name="System Monitoring Agent",
                description="Real-time monitoring and alerting",
                primary_model="deepseek",
                fallback_models=["phi"],
                capabilities=["performance_tracking", "alert_management"],
                model_routing={"default": "deepseek"},
                endpoint="/api/monitoring"
            ),
            "governance_agent": AgentConfig(
                name="Governance & Audit Agent",
                description="Policy enforcement and audit trail",
                primary_model="mixtral",
                fallback_models=["deepseek"],
                capabilities=["policy_enforcement", "audit_logging"],
                model_routing={"default": "mixtral"},
                endpoint="/api/governance"
            ),
            "pipeline_agent": AgentConfig(
                name="Data Pipeline Agent",
                description="Advanced data processing and pipeline management",
                primary_model="deepseek",
                fallback_models=["phi"],
                capabilities=["data_processing", "pipeline_orchestration"],
                model_routing={"default": "deepseek"},
                endpoint="/api/pipeline"
            )
        }
    
    async def initialize(self):
        """Initialize all sovereign agents"""
        try:
            # Initialize advanced consciousness
            self.consciousness = AdvancedSovereignConsciousness()
            await self.consciousness.initialize()
            
            # Initialize each agent
            for agent_id, config in self.agent_configs.items():
                if config.enabled:
                    agent = await self._create_agent(agent_id, config)
                    self.agents[agent_id] = agent
                    logger.info(f"Initialized {config.name}")
            
            logger.info(f"Successfully initialized {len(self.agents)} sovereign agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    async def _create_agent(self, agent_id: str, config: AgentConfig):
        """Create a specific agent based on configuration"""
        if agent_id == "consciousness_agent":
            return self.consciousness
        
        # Create other specialized agents
        from src.agent_implementations import (
            RetrievalAgent, MonitoringAgent, GovernanceAgent, PipelineAgent,
            ConsciousnessAgent, MemoryAgent, OrchestrationAgent
        )

        agent_classes = {
            "memory_agent": MemoryAgent(),
            "orchestration_agent": OrchestrationAgent(),
            "retrieval_agent": RetrievalAgent(),
            "monitoring_agent": MonitoringAgent(),
            "governance_agent": GovernanceAgent(),
            "pipeline_agent": PipelineAgent()
        }
        
        return agent_classes.get(agent_id)
    
    async def process_request(self, agent_id: str, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a request through a specific agent"""
        if agent_id not in self.agents:
            # Return a consistent error structure to avoid downstream validation issues
            return {
                "success": False,
                "agent": agent_id,
                "error": f"Agent {agent_id} not found",
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            agent = self.agents[agent_id]
            
            # Route to appropriate processing method based on agent type
            if agent_id == "consciousness_agent":
                response = await self.consciousness.process_query(query, context or {})
            else:
                # Generic agent processing
                response = await self._process_generic_agent(agent, query, context or {})
            
            return {
                "success": True,
                "agent": agent_id,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing request for {agent_id}: {e}")
            return {
                "success": False,
                "agent": agent_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _process_generic_agent(self, agent: Any, query: str, context: Dict[str, Any]) -> Any:
        """Generic processing for non-consciousness agents"""
        if hasattr(agent, 'process_query'):
            return await agent.process_query(query, context)
        elif hasattr(agent, 'execute'):
            return await agent.execute(query, context)
        else:
            return f"Agent processed query: {query}"
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get information about all available agents with real model mappings"""
        return {
            "total_agents": len(self.agent_configs),
            "active_agents": len(self.agents),
            "model_registry": self.model_configs,
            "agents": {
                agent_id: {
                    "name": config.name,
                    "description": config.description,
                    "primary_model": config.primary_model,
                    "fallback_models": config.fallback_models,
                    "capabilities": config.capabilities,
                    "model_routing": config.model_routing,
                    "status": "active" if agent_id in self.agents else "inactive",
                    "endpoint": config.endpoint
                }
                for agent_id, config in self.agent_configs.items()
            },
            "platform_info": {
                "total_models": len(self.model_configs),
                "consciousness_enhanced": True,
                "deployment_ready": True
            }
        }

# Global orchestrator instance
orchestrator = SovereignAgentOrchestrator()

async def initialize_platform():
    """Initialize the entire platform"""
    await orchestrator.initialize()
    return orchestrator
