#!/usr/bin/env python3
"""
Terraform MCP Server - COMPREHENSIVE Edition

A full-featured MCP server for ALL Terraform operations.
Executes Terraform CLI commands directly - no Docker required.

Environment Variables:
- TERRAFORM_WORKING_DIR: Default working directory for Terraform commands

Tools (30+ commands):
  Core Workflow:
    - version, init, validate, fmt, plan, apply, destroy

  State Management:
    - state_list, state_show, state_mv, state_rm, state_pull, state_push
    - state_replace_provider, force_unlock

  Inspection:
    - show, graph, output, console, providers, providers_schema
    - metadata_functions

  Workspace:
    - workspace_list, workspace_select, workspace_new, workspace_delete
    - workspace_show

  Resource Control:
    - taint, untaint, refresh, import

  Module Management:
    - get, providers_lock, providers_mirror
"""

from __future__ import annotations

import json
import sys
import os
import subprocess
from pathlib import Path
from typing import Any, Optional, Dict, List

# Default working directory
DEFAULT_WORKING_DIR = os.getcwd()


def _get_working_dir(working_dir: Optional[str] = None) -> str:
    """Get the working directory for Terraform commands."""
    if working_dir:
        path = Path(working_dir).expanduser().resolve()
        if path.exists():
            return str(path)
        return working_dir
    return os.environ.get("TERRAFORM_WORKING_DIR", DEFAULT_WORKING_DIR)


def _run_terraform(
    args: List[str],
    working_dir: Optional[str] = None,
    input_text: Optional[str] = None,
    timeout: int = 300
) -> Dict[str, Any]:
    """Run a Terraform command and return the result."""
    cwd = _get_working_dir(working_dir)

    # Check if terraform is available
    try:
        subprocess.run(["terraform", "version"], capture_output=True, timeout=10, check=True)
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Terraform CLI not found. Please install Terraform: https://developer.hashicorp.com/terraform/install"
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Terraform version check timed out"}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"Terraform error: {e.stderr.decode() if e.stderr else str(e)}"}

    cmd = ["terraform"] + args

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            input=input_text,
            timeout=timeout
        )

        output = result.stdout
        error = result.stderr

        # Some terraform commands output to stderr even on success (like init)
        if result.returncode == 0:
            return {
                "success": True,
                "output": output or error,
                "working_dir": cwd,
                "command": " ".join(cmd)
            }
        else:
            return {
                "success": False,
                "error": error or output,
                "working_dir": cwd,
                "command": " ".join(cmd),
                "exit_code": result.returncode
            }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds",
            "command": " ".join(cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "command": " ".join(cmd)
        }


def _run_terraform_json(
    args: List[str],
    working_dir: Optional[str] = None,
    timeout: int = 300
) -> Dict[str, Any]:
    """Run a Terraform command with -json output."""
    result = _run_terraform(args + ["-json"], working_dir, timeout=timeout)

    if result.get("success") and result.get("output"):
        try:
            # Parse JSON output (may be multiple JSON objects, one per line)
            output = result["output"].strip()
            if output:
                lines = output.split("\n")
                parsed = []
                for line in lines:
                    if line.strip():
                        try:
                            parsed.append(json.loads(line))
                        except json.JSONDecodeError:
                            parsed.append({"raw": line})
                result["parsed"] = parsed if len(parsed) > 1 else (parsed[0] if parsed else None)
        except Exception:
            pass

    return result


# ============================================================================
# CORE TERRAFORM TOOLS
# ============================================================================

def terraform_version() -> Dict[str, Any]:
    """Show Terraform version information."""
    result = _run_terraform(["version"])

    if result.get("success"):
        output = result.get("output", "")
        lines = output.strip().split("\n")
        version_info = {
            "terraform_version": lines[0] if lines else "unknown",
            "providers": []
        }

        for line in lines[1:]:
            if line.strip().startswith("+"):
                version_info["providers"].append(line.strip())

        result["version_info"] = version_info

    return result


