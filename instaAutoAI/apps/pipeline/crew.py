"""
CrewAI integration for agent orchestration.

Uses async CrewAI 0.100+ with hierarchical process and LangGraph checkpointing.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from crewai import Agent, Task, Crew
from crewai.process import Process
from langgraph.checkpoint.base import BaseCheckpointSaver

from .exceptions import AgentTimeoutError
from .state import CheckpointManager, PipelineState
from .llm_client import LLMClient
from .vram_manager import VRAMManager

logger = logging.getLogger(__name__)


class CrewOrchestrator:
    """
    Orchestrates CrewAI agents with async execution, VRAM management,
    and state persistence via LangGraph checkpointing.
    """

    def __init__(self, thread_id: str, state: PipelineState):
        self.thread_id = thread_id
        self.state = state
        self.checkpoint_manager = CheckpointManager()
        self.vram_manager = VRAMManager(required_mb=1024)  # adjust as needed
        self.llm = LLMClient.get_client()  # default OpenAI

    async def run(self, task_definition: Dict[str, Any]) -> PipelineState:
        """
        Execute a CrewAI crew based on the current state and task definition.

        :param task_definition: dict containing agents, tasks, and process.
        :return: Updated pipeline state.
        """
        # Restore state if a checkpoint exists
        checkpoint = await self.checkpoint_manager.load(self.thread_id)
        if checkpoint:
            self.state = checkpoint

        # Build agents and tasks
        agents = [
            Agent(
                role=agent_def["role"],
                goal=agent_def["goal"],
                backstory=agent_def.get("backstory", ""),
                llm=self.llm,
                allow_delegation=agent_def.get("allow_delegation", False),
                verbose=True,
            )
            for agent_def in task_definition["agents"]
        ]

        tasks = [
            Task(
                description=task_def["description"],
                expected_output=task_def.get("expected_output", ""),
                agent=agents[task_def["agent_index"]],
                async_execution=True,  # enable async tasks
            )
            for task_def in task_definition["tasks"]
        ]

        crew = Crew(
            agents=agents,
            tasks=tasks,
            process=Process.hierarchical if task_definition.get("hierarchical") else Process.sequential,
            manager_llm=self.llm if task_definition.get("hierarchical") else None,
            verbose=True,
        )

        # Execute with VRAM management
        async with self.vram_manager:
            try:
                # Use async kickoff (CrewAI 0.100+)
                result = await crew.kickoff_async()
                # Update state with result
                self.state["result"] = result
                self.state["progress"] = 100
                self.state["current_node"] = "complete"
                self.state["timestamp"] = datetime.utcnow().isoformat()
            except asyncio.TimeoutError:
                raise AgentTimeoutError(f"Crew execution timed out for thread {self.thread_id}")
            except Exception as e:
                self.state["error"] = str(e)
                raise

        # Save final checkpoint
        await self.checkpoint_manager.save(self.thread_id, self.state)
        return self.state

    async def cleanup(self):
        """Delete checkpoints after job completion."""
        await self.checkpoint_manager.delete(self.thread_id)