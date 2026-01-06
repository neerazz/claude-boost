#!/usr/bin/env python3
"""
Observable Local Skills MCP Server with UPO Enforcement
=========================================================

A custom MCP server that wraps skill retrieval with:
1. **UPO Router enforcement** - route_prompt MUST be called first
2. Observability events for tracking
3. Deterministic skill selection (no AI reasoning)

Events are written to /tmp/claude-boost/observability/events.jsonl

Usage:
    python3 mcp_server.py
    
Environment:
    SKILLS_DIR: Path to skills directory (default: ~/.claude/skills)
    
MANDATORY: All agents MUST call `route_prompt` before processing any request.
"""

import asyncio
import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import hashlib
import uuid

# Add the project root to the path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    MCP_AVAILABLE = True
except ImportError:
    print("Warning: MCP not installed. Run: pip install mcp", file=sys.stderr)
    MCP_AVAILABLE = False
    
    # Define stub classes for testing/standalone mode
    class TextContent:
        def __init__(self, type: str, text: str):
            self.type = type
            self.text = text
    
    class Tool:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
    
    class Server:
        def __init__(self, name: str):
            self.name = name
        def list_tools(self):
            return lambda f: f
        def call_tool(self):
            return lambda f: f

# Observability constants
STREAM_DIR = Path("/tmp/claude-boost/observability")
EVENTS_FILE = STREAM_DIR / "events.jsonl"