def terraform_init(
    working_dir: Optional[str] = None,
    upgrade: bool = False,
    reconfigure: bool = False,
    migrate_state: bool = False,
    backend_config: Optional[Dict[str, str]] = None,
    plugin_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Initialize Terraform working directory."""
    args = ["init", "-input=false"]

    if upgrade:
        args.append("-upgrade")
    if reconfigure:
        args.append("-reconfigure")
    if migrate_state:
        args.append("-migrate-state")
    if backend_config:
        for key, value in backend_config.items():
            args.append(f"-backend-config={key}={value}")
    if plugin_dir:
        args.append(f"-plugin-dir={plugin_dir}")

    return _run_terraform(args, working_dir, timeout=600)


def terraform_validate(working_dir: Optional[str] = None) -> Dict[str, Any]:
    """Validate Terraform configuration."""
    return _run_terraform_json(["validate"], working_dir)


def terraform_fmt(
    working_dir: Optional[str] = None,
    check: bool = False,
    recursive: bool = True,
    diff: bool = False,
    write: bool = True
) -> Dict[str, Any]:
    """Format Terraform configuration files."""
    args = ["fmt"]

    if check:
        args.append("-check")
    if recursive:
        args.append("-recursive")
    if diff:
        args.append("-diff")
    if not write:
        args.append("-write=false")

    return _run_terraform(args, working_dir)


def terraform_plan(
    working_dir: Optional[str] = None,
    out: Optional[str] = None,
    target: Optional[List[str]] = None,
    var: Optional[Dict[str, str]] = None,
    var_file: Optional[str] = None,
    destroy: bool = False,
    refresh_only: bool = False,
    replace: Optional[List[str]] = None,
    refresh: bool = True,
    parallelism: Optional[int] = None
) -> Dict[str, Any]:
    """Generate Terraform execution plan."""
    args = ["plan", "-input=false"]

    if out:
        args.append(f"-out={out}")
    if target:
        for t in target:
            args.append(f"-target={t}")
    if var:
        for key, value in var.items():
            args.append(f"-var={key}={value}")
    if var_file:
        args.append(f"-var-file={var_file}")
    if destroy:
        args.append("-destroy")
    if refresh_only:
        args.append("-refresh-only")
    if replace:
        for r in replace:
            args.append(f"-replace={r}")
    if not refresh:
        args.append("-refresh=false")
    if parallelism:
        args.append(f"-parallelism={parallelism}")

    return _run_terraform(args, working_dir, timeout=600)


def terraform_apply(
    working_dir: Optional[str] = None,
    plan_file: Optional[str] = None,
    target: Optional[List[str]] = None,
    var: Optional[Dict[str, str]] = None,
    var_file: Optional[str] = None,
    auto_approve: bool = False,
    refresh_only: bool = False,
    replace: Optional[List[str]] = None,
    parallelism: Optional[int] = None
) -> Dict[str, Any]:
    """Apply Terraform changes. REQUIRES auto_approve=true."""
    args = ["apply", "-input=false"]

    if auto_approve:
        args.append("-auto-approve")
    else:
        return {
            "success": False,
            "error": "auto_approve must be True to apply changes. This is a safety measure.",
            "hint": "Review the plan first with terraform_plan, then set auto_approve=True"
        }

    if plan_file:
        args.append(plan_file)
    else:
        if target:
            for t in target:
                args.append(f"-target={t}")
        if var:
            for key, value in var.items():
                args.append(f"-var={key}={value}")
        if var_file:
            args.append(f"-var-file={var_file}")
        if refresh_only:
            args.append("-refresh-only")
        if replace:
            for r in replace:
                args.append(f"-replace={r}")
        if parallelism:
            args.append(f"-parallelism={parallelism}")

    return _run_terraform(args, working_dir, timeout=1800)


def terraform_destroy(
    working_dir: Optional[str] = None,
    target: Optional[List[str]] = None,
    var: Optional[Dict[str, str]] = None,
    var_file: Optional[str] = None,
    auto_approve: bool = False,
    parallelism: Optional[int] = None
) -> Dict[str, Any]:
    """Destroy infrastructure. EXTREMELY DANGEROUS - requires auto_approve=true."""
    if not auto_approve:
        return {
            "success": False,
            "error": "auto_approve must be True to destroy. Critical safety measure.",
            "warning": "DANGER: terraform destroy will permanently delete infrastructure!"
        }

    args = ["destroy", "-input=false", "-auto-approve"]

    if target:
        for t in target:
            args.append(f"-target={t}")
    if var:
        for key, value in var.items():
            args.append(f"-var={key}={value}")
    if var_file:
        args.append(f"-var-file={var_file}")
    if parallelism:
        args.append(f"-parallelism={parallelism}")

    return _run_terraform(args, working_dir, timeout=1800)


# ============================================================================
# INSPECTION TOOLS
# ============================================================================

def terraform_show(
    working_dir: Optional[str] = None,
    plan_file: Optional[str] = None,
    json_output: bool = True
) -> Dict[str, Any]:
    """Show current state or a saved plan file in detail."""
    args = ["show"]

    if json_output:
        args.append("-json")

    if plan_file:
        args.append(plan_file)

    result = _run_terraform(args, working_dir)

    if result.get("success") and json_output and result.get("output"):
        try:
            result["state"] = json.loads(result["output"])
        except json.JSONDecodeError:
            pass

    return result


def terraform_graph(
    working_dir: Optional[str] = None,
    plan_file: Optional[str] = None,
    draw_cycles: bool = False,
    type_graph: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a visual graph of Terraform resources (DOT format)."""
    args = ["graph"]

    if plan_file:
        args.append(f"-plan={plan_file}")
    if draw_cycles:
        args.append("-draw-cycles")
    if type_graph:
        args.append(f"-type={type_graph}")

    return _run_terraform(args, working_dir)


def terraform_output(
    working_dir: Optional[str] = None,
    name: Optional[str] = None,
    raw: bool = False
) -> Dict[str, Any]:
    """Show Terraform outputs from state."""
    args = ["output"]

    if raw:
        args.append("-raw")
    else:
        args.append("-json")

    if name:
        args.append(name)

    result = _run_terraform(args, working_dir)

    if result.get("success") and not raw and result.get("output"):
        try:
            result["outputs"] = json.loads(result["output"])
        except json.JSONDecodeError:
            pass

    return result


def terraform_console(
    expression: str,
    working_dir: Optional[str] = None,
    var: Optional[Dict[str, str]] = None,
    var_file: Optional[str] = None
) -> Dict[str, Any]:
    """Evaluate a Terraform expression (non-interactive)."""
    args = ["console"]

    if var:
        for key, value in var.items():
            args.append(f"-var={key}={value}")
    if var_file:
        args.append(f"-var-file={var_file}")

    return _run_terraform(args, working_dir, input_text=expression + "\n")


def terraform_providers(working_dir: Optional[str] = None) -> Dict[str, Any]:
    """List providers used in configuration."""
    return _run_terraform(["providers"], working_dir)


def terraform_providers_schema(
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Output schemas for all providers (JSON). Very useful for understanding resource attributes."""
    result = _run_terraform(["providers", "schema", "-json"], working_dir, timeout=120)

    if result.get("success") and result.get("output"):
        try:
            result["schema"] = json.loads(result["output"])
        except json.JSONDecodeError:
            pass

    return result


def terraform_metadata_functions(working_dir: Optional[str] = None) -> Dict[str, Any]:
    """List available Terraform functions with descriptions."""
    result = _run_terraform(["metadata", "functions", "-json"], working_dir)

    if result.get("success") and result.get("output"):
        try:
            result["functions"] = json.loads(result["output"])
        except json.JSONDecodeError:
            pass

    return result


# ============================================================================
# STATE MANAGEMENT TOOLS
# ============================================================================

def terraform_state_list(
    working_dir: Optional[str] = None,
    address: Optional[str] = None,
    state_file: Optional[str] = None
) -> Dict[str, Any]:
    """List resources in Terraform state."""
    args = ["state", "list"]

    if state_file:
        args.extend(["-state", state_file])
    if address:
        args.append(address)

    result = _run_terraform(args, working_dir)

    if result.get("success") and result.get("output"):
        resources = [r.strip() for r in result["output"].strip().split("\n") if r.strip()]
        result["resources"] = resources
        result["count"] = len(resources)

    return result


def terraform_state_show(
    address: str,
    working_dir: Optional[str] = None,
    state_file: Optional[str] = None
) -> Dict[str, Any]:
    """Show attributes of a single resource in state."""
    args = ["state", "show"]

    if state_file:
        args.extend(["-state", state_file])
    args.append(address)

    return _run_terraform(args, working_dir)


def terraform_state_mv(
    source: str,
    destination: str,
    working_dir: Optional[str] = None,
    state_file: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Move a resource in state (rename or move to module)."""
    args = ["state", "mv"]

    if state_file:
        args.extend(["-state", state_file])
    if dry_run:
        args.append("-dry-run")

    args.extend([source, destination])

    return _run_terraform(args, working_dir)


def terraform_state_rm(
    addresses: List[str],
    working_dir: Optional[str] = None,
    state_file: Optional[str] = None,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Remove resources from state (does NOT destroy infrastructure)."""
    args = ["state", "rm"]

    if state_file:
        args.extend(["-state", state_file])
    if dry_run:
        args.append("-dry-run")

    args.extend(addresses)

    return _run_terraform(args, working_dir)


def terraform_state_pull(working_dir: Optional[str] = None) -> Dict[str, Any]:
    """Pull current state and output to stdout (for backup or inspection)."""
    result = _run_terraform(["state", "pull"], working_dir)

    if result.get("success") and result.get("output"):
        try:
            result["state"] = json.loads(result["output"])
        except json.JSONDecodeError:
            pass

    return result


def terraform_state_push(
    state_file: str,
    working_dir: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """Push a local state file to remote backend. DANGEROUS."""
    if not force:
        return {
            "success": False,
            "error": "force must be True to push state. This overwrites remote state!",
            "warning": "DANGER: This will overwrite the remote state file!"
        }

    args = ["state", "push"]
    if force:
        args.append("-force")
    args.append(state_file)

    return _run_terraform(args, working_dir)


def terraform_state_replace_provider(
    from_provider: str,
    to_provider: str,
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Replace provider in state (useful for provider migrations)."""
    args = ["state", "replace-provider", "-auto-approve", from_provider, to_provider]
    return _run_terraform(args, working_dir)


def terraform_force_unlock(
    lock_id: str,
    working_dir: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """Manually unlock state if lock is stuck."""
    if not force:
        return {
            "success": False,
            "error": "force must be True to unlock. Only use if you're sure no one is running Terraform."
        }

    args = ["force-unlock", "-force", lock_id]
    return _run_terraform(args, working_dir)


# ============================================================================
# WORKSPACE TOOLS
# ============================================================================

def terraform_workspace_list(working_dir: Optional[str] = None) -> Dict[str, Any]:
    """List Terraform workspaces."""
    result = _run_terraform(["workspace", "list"], working_dir)

    if result.get("success") and result.get("output"):
        workspaces = []
        current = None
        for line in result["output"].strip().split("\n"):
            ws = line.strip()
            if ws.startswith("*"):
                ws = ws[1:].strip()
                current = ws
            if ws:
                workspaces.append(ws)
        result["workspaces"] = workspaces
        result["current"] = current

    return result


def terraform_workspace_show(working_dir: Optional[str] = None) -> Dict[str, Any]:
    """Show current workspace name."""
    result = _run_terraform(["workspace", "show"], working_dir)

    if result.get("success") and result.get("output"):
        result["workspace"] = result["output"].strip()

    return result


def terraform_workspace_select(
    name: str,
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Select a Terraform workspace."""
    return _run_terraform(["workspace", "select", name], working_dir)


def terraform_workspace_new(
    name: str,
    working_dir: Optional[str] = None,
    state_file: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new Terraform workspace."""
    args = ["workspace", "new"]

    if state_file:
        args.extend(["-state", state_file])
    args.append(name)

    return _run_terraform(args, working_dir)


def terraform_workspace_delete(
    name: str,
    working_dir: Optional[str] = None,
    force: bool = False
) -> Dict[str, Any]:
    """Delete a Terraform workspace."""
    args = ["workspace", "delete"]

    if force:
        args.append("-force")
    args.append(name)

    return _run_terraform(args, working_dir)


# ============================================================================
# RESOURCE CONTROL TOOLS
# ============================================================================

def terraform_taint(
    address: str,
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Mark resource for recreation on next apply (deprecated, use -replace in plan/apply instead)."""
    return _run_terraform(["taint", address], working_dir)


def terraform_untaint(
    address: str,
    working_dir: Optional[str] = None
) -> Dict[str, Any]:
    """Remove taint from resource."""
    return _run_terraform(["untaint", address], working_dir)


def terraform_refresh(
    working_dir: Optional[str] = None,
    target: Optional[List[str]] = None,
    var: Optional[Dict[str, str]] = None,
    var_file: Optional[str] = None
) -> Dict[str, Any]:
    """Refresh state to match real infrastructure."""
    args = ["refresh", "-input=false"]

    if target:
        for t in target:
            args.append(f"-target={t}")
    if var:
        for key, value in var.items():
            args.append(f"-var={key}={value}")
    if var_file:
        args.append(f"-var-file={var_file}")

    return _run_terraform(args, working_dir, timeout=600)


def terraform_import(
    address: str,
    resource_id: str,
    working_dir: Optional[str] = None,
    var: Optional[Dict[str, str]] = None,
    var_file: Optional[str] = None
) -> Dict[str, Any]:
    """Import existing infrastructure into Terraform state."""
    args = ["import", "-input=false"]

    if var:
        for key, value in var.items():
            args.append(f"-var={key}={value}")
    if var_file:
        args.append(f"-var-file={var_file}")

    args.extend([address, resource_id])

    return _run_terraform(args, working_dir, timeout=300)


# ============================================================================
# MODULE MANAGEMENT TOOLS
# ============================================================================

def terraform_get(
    working_dir: Optional[str] = None,
    update: bool = False
) -> Dict[str, Any]:
    """Download and update modules."""
    args = ["get"]

    if update:
        args.append("-update")

    return _run_terraform(args, working_dir, timeout=300)


def terraform_providers_lock(
    working_dir: Optional[str] = None,
    platform: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create or update dependency lock file."""
    args = ["providers", "lock"]

    if platform:
        for p in platform:
            args.extend(["-platform", p])

    return _run_terraform(args, working_dir, timeout=300)


def terraform_providers_mirror(
    target_dir: str,
    working_dir: Optional[str] = None,
    platform: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Mirror providers to a local directory for offline use."""
    args = ["providers", "mirror"]

    if platform:
        for p in platform:
            args.extend(["-platform", p])

    args.append(target_dir)

    return _run_terraform(args, working_dir, timeout=600)


# ============================================================================
# MCP PROTOCOL IMPLEMENTATION
# ============================================================================

TOOLS = [
    # Core Workflow
    {
        "name": "version",
        "description": "Show Terraform version and provider information.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "init",
        "description": "Initialize Terraform working directory. Downloads providers and modules.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "upgrade": {"type": "boolean", "description": "Upgrade modules and plugins"},
                "reconfigure": {"type": "boolean", "description": "Reconfigure backend"},
                "migrate_state": {"type": "boolean", "description": "Migrate state to new backend"},
                "backend_config": {"type": "object", "description": "Backend configuration key-value pairs"},
                "plugin_dir": {"type": "string", "description": "Directory for plugin binaries"}
            }
        }
    },
    {
        "name": "validate",
        "description": "Validate Terraform configuration syntax and consistency.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            }
        }
    },
    {
        "name": "fmt",
        "description": "Format Terraform configuration files to canonical style.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "check": {"type": "boolean", "description": "Check only, don't modify"},
                "recursive": {"type": "boolean", "description": "Process subdirectories"},
                "diff": {"type": "boolean", "description": "Show differences"},
                "write": {"type": "boolean", "description": "Write changes to files", "default": True}
            }
        }
    },
    {
        "name": "plan",
        "description": "Generate execution plan showing what will be created/changed/destroyed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "out": {"type": "string", "description": "Save plan to file"},
                "target": {"type": "array", "items": {"type": "string"}, "description": "Target specific resources"},
                "var": {"type": "object", "description": "Variable values"},
                "var_file": {"type": "string", "description": "Variable file path"},
                "destroy": {"type": "boolean", "description": "Create destroy plan"},
                "refresh_only": {"type": "boolean", "description": "Only refresh state"},
                "replace": {"type": "array", "items": {"type": "string"}, "description": "Force replacement of resources"},
                "refresh": {"type": "boolean", "description": "Update state before planning", "default": True},
                "parallelism": {"type": "integer", "description": "Number of parallel operations"}
            }
        }
    },
    {
        "name": "apply",
        "description": "Apply Terraform changes. REQUIRES auto_approve=true for safety.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "plan_file": {"type": "string", "description": "Path to saved plan file"},
                "target": {"type": "array", "items": {"type": "string"}, "description": "Target specific resources"},
                "var": {"type": "object", "description": "Variable values"},
                "var_file": {"type": "string", "description": "Variable file path"},
                "auto_approve": {"type": "boolean", "description": "Skip approval (REQUIRED)"},
                "refresh_only": {"type": "boolean", "description": "Only refresh state"},
                "replace": {"type": "array", "items": {"type": "string"}, "description": "Force replacement of resources"},
                "parallelism": {"type": "integer", "description": "Number of parallel operations"}
            }
        }
    },
    {
        "name": "destroy",
        "description": "DESTROY infrastructure. EXTREMELY DANGEROUS - requires auto_approve=true.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "target": {"type": "array", "items": {"type": "string"}, "description": "Target specific resources"},
                "var": {"type": "object", "description": "Variable values"},
                "var_file": {"type": "string", "description": "Variable file path"},
                "auto_approve": {"type": "boolean", "description": "Skip approval (REQUIRED)"},
                "parallelism": {"type": "integer", "description": "Number of parallel operations"}
            }
        }
    },

    # Inspection Tools
    {
        "name": "show",
        "description": "Show current state or a saved plan file in full detail (JSON).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "plan_file": {"type": "string", "description": "Path to plan file to show"},
                "json_output": {"type": "boolean", "description": "Output as JSON", "default": True}
            }
        }
    },
    {
        "name": "graph",
        "description": "Generate dependency graph in DOT format for visualization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "plan_file": {"type": "string", "description": "Path to plan file"},
                "draw_cycles": {"type": "boolean", "description": "Highlight cycles"},
                "type_graph": {"type": "string", "description": "Type of graph (plan, plan-refresh-only, plan-destroy, apply)"}
            }
        }
    },
    {
        "name": "output",
        "description": "Show Terraform outputs from state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "name": {"type": "string", "description": "Specific output name"},
                "raw": {"type": "boolean", "description": "Output raw value without quotes"}
            }
        }
    },
    {
        "name": "console",
        "description": "Evaluate a Terraform expression. Useful for testing interpolations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Expression to evaluate"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "var": {"type": "object", "description": "Variable values"},
                "var_file": {"type": "string", "description": "Variable file path"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "providers",
        "description": "List providers required by configuration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            }
        }
    },
    {
        "name": "providers_schema",
        "description": "Output full provider schemas (JSON). Shows all resource types and their attributes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            }
        }
    },
    {
        "name": "metadata_functions",
        "description": "List all available Terraform functions with descriptions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            }
        }
    },

    # State Management
    {
        "name": "state_list",
        "description": "List all resources in Terraform state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "address": {"type": "string", "description": "Filter by address pattern"},
                "state_file": {"type": "string", "description": "Path to state file"}
            }
        }
    },
    {
        "name": "state_show",
        "description": "Show attributes of a specific resource in state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Resource address"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "state_file": {"type": "string", "description": "Path to state file"}
            },
            "required": ["address"]
        }
    },
    {
        "name": "state_mv",
        "description": "Move/rename a resource in state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "source": {"type": "string", "description": "Source address"},
                "destination": {"type": "string", "description": "Destination address"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "state_file": {"type": "string", "description": "Path to state file"},
                "dry_run": {"type": "boolean", "description": "Preview without making changes"}
            },
            "required": ["source", "destination"]
        }
    },
    {
        "name": "state_rm",
        "description": "Remove resources from state (does NOT destroy infrastructure).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "addresses": {"type": "array", "items": {"type": "string"}, "description": "Resource addresses to remove"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "state_file": {"type": "string", "description": "Path to state file"},
                "dry_run": {"type": "boolean", "description": "Preview without making changes"}
            },
            "required": ["addresses"]
        }
    },
    {
        "name": "state_pull",
        "description": "Pull and output current state (for backup or inspection).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            }
        }
    },
    {
        "name": "state_push",
        "description": "Push local state to remote backend. DANGEROUS - requires force=true.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "state_file": {"type": "string", "description": "Path to state file to push"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "force": {"type": "boolean", "description": "Force push (REQUIRED, overwrites remote)"}
            },
            "required": ["state_file"]
        }
    },
    {
        "name": "state_replace_provider",
        "description": "Replace provider in state (for provider migrations).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_provider": {"type": "string", "description": "Current provider address"},
                "to_provider": {"type": "string", "description": "New provider address"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            },
            "required": ["from_provider", "to_provider"]
        }
    },
    {
        "name": "force_unlock",
        "description": "Manually unlock state if lock is stuck.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lock_id": {"type": "string", "description": "Lock ID to release"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "force": {"type": "boolean", "description": "Force unlock (REQUIRED)"}
            },
            "required": ["lock_id"]
        }
    },

    # Workspace Management
    {
        "name": "workspace_list",
        "description": "List all workspaces.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            }
        }
    },
    {
        "name": "workspace_show",
        "description": "Show current workspace name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            }
        }
    },
    {
        "name": "workspace_select",
        "description": "Select/switch to a workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Workspace name"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "workspace_new",
        "description": "Create a new workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "New workspace name"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "state_file": {"type": "string", "description": "Copy state from this file"}
            },
            "required": ["name"]
        }
    },
    {
        "name": "workspace_delete",
        "description": "Delete a workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Workspace name to delete"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "force": {"type": "boolean", "description": "Force delete even if state is not empty"}
            },
            "required": ["name"]
        }
    },

    # Resource Control
    {
        "name": "taint",
        "description": "Mark resource for recreation (deprecated, prefer -replace in plan/apply).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Resource address to taint"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            },
            "required": ["address"]
        }
    },
    {
        "name": "untaint",
        "description": "Remove taint from resource.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Resource address to untaint"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"}
            },
            "required": ["address"]
        }
    },
    {
        "name": "refresh",
        "description": "Update state to match real infrastructure.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "target": {"type": "array", "items": {"type": "string"}, "description": "Target specific resources"},
                "var": {"type": "object", "description": "Variable values"},
                "var_file": {"type": "string", "description": "Variable file path"}
            }
        }
    },
    {
        "name": "import",
        "description": "Import existing infrastructure into Terraform state.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Terraform resource address"},
                "resource_id": {"type": "string", "description": "Cloud resource ID"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "var": {"type": "object", "description": "Variable values"},
                "var_file": {"type": "string", "description": "Variable file path"}
            },
            "required": ["address", "resource_id"]
        }
    },

    # Module Management
    {
        "name": "get",
        "description": "Download and update modules.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "update": {"type": "boolean", "description": "Update already-downloaded modules"}
            }
        }
    },
    {
        "name": "providers_lock",
        "description": "Create/update dependency lock file for providers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "platform": {"type": "array", "items": {"type": "string"}, "description": "Platforms to lock (e.g., linux_amd64, darwin_arm64)"}
            }
        }
    },
    {
        "name": "providers_mirror",
        "description": "Mirror providers to local directory for offline/air-gapped use.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_dir": {"type": "string", "description": "Directory to mirror providers to"},
                "working_dir": {"type": "string", "description": "Directory containing Terraform files"},
                "platform": {"type": "array", "items": {"type": "string"}, "description": "Platforms to mirror"}
            },
            "required": ["target_dir"]
        }
    }
]


def handle_request(request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Handle incoming MCP request."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "terraform", "version": "2.0.0"}
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": TOOLS}
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        tool_functions = {
            # Core
            "version": terraform_version,
            "init": terraform_init,
            "validate": terraform_validate,
            "fmt": terraform_fmt,
            "plan": terraform_plan,
            "apply": terraform_apply,
            "destroy": terraform_destroy,
            # Inspection
            "show": terraform_show,
            "graph": terraform_graph,
            "output": terraform_output,
            "console": terraform_console,
            "providers": terraform_providers,
            "providers_schema": terraform_providers_schema,
            "metadata_functions": terraform_metadata_functions,
            # State
            "state_list": terraform_state_list,
            "state_show": terraform_state_show,
            "state_mv": terraform_state_mv,
            "state_rm": terraform_state_rm,
            "state_pull": terraform_state_pull,
            "state_push": terraform_state_push,
            "state_replace_provider": terraform_state_replace_provider,
            "force_unlock": terraform_force_unlock,
            # Workspace
            "workspace_list": terraform_workspace_list,
            "workspace_show": terraform_workspace_show,
            "workspace_select": terraform_workspace_select,
            "workspace_new": terraform_workspace_new,
            "workspace_delete": terraform_workspace_delete,
            # Resource Control
            "taint": terraform_taint,
            "untaint": terraform_untaint,
            "refresh": terraform_refresh,
            "import": terraform_import,
            # Module Management
            "get": terraform_get,
            "providers_lock": terraform_providers_lock,
            "providers_mirror": terraform_providers_mirror
        }

        if tool_name in tool_functions:
            try:
                result = tool_functions[tool_name](**arguments)
            except TypeError as e:
                result = {"success": False, "error": f"Invalid arguments: {e}"}
            except Exception as e:
                result = {"success": False, "error": str(e)}
        else:
            result = {"success": False, "error": f"Unknown tool: {tool_name}"}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            }
        }

    elif method == "notifications/initialized":
        return None

    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }


def main():
    """Main MCP server loop using stdio."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            response = handle_request(request)

            if response:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()

        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
