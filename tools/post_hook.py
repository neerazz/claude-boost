#!/usr/bin/env python3
"""
Unified Post-Hook Orchestrator
==============================

SINGLE ENTRY POINT for ALL sync operations.

This script consolidates all post-hook checks, sync operations, and validations
into ONE self-contained tool. Run this after ANY code change.

⛔ SESSION LOCK ENFORCEMENT (TWO-LEVEL VALIDATION)
================================================
Level 1: Documentation (AGENTS.md, .cursorrules, CLAUDE.md) tells AI to run this
Level 2: This script validates and BLOCKS if session lock is incomplete

Usage:
    python tools/post_hook.py              # Auto-detect changes and sync + mark lock COMPLETE
    python tools/post_hook.py --check      # Deterministic check only (CI/CD)
    python tools/post_hook.py --force      # Force full sync regardless of changes
    python tools/post_hook.py --only hooks # Sync only specific domain(s)
    python tools/post_hook.py --status     # Show sync status + lock status
    python tools/post_hook.py --clear-lock --force  # Emergency clear lock (USE WITH CAUTION)
    python tools/post_hook.py --verbose    # Show detailed output

What it checks:
    - skills/      → dag_manager.py, skills/scripts/sync.py
    - commands/    → commands/scripts/sync.py
    - hooks/       → hooks/sync.py
    - mcp-servers/ → mcp_sync.py (if exists)

Exit Codes:
    0 = All synced, no action needed (or sync successful)
    1 = Sync required but not run (--check mode)
    2 = Sync failed
    3 = Session lock validation failed (BLOCKED)

AGENTS.md Compliance:
    This is the ONLY script AI agents need to run after code changes.
    Replaces individual calls to dag_manager.py, command_sync, etc.
    
⛔ MANDATORY: Run at END of EVERY AI session to mark lock COMPLETE.
"""

import io
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

import argparse
import hashlib
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# Configuration
# ============================================================================

REPO_ROOT = Path(__file__).parent.parent
CACHE_DIR = REPO_ROOT / "data" / "cache"
UNIFIED_CACHE_PATH = CACHE_DIR / "unified_post_hook.json"
SESSION_LOCK_PATH = CACHE_DIR / "session_lock.json"

# Tracked directories and their handlers
# Each domain has a SELF-CONTAINED sync script that travels WITH the domain
SYNC_HANDLERS = {
    "skills": {
        "source_dir": REPO_ROOT / "skills",
        "self_contained_script": REPO_ROOT / "skills" / "scripts" / "sync.py",
        "skill_dag_sync": REPO_ROOT / "skills" / "skill-architect" / "scripts" / "dag_manager.py",
        "skill_validator": REPO_ROOT / "skills" / "skill-architect" / "scripts" / "skill_best_practices_validator.py",
        "skill_auto_fixer": REPO_ROOT / "skills" / "skill-architect" / "scripts" / "skill_auto_fixer.py",
        "fallback_scripts": [
            ("skill_converter.py", "full-sync"),
        ],
        "description": "Agent Skills",
    },
    "commands": {
        "source_dir": REPO_ROOT / "commands",
        "self_contained_script": REPO_ROOT / "commands" / "scripts" / "sync.py",
        "fallback_scripts": [
            ("command_sync.py", "post-hook"),
        ],
        "description": "Slash Commands",
    },
    "hooks": {
        "source_dir": REPO_ROOT / "hooks",
        "self_contained_script": REPO_ROOT / "hooks" / "sync.py",
        "fallback_scripts": [],
        "description": "AI Tool Hooks",
    },
    "mcp-servers": {
        "source_dir": REPO_ROOT / "mcp-servers",
        "self_contained_script": None,  # No self-contained script yet
        "fallback_scripts": [
            ("mcp_sync.py", "sync-all"),
        ],
        "description": "MCP Server Config",
        "optional": True,
    },
}