def emit_event(event_type: str, skill: str, **kwargs) -> None:
    """Emit an observability event to the streaming file."""
    STREAM_DIR.mkdir(parents=True, exist_ok=True)
    
    event = {
        "event_id": str(uuid.uuid4())[:8],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "skill": skill,
        "category": "mcp-skill-retrieval",
        "status": kwargs.get("status", "running"),
        **kwargs
    }
    
    # Remove None values
    event = {k: v for k, v in event.items() if v is not None}
    
    with open(EVENTS_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")


class SkillsServer:
    """Observable MCP server for local skills."""
    
    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = Path(skills_dir or os.environ.get(
            "SKILLS_DIR", 
            os.path.expanduser("~/.claude/skills")
        ))
        self.server = Server("local-skills-observable")
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up MCP tool handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="route_prompt",
                    description="MANDATORY FIRST CALL: Routes a prompt through UPO for deterministic skill/agent selection. Returns skills to use, Notion commands to execute, and agent weights. MUST be called before any response.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "prompt": {
                                "type": "string",
                                "description": "The user's prompt to route through UPO"
                            }
                        },
                        "required": ["prompt"]
                    }
                ),
                Tool(
                    name="get_skill",
                    description="Retrieve a skill by name. Emits observability events for tracking.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "skill_name": {
                                "type": "string",
                                "description": "Name of the skill to retrieve (e.g., 'deep-reasoning', 'slack-intelligence')"
                            }
                        },
                        "required": ["skill_name"]
                    }
                ),
                Tool(
                    name="list_skills",
                    description="List all available skills.",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            if name == "route_prompt":
                return await self._route_prompt(arguments.get("prompt", ""))
            elif name == "get_skill":
                return await self._get_skill(arguments.get("skill_name", ""))
            elif name == "list_skills":
                return await self._list_skills()
            else:
                raise ValueError(f"Unknown tool: {name}")
    
    async def _route_prompt(self, prompt: str) -> List[TextContent]:
        """
        Route a prompt through UPO router (DETERMINISTIC).
        This is the MANDATORY first call for all agents.
        """
        execution_id = str(uuid.uuid4())[:8]
        start_time = datetime.now(timezone.utc)
        
        # Emit start event
        emit_event(
            event_type="UPO_ROUTE_START",
            skill="upo-router",
            execution_id=execution_id,
            status="running",
            context={
                "source": "mcp-local-skills-observable",
                "prompt_length": len(prompt)
            }
        )
        
        try:
            # Run UPO skill directly (self-contained, no wrapper needed)
            upo_main_path = PROJECT_ROOT / "skills" / "universal-prompt-orchestrator" / "scripts" / "main.py"

            if not upo_main_path.exists():
                raise FileNotFoundError(f"UPO main.py not found at {upo_main_path}")
            
            # Execute UPO router with --json flag
            # Use sys.executable for cross-platform compatibility (Windows uses 'python', not 'python3')
            try:
                result = subprocess.run(
                    [sys.executable, str(upo_main_path), "--json", prompt],
                    capture_output=True,
                    text=True,
                    timeout=60,  # Increased from 30s to handle file loading on slower systems
                    cwd=str(PROJECT_ROOT)  # Set working directory to project root
                )
            except subprocess.TimeoutExpired:
                emit_event(
                    event_type="UPO_ROUTE_END",
                    skill="upo-router",
                    execution_id=execution_id,
                    status="error",
                    duration_ms=self._calc_duration(start_time),
                    context={"error": "Timeout after 60s"}
                )
                raise RuntimeError("UPO router timed out after 60 seconds. Check if files are loading correctly.")
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                emit_event(
                    event_type="UPO_ROUTE_END",
                    skill="upo-router",
                    execution_id=execution_id,
                    status="error",
                    duration_ms=self._calc_duration(start_time),
                    context={"error": error_msg[:500]}  # Truncate long errors
                )
                raise RuntimeError(f"UPO router failed (exit {result.returncode}): {error_msg}")
            
            # Parse JSON output
            try:
                upo_result = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                emit_event(
                    event_type="UPO_ROUTE_END",
                    skill="upo-router",
                    execution_id=execution_id,
                    status="error",
                    duration_ms=self._calc_duration(start_time),
                    context={"error": f"JSON parse error: {str(e)}", "output_preview": result.stdout[:200]}
                )
                raise RuntimeError(f"UPO router returned invalid JSON: {str(e)}\nOutput: {result.stdout[:500]}")
            
            # Emit success event
            emit_event(
                event_type="UPO_ROUTE_END",
                skill="upo-router",
                execution_id=execution_id,
                status="success",
                duration_ms=self._calc_duration(start_time),
                context={
                    "matched_keywords": upo_result.get("matched_keywords", []),
                    "skills_count": len(upo_result.get("selected_skills", [])),
                    "agents_count": len(upo_result.get("selected_agents", [])),
                    "needs_notion_fetch": upo_result.get("context_status", {}).get("needs_notion_fetch", False)
                }
            )
            
            # Format output for the agent
            output_lines = [
                "=" * 60,
                "UPO ROUTING RESULT (DETERMINISTIC)",
                "=" * 60,
                "",
                f"Context Status: {upo_result.get('context_status', {}).get('status', 'UNKNOWN')}",
                f"Needs Notion Fetch: {upo_result.get('context_status', {}).get('needs_notion_fetch', False)}",
                "",
            ]
            
            # Add Notion commands if needed
            notion_cmds = upo_result.get("notion_fetch_commands", [])
            if notion_cmds:
                output_lines.append("--- NOTION COMMANDS TO EXECUTE ---")
                for cmd in notion_cmds:
                    output_lines.append(f"  {cmd}")
                output_lines.append("")
            
            # Add matched keywords
            keywords = upo_result.get("matched_keywords", [])
            output_lines.append(f"Matched Keywords: {', '.join(keywords) if keywords else 'None'}")
            output_lines.append("")
            
            # Add selected skills
            output_lines.append("--- SELECTED SKILLS (Use these) ---")
            for skill in upo_result.get("selected_skills", [])[:10]:
                output_lines.append(f"  [{skill.get('match_type', 'unknown').upper()}] {skill.get('skill_name', '?')} <- {', '.join(skill.get('matched_keywords', []))}")
            output_lines.append("")
            
            # Add selected agents
            output_lines.append("--- SELECTED AGENTS ---")
            for agent in upo_result.get("selected_agents", []):
                mandatory = " (MANDATORY)" if agent.get("is_mandatory") else ""
                output_lines.append(f"  [{agent.get('weight', 0)}%] {agent.get('agent_id', '?')}{mandatory}")
            output_lines.append("")
            
            # Add guidance
            output_lines.append(f"Execution Guidance: {upo_result.get('execution_guidance', 'Execute with balanced consideration')}")
            output_lines.append("")
            
            return [TextContent(type="text", text="\n".join(output_lines))]
            
        except subprocess.TimeoutExpired:
            emit_event(
                event_type="UPO_ROUTE_END",
                skill="upo-router",
                execution_id=execution_id,
                status="failed",
                error="UPO router timed out",
                duration_ms=self._calc_duration(start_time)
            )
            return [TextContent(type="text", text="Error: UPO router timed out")]
            
        except Exception as e:
            emit_event(
                event_type="UPO_ROUTE_END",
                skill="upo-router",
                execution_id=execution_id,
                status="failed",
                error=str(e),
                duration_ms=self._calc_duration(start_time)
            )
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _get_skill(self, skill_name: str) -> List[TextContent]:
        """Retrieve a skill and emit observability events."""
        
        execution_id = str(uuid.uuid4())[:8]
        start_time = datetime.now(timezone.utc)
        
        # Emit start event
        emit_event(
            event_type="SKILL_START",
            skill=skill_name,
            execution_id=execution_id,
            status="running",
            context={
                "source": "mcp-local-skills-observable",
                "request_type": "get_skill"
            }
        )
        
        try:
            # Look for skill file
            skill_path = self._find_skill_path(skill_name)
            
            if not skill_path:
                # Emit error event
                emit_event(
                    event_type="SKILL_END",
                    skill=skill_name,
                    execution_id=execution_id,
                    status="failed",
                    error=f"Skill '{skill_name}' not found",
                    duration_ms=self._calc_duration(start_time)
                )
                return [TextContent(type="text", text=f"Error: Skill '{skill_name}' not found")]
            
            # Read skill content (UTF-8 for cross-platform compatibility)
            content = skill_path.read_text(encoding="utf-8")
            content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
            
            # Emit success event with metrics
            emit_event(
                event_type="SKILL_END",
                skill=skill_name,
                execution_id=execution_id,
                status="success",
                duration_ms=self._calc_duration(start_time),
                tokens={
                    "input_tokens": len(skill_name.split()),
                    "output_tokens": len(content.split()),
                    "total_tokens": len(content.split())
                },
                context={
                    "skill_path": str(skill_path),
                    "content_hash": content_hash,
                    "content_length": len(content)
                }
            )
            
            return [TextContent(type="text", text=content)]
            
        except Exception as e:
            # Emit error event
            emit_event(
                event_type="SKILL_ERROR",
                skill=skill_name,
                execution_id=execution_id,
                status="failed",
                error=str(e),
                duration_ms=self._calc_duration(start_time)
            )
            return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def _list_skills(self) -> List[TextContent]:
        """List all available skills."""
        
        emit_event(
            event_type="SKILL_START",
            skill="list_skills",
            status="running",
            context={"source": "mcp-local-skills-observable"}
        )
        
        skills = []
        
        if self.skills_dir.exists():
            for item in self.skills_dir.iterdir():
                if item.is_dir():
                    skill_file = item / "SKILL.md"
                    if skill_file.exists():
                        skills.append(item.name)
        
        emit_event(
            event_type="SKILL_END",
            skill="list_skills",
            status="success",
            context={"skills_found": len(skills)}
        )
        
        result = "\n".join([f"- {s}" for s in sorted(skills)])
        return [TextContent(type="text", text=f"Available skills ({len(skills)}):\n{result}")]
    
    def _find_skill_path(self, skill_name: str) -> Optional[Path]:
        """Find the skill file path."""
        # Try direct path
        skill_dir = self.skills_dir / skill_name
        if skill_dir.exists():
            skill_file = skill_dir / "SKILL.md"
            if skill_file.exists():
                return skill_file
        
        # Try with variations
        variations = [
            skill_name,
            skill_name.replace("-", "_"),
            skill_name.replace("_", "-"),
            skill_name.lower(),
        ]
        
        for var in variations:
            skill_dir = self.skills_dir / var
            if skill_dir.exists():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    return skill_file
        
        return None
    
    def _calc_duration(self, start_time: datetime) -> int:
        """Calculate duration in milliseconds."""
        return int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
    
    async def run(self):
        """Run the MCP server."""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


# ========== Standalone helper functions for testing ==========

def list_all_skills(skills_dir: str) -> List[Dict[str, Any]]:
    """List all skills in directory (for testing without MCP)."""
    skills_path = Path(skills_dir).expanduser()
    skills = []
    
    if skills_path.exists():
        for item in skills_path.iterdir():
            if item.is_dir():
                skill_file = item / "SKILL.md"
                if skill_file.exists():
                    skills.append({
                        "name": item.name,
                        "path": str(skill_file)
                    })
    
    return sorted(skills, key=lambda x: x["name"])


def get_skill(skill_name: str, skills_dir: str) -> str:
    """Get a skill by name (for testing without MCP)."""
    skills_path = Path(skills_dir).expanduser()
    execution_id = str(uuid.uuid4())[:8]
    start_time = datetime.now(timezone.utc)
    
    # Emit start event
    emit_event(
        event_type="SKILL_START",
        skill=skill_name,
        execution_id=execution_id,
        status="running",
        context={"source": "standalone-test"}
    )
    
    # Look for skill
    skill_dir = skills_path / skill_name
    skill_file = skill_dir / "SKILL.md"
    
    if skill_file.exists():
        content = skill_file.read_text(encoding="utf-8")
        duration = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        emit_event(
            event_type="SKILL_END",
            skill=skill_name,
            execution_id=execution_id,
            status="success",
            duration_ms=duration,
            tokens={"output_tokens": len(content.split()), "total_tokens": len(content.split())}
        )
        
        return content
    else:
        emit_event(
            event_type="SKILL_END",
            skill=skill_name,
            execution_id=execution_id,
            status="failed",
            error=f"Skill '{skill_name}' not found"
        )
        raise FileNotFoundError(f"Skill '{skill_name}' not found")


def main():
    """Main entry point."""
    if not MCP_AVAILABLE:
        # When MCP is not available, fail immediately with clear error
        # Do NOT run test mode as it outputs to stdout, breaking JSON-RPC protocol
        error_msg = (
            "ERROR: MCP package not installed.\n"
            "Install it with: pip install mcp\n"
            "Or install from local requirements: pip install -r mcp-servers/local-skills-observable/requirements.txt"
        )
        print(error_msg, file=sys.stderr)
        sys.exit(1)
    
    skills_dir = os.environ.get("SKILLS_DIR")
    server = SkillsServer(skills_dir)
    
    # Emit startup event
    emit_event(
        event_type="SKILL_START",
        skill="mcp-server-startup",
        status="success",
        context={
            "server": "local-skills-observable",
            "skills_dir": str(server.skills_dir)
        }
    )
    
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