# Skip patterns for hash computation
# These are generated files that change during sync - excluding them prevents infinite sync loops
SKIP_PATTERNS = {
    "__pycache__",
    ".git",
    ".DS_Store",
    "node_modules",
    ".pyc",
    ".cache",  # Exclude cache directories created by self-contained scripts
    "sync_state.json",  # Exclude sync state files
    "keyword_mappings.json",  # Exclude generated keyword mappings
    "keyword_skill_mapping.json",  # Exclude generated DAG mapping
    "skill_dag.json",  # Exclude generated DAG file (in skills/universal-prompt-orchestrator/data/dag/)
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DirectoryState:
    """State of a tracked directory."""
    name: str
    hash: str
    file_count: int
    last_modified: str


@dataclass
class SyncResult:
    """Result of a sync operation."""
    handler: str
    script: str
    action: str
    success: bool
    message: str
    duration_seconds: float = 0.0


@dataclass
class PostHookReport:
    """Complete post-hook execution report."""
    timestamp: str
    mode: str  # "check", "sync", "force"
    changes_detected: Dict[str, bool]
    sync_results: List[SyncResult]
    all_synced: bool
    total_duration: float


# ============================================================================
# Hash Computation
# ============================================================================

def should_skip_path(path: Path) -> bool:
    """Check if path should be skipped for hashing."""
    for part in path.parts:
        if part in SKIP_PATTERNS:
            return True
        if part.endswith('.pyc'):
            return True
    return False


def compute_directory_hash(directory: Path) -> Tuple[str, int]:
    """Compute combined hash of all files in directory."""
    if not directory.exists():
        return "", 0
    
    hasher = hashlib.sha256()
    file_count = 0
    
    for file_path in sorted(directory.rglob("*")):
        if file_path.is_file() and not should_skip_path(file_path):
            try:
                rel_path = file_path.relative_to(directory)
                hasher.update(str(rel_path).encode('utf-8'))
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                file_count += 1
            except (IOError, OSError):
                continue
    
    return hasher.hexdigest(), file_count


# ============================================================================
# Cache Management
# ============================================================================

def load_cache() -> Dict[str, Any]:
    """Load unified post-hook cache."""
    if not UNIFIED_CACHE_PATH.exists():
        return {"directories": {}, "last_run": ""}
    
    try:
        with open(UNIFIED_CACHE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"directories": {}, "last_run": ""}


def save_cache(cache: Dict[str, Any]) -> None:
    """Save unified post-hook cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(UNIFIED_CACHE_PATH, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)


def save_report(report: PostHookReport) -> None:
    """Save post-hook execution report."""
    report_path = CACHE_DIR / "post_hook_report.json"
    
    # Load existing reports
    reports = []
    if report_path.exists():
        try:
            with open(report_path, 'r', encoding='utf-8') as f:
                reports = json.load(f)
        except (json.JSONDecodeError, IOError):
            reports = []
    
    # Add new report (keep last 50)
    report_dict = {
        "timestamp": report.timestamp,
        "mode": report.mode,
        "changes_detected": report.changes_detected,
        "sync_results": [
            {
                "handler": r.handler,
                "script": r.script,
                "action": r.action,
                "success": r.success,
                "message": r.message,
                "duration_seconds": r.duration_seconds,
            }
            for r in report.sync_results
        ],
        "all_synced": report.all_synced,
        "total_duration": report.total_duration,
    }
    reports.append(report_dict)
    reports = reports[-50:]
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(reports, f, indent=2)


# ============================================================================
# Session Lock Enforcement (Level 2 Validation)
# ============================================================================

@dataclass
class SessionLockStatus:
    """Status of the session lock."""
    exists: bool
    status: str  # "ACTIVE", "COMPLETE", "NONE"
    session_start: Optional[str] = None
    completed_at: Optional[str] = None
    blocked: bool = False
    message: str = ""


def get_session_lock_status() -> SessionLockStatus:
    """
    Get the current session lock status.
    
    This is Level 2 validation - code enforcement that cannot be ignored.
    """
    if not SESSION_LOCK_PATH.exists():
        return SessionLockStatus(
            exists=False,
            status="NONE",
            blocked=False,
            message="No session lock exists. Ready to proceed."
        )
    
    try:
        lock_data = json.loads(SESSION_LOCK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return SessionLockStatus(
            exists=True,
            status="CORRUPT",
            blocked=True,
            message="Session lock file is corrupt. Use --clear-lock --force to clear."
        )
    
    status = lock_data.get("status", "UNKNOWN")
    session_start = lock_data.get("session_start")
    completed_at = lock_data.get("completed_at")
    
    if status == "ACTIVE":
        # Check if this is a stale lock (session crashed)
        if session_start:
            try:
                start_time = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                age_hours = (datetime.now(timezone.utc) - start_time).total_seconds() / 3600
                if age_hours > 24:
                    return SessionLockStatus(
                        exists=True,
                        status="STALE",
                        session_start=session_start,
                        blocked=True,
                        message=f"⚠️ Stale session lock from {session_start} ({age_hours:.1f}h ago). "
                                f"Previous session may have crashed. Use --clear-lock --force if sure."
                    )
            except (ValueError, TypeError):
                pass
        
        return SessionLockStatus(
            exists=True,
            status="ACTIVE",
            session_start=session_start,
            blocked=True,
            message=f"⛔ BLOCKED: Previous session did not complete properly.\n"
                    f"   Session started: {session_start}\n"
                    f"   Run 'python3 tools/post_hook.py' to complete and unblock."
        )
    
    if status == "COMPLETE":
        return SessionLockStatus(
            exists=True,
            status="COMPLETE",
            session_start=session_start,
            completed_at=completed_at,
            blocked=False,
            message=f"✅ Previous session completed properly at {completed_at}"
        )
    
    return SessionLockStatus(
        exists=True,
        status=status,
        blocked=True,
        message=f"Unknown lock status: {status}. Use --clear-lock --force to clear."
    )


def create_session_lock() -> bool:
    """
    Create a new session lock with status ACTIVE.
    
    Called at the start of sync operations.
    """
    lock_data = {
        "session_start": datetime.now(timezone.utc).isoformat(),
        "pid": os.getpid(),
        "status": "ACTIVE",
        "post_hooks_required": ["post_hook.py"],
        "post_hooks_completed": [],
        "created_by": "post_hook.py"
    }
    
    try:
        SESSION_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        SESSION_LOCK_PATH.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
        return True
    except OSError:
        return False


def clear_session_lock(force: bool = False) -> Tuple[bool, str]:
    """
    Clear the session lock.
    
    Args:
        force: If True, clear even if lock is ACTIVE (emergency use only)
    
    Returns:
        Tuple of (success, message)
    """
    if not SESSION_LOCK_PATH.exists():
        return True, "No session lock to clear."
    
    lock_status = get_session_lock_status()
    
    if lock_status.status == "ACTIVE" and not force:
        return False, (
            "⛔ Cannot clear ACTIVE lock without --force flag.\n"
            "   This lock exists because a previous session did not complete.\n"
            "   If you're sure no session is running, use: --clear-lock --force"
        )
    
    try:
        SESSION_LOCK_PATH.unlink()
        return True, f"✅ Session lock cleared. Status was: {lock_status.status}"
    except OSError as e:
        return False, f"❌ Failed to clear lock: {e}"


def mark_session_hook_complete(hook_name: str) -> bool:
    """
    Mark a post-run hook as complete in the preflight gate session lock.

    This is required to unblock future `tools/preflight_gate.py` runs.
    """
    if not SESSION_LOCK_PATH.exists():
        # Create a new lock and immediately mark complete
        create_session_lock()
    
    try:
        lock_data = json.loads(SESSION_LOCK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return False

    completed = lock_data.setdefault("post_hooks_completed", [])
    if hook_name not in completed:
        completed.append(hook_name)

    required = set(lock_data.get("post_hooks_required", []))
    completed_set = set(lock_data.get("post_hooks_completed", []))

    if required and required <= completed_set:
        lock_data["status"] = "COMPLETE"
        lock_data["completed_at"] = datetime.now(timezone.utc).isoformat()

    try:
        SESSION_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
        SESSION_LOCK_PATH.write_text(json.dumps(lock_data, indent=2), encoding="utf-8")
    except OSError:
        return False

    return True


# ============================================================================
# Change Detection
# ============================================================================

def detect_changes() -> Dict[str, Tuple[bool, DirectoryState]]:
    """Detect which directories have changed since last sync."""
    cache = load_cache()
    cached_dirs = cache.get("directories", {})
    
    changes = {}
    
    for name, config in SYNC_HANDLERS.items():
        source_dir = config["source_dir"]
        
        if not source_dir.exists():
            if config.get("optional"):
                continue
            changes[name] = (True, DirectoryState(
                name=name, hash="", file_count=0,
                last_modified=datetime.now().isoformat()
            ))
            continue
        
        current_hash, file_count = compute_directory_hash(source_dir)
        cached_hash = cached_dirs.get(name, {}).get("hash", "")
        
        changed = current_hash != cached_hash
        
        state = DirectoryState(
            name=name,
            hash=current_hash,
            file_count=file_count,
            last_modified=datetime.now().isoformat()
        )
        
        changes[name] = (changed, state)
    
    return changes


# ============================================================================
# Sync Execution
# ============================================================================

def run_sync_script(handler_name: str, script_name: str, action: str) -> SyncResult:
    """Run a single sync script."""
    script_path = REPO_ROOT / "tools" / script_name
    
    if not script_path.exists():
        return SyncResult(
            handler=handler_name,
            script=script_name,
            action=action,
            success=False,
            message=f"Script not found: {script_path}"
        )
    
    start_time = datetime.now()
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), action],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=300,  # 5 minute timeout
            encoding='utf-8',
            errors='replace'
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            return SyncResult(
                handler=handler_name,
                script=script_name,
                action=action,
                success=True,
                message="Success",
                duration_seconds=duration
            )
        else:
            # Extract error message
            error_msg = result.stderr[:200] if result.stderr else result.stdout[:200]
            return SyncResult(
                handler=handler_name,
                script=script_name,
                action=action,
                success=False,
                message=f"Exit {result.returncode}: {error_msg}",
                duration_seconds=duration
            )
    
    except subprocess.TimeoutExpired:
        return SyncResult(
            handler=handler_name,
            script=script_name,
            action=action,
            success=False,
            message="Timeout after 5 minutes"
        )
    except Exception as e:
        return SyncResult(
            handler=handler_name,
            script=script_name,
            action=action,
            success=False,
            message=str(e)
        )


def run_handler_sync(handler_name: str, config: Dict) -> List[SyncResult]:
    """Run sync for a handler - prefers self-contained scripts."""
    results = []
    
    # For skills: Run dag_manager.py --sync FIRST (updates DAG + keyword mapping)
    dag_sync = config.get("skill_dag_sync")
    if dag_sync and dag_sync.exists():
        result = run_self_contained_script(handler_name, dag_sync, action="--sync")
        results.append(result)
        # Continue even if dag_sync has warnings
    
    # Try self-contained script (lives WITH the domain)
    self_contained = config.get("self_contained_script")
    if self_contained and self_contained.exists():
        result = run_self_contained_script(handler_name, self_contained)
        results.append(result)
        if result.success:
            return results  # Self-contained script handled everything
    
    # Fall back to tools/ scripts
    for script_name, action in config.get("fallback_scripts", []):
        result = run_sync_script(handler_name, script_name, action)
        results.append(result)
        
        # Stop if a script fails
        if not result.success:
            break
    
    return results


def run_self_contained_script(handler_name: str, script_path: Path, action: str = None) -> SyncResult:
    """Run a self-contained domain sync script."""
    start_time = datetime.now()
    
    try:
        cmd = [sys.executable, str(script_path)]
        if action:
            cmd.append(action)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=300,
            encoding='utf-8',
            errors='replace'
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if result.returncode == 0:
            return SyncResult(
                handler=handler_name,
                script=script_path.name,
                action=action or "sync",
                success=True,
                message=f"Success ({script_path.name})",
                duration_seconds=duration
            )
        else:
            error_msg = result.stderr[:200] if result.stderr else result.stdout[:200]
            return SyncResult(
                handler=handler_name,
                script=script_path.name,
                action=action or "sync",
                success=False,
                message=f"Exit {result.returncode}: {error_msg}",
                duration_seconds=duration
            )
    
    except subprocess.TimeoutExpired:
        return SyncResult(
            handler=handler_name,
            script=script_path.name,
            action="sync",
            success=False,
            message="Timeout after 5 minutes"
        )
    except Exception as e:
        return SyncResult(
            handler=handler_name,
            script=script_path.name,
            action="sync",
            success=False,
            message=str(e)
        )


# ============================================================================
# Main Operations
# ============================================================================

def check_sync_status(verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    DETERMINISTIC CHECK - Returns (all_synced, details).
    
    Use in CI/CD or pre-commit hooks.
    """
    changes = detect_changes()
    
    details = {
        "timestamp": datetime.now().isoformat(),
        "directories": {},
        "changes_needed": [],
    }
    
    all_synced = True
    
    for name, (changed, state) in changes.items():
        details["directories"][name] = {
            "hash": state.hash[:16] + "..." if state.hash else "none",
            "file_count": state.file_count,
            "changed": changed,
        }
        
        if changed:
            all_synced = False
            details["changes_needed"].append(name)
    
    return all_synced, details


def run_post_hook(force: bool = False, verbose: bool = False, only_domains: List[str] = None) -> PostHookReport:
    """
    Run post-hook sync for all changed directories.

    Args:
        force: If True, sync all directories regardless of changes.
        verbose: If True, show detailed output.
        only_domains: If provided, only sync these specific domains.
    """
    start_time = datetime.now()
    changes = detect_changes()

    sync_results = []
    changes_detected = {}

    # Filter to only specified domains if --only was used
    domains_to_process = only_domains if only_domains else list(changes.keys())

    for name in domains_to_process:
        if name not in changes:
            if verbose:
                print(f"⚠️  {name}: Unknown domain, skipping")
            continue

        changed, state = changes[name]
        changes_detected[name] = changed

        # Skip if no changes and not forced
        if not changed and not force:
            if verbose:
                print(f"⏭️  {name}: No changes (hash: {state.hash[:12]}...)")
            continue

        config = SYNC_HANDLERS[name]
        reason = "forced" if force and not changed else "changed"

        if verbose:
            print(f"🔄 {name}: Syncing ({reason}, {state.file_count} files)...")

        results = run_handler_sync(name, config)
        sync_results.extend(results)
    
    # Update cache with new hashes
    cache = load_cache()
    cache["directories"] = {}
    cache["last_run"] = datetime.now().isoformat()
    
    for name, (_, state) in changes.items():
        cache["directories"][name] = {
            "hash": state.hash,
            "file_count": state.file_count,
            "last_modified": state.last_modified,
        }
    
    save_cache(cache)
    
    # Build report
    all_synced = all(r.success for r in sync_results) if sync_results else True
    total_duration = (datetime.now() - start_time).total_seconds()
    
    report = PostHookReport(
        timestamp=datetime.now().isoformat(),
        mode="force" if force else "sync",
        changes_detected=changes_detected,
        sync_results=sync_results,
        all_synced=all_synced,
        total_duration=total_duration,
    )
    
    save_report(report)
    
    return report


# ============================================================================
# CLI Interface
# ============================================================================

def print_header():
    """Print CLI header."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║         Unified Post-Hook Orchestrator                       ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()


def cmd_check(args) -> int:
    """Deterministic check - returns non-zero if sync needed."""
    print_header()
    print("Mode: CHECK (deterministic)")
    print()
    
    all_synced, details = check_sync_status(args.verbose)
    
    print("📂 Tracked Directories:")
    for name, info in details["directories"].items():
        status = "✅" if not info["changed"] else "⚠️ "
        print(f"   {status} {name}: {info['file_count']} files (hash: {info['hash']})")
    
    print()
    
    if all_synced:
        print("✅ ALL SYNCED - No action needed")
        return 0
    else:
        print("❌ SYNC REQUIRED")
        print(f"   Changed: {', '.join(details['changes_needed'])}")
        print()
        print("━━━ Run this to sync ━━━")
        print("python tools/post_hook.py")
        return 1


def cmd_sync(args) -> int:
    """Run sync for changed directories."""
    print_header()

    # Parse --only flag if provided
    only_domains = None
    if hasattr(args, 'only') and args.only:
        only_domains = [d.strip() for d in args.only.split(',')]
        invalid = [d for d in only_domains if d not in SYNC_HANDLERS]
        if invalid:
            print(f"❌ Unknown domain(s): {', '.join(invalid)}")
            print(f"   Valid domains: {', '.join(SYNC_HANDLERS.keys())}")
            return 1

    mode_parts = []
    if args.force:
        mode_parts.append("FORCE")
    if only_domains:
        mode_parts.append(f"ONLY: {','.join(only_domains)}")
    mode_parts.append("SYNC")
    print(f"Mode: {' '.join(mode_parts)}")
    print()

    # First check what needs syncing
    all_synced, details = check_sync_status(args.verbose)

    # Filter changes_needed to only_domains if specified
    changes_needed = details.get("changes_needed", [])
    if only_domains:
        changes_needed = [d for d in changes_needed if d in only_domains]

    if not changes_needed and not args.force:
        if only_domains:
            print(f"✅ Specified domains already synced: {', '.join(only_domains)}")
        else:
            print("✅ All domains synced - No action needed")
        # IMPORTANT: Unblock preflight gate session lock even when no sync needed.
        mark_session_hook_complete("post_hook.py")
        return 0

    print("📂 Directories to sync:")
    domains_to_show = only_domains if only_domains else (changes_needed or list(SYNC_HANDLERS.keys()))
    for name in domains_to_show:
        config = SYNC_HANDLERS.get(name, {})
        changed_marker = "⚡" if name in changes_needed else "📦"
        print(f"   {changed_marker} {name}: {config.get('description', '')}")

    print()

    # Run sync
    report = run_post_hook(force=args.force, verbose=args.verbose, only_domains=only_domains)
    
    # Print results
    print("━━━ Sync Results ━━━")
    for result in report.sync_results:
        status = "✅" if result.success else "❌"
        print(f"   {status} {result.handler}/{result.script} {result.action}")
        if not result.success:
            print(f"      Error: {result.message[:100]}")
    
    print()
    print(f"⏱️  Total time: {report.total_duration:.1f}s")
    print(f"📄 Cache: {UNIFIED_CACHE_PATH}")
    print()
    
    if report.all_synced:
        print("✅ POST-HOOK COMPLETE - All synced")
        mark_session_hook_complete("post_hook.py")
        return 0
    else:
        print("❌ POST-HOOK FAILED - Some syncs failed")
        return 2


def cmd_status(args) -> int:
    """Show current sync status and session lock status."""
    print_header()
    print("Mode: STATUS")
    print()
    
    # ========================================
    # Session Lock Status (Level 2 Validation)
    # ========================================
    print("━━━ Session Lock Status (Level 2 Validation) ━━━")
    lock_status = get_session_lock_status()
    
    if lock_status.status == "NONE":
        print("🔓 No active session lock")
    elif lock_status.status == "COMPLETE":
        print(f"✅ Lock Status: COMPLETE")
        print(f"   Session started: {lock_status.session_start}")
        print(f"   Completed at: {lock_status.completed_at}")
    elif lock_status.status == "ACTIVE":
        print(f"⛔ Lock Status: ACTIVE (BLOCKING)")
        print(f"   Session started: {lock_status.session_start}")
        print(f"   ⚠️  Next session will be BLOCKED until this completes")
    elif lock_status.status == "STALE":
        print(f"⚠️  Lock Status: STALE")
        print(f"   {lock_status.message}")
    else:
        print(f"❓ Lock Status: {lock_status.status}")
        print(f"   {lock_status.message}")
    
    print()
    
    # ========================================
    # Sync Status
    # ========================================
    print("━━━ Sync Status ━━━")
    cache = load_cache()
    
    print(f"📅 Last sync: {cache.get('last_run', 'never')}")
    print()
    
    all_synced, details = check_sync_status(args.verbose)
    
    print("📂 Directory Status:")
    for name, info in details["directories"].items():
        config = SYNC_HANDLERS.get(name, {})
        status = "✅ Synced" if not info["changed"] else "⚠️  Changed"
        print(f"   {name}:")
        print(f"      Status: {status}")
        print(f"      Files: {info['file_count']}")
        print(f"      Hash: {info['hash']}")
        if config.get("scripts"):
            scripts = ", ".join(s[0] for s in config["scripts"])
            print(f"      Scripts: {scripts}")
    
    print()
    
    if all_synced:
        print("✅ All directories in sync")
    else:
        print(f"⚠️  Sync needed: {', '.join(details['changes_needed'])}")
    
    return 0


def cmd_clear_lock(args) -> int:
    """Clear the session lock (emergency use only)."""
    print_header()
    print("Mode: CLEAR LOCK")
    print()
    
    if not args.force:
        print("⚠️  CAUTION: Clearing the session lock is an emergency operation.")
        print("   Only use this if you're SURE no session is running.")
        print()
        print("   To proceed, run: python3 tools/post_hook.py --clear-lock --force")
        return 1
    
    success, message = clear_session_lock(force=True)
    print(message)
    
    return 0 if success else 2


def main():
    parser = argparse.ArgumentParser(
        description="Unified Post-Hook Orchestrator - Single entry point for all sync operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python tools/post_hook.py              # Auto-detect and sync changes + mark lock COMPLETE
    python tools/post_hook.py --check      # Check only (CI/CD mode)
    python tools/post_hook.py --force      # Force sync all domains
    python tools/post_hook.py --only hooks # Sync only hooks domain
    python tools/post_hook.py --only skills,commands  # Sync specific domains
    python tools/post_hook.py --status     # Show sync status + lock status
    python tools/post_hook.py --clear-lock --force  # Emergency clear lock (USE WITH CAUTION)

⛔ SESSION LOCK ENFORCEMENT (Two-Level Validation):
    Level 1: Documentation tells AI to run this
    Level 2: This script validates and BLOCKS if lock incomplete

This replaces individual calls to:
    - python skills/skill-architect/scripts/dag_manager.py --sync
    - python tools/command_sync.py post-hook
    - python tools/skill_converter.py full-sync
    - python tools/mcp_sync.py sync-all

⛔ MANDATORY: Run this at END of EVERY AI session.
        """
    )
    
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="Check only - returns non-zero if sync needed (CI/CD mode)"
    )
    
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Force sync all directories regardless of changes (also required for --clear-lock)"
    )
    
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show detailed sync status and session lock status"
    )
    
    parser.add_argument(
        "--clear-lock",
        action="store_true",
        help="Clear the session lock (EMERGENCY USE ONLY - requires --force)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "--only",
        type=str,
        help=f"Sync only specific domain(s). Comma-separated. Options: {', '.join(SYNC_HANDLERS.keys())}"
    )

    args = parser.parse_args()
    
    # Handle commands in priority order
    if args.clear_lock:
        sys.exit(cmd_clear_lock(args))
    elif args.status:
        sys.exit(cmd_status(args))
    elif args.check:
        sys.exit(cmd_check(args))
    else:
        sys.exit(cmd_sync(args))


if __name__ == "__main__":
    main()
