#!/usr/bin/env python3
"""
Preflight Gate - Universal Enforcement for ALL AI Coding Tools
===============================================================

⛔ MANDATORY: ALL AI tools MUST call this BEFORE starting work.

This script enforces rules ACROSS ALL AI tools:
- Claude Code, Cursor, Gemini CLI, Codex, Antigravity

Usage:
    python3 tools/preflight_gate.py              # Check if session can start
    python3 tools/preflight_gate.py --status     # Show current status
    python3 tools/preflight_gate.py --clear-lock # Clear stale lock (emergency)
    python3 tools/preflight_gate.py --validate   # Run all validation checks

Exit Codes:
    0 = OK to proceed
    1 = BLOCKED - Previous session incomplete
    2 = BLOCKED - Validation failed
    3 = WARNING - Proceed with caution

Enforcement Layers:
    1. Session Lock Check - Was previous session completed?
    2. Containment Check - Are all domains self-contained?
    3. Sync Status Check - Are all domains in sync?
    4. Structure Check - Do skills have required files?

AGENTS.md Compliance:
    This is the UNIVERSAL gate for Section 4.0 (Master Rule Tree).
    All AI tools should call this at session start.
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

# ============================================================================
# Configuration
# ============================================================================

REPO_ROOT = Path(__file__).parent.parent
CACHE_DIR = REPO_ROOT / "data" / "cache"
SESSION_LOCK_PATH = CACHE_DIR / "session_lock.json"
PREFLIGHT_REPORT_PATH = CACHE_DIR / "preflight_report.json"

# Validation checks to run
VALIDATION_CHECKS = {
    "session_lock": {
        "name": "Session Lock",
        "description": "Check if previous session completed",
        "severity": "BLOCKING",  # BLOCKING, WARNING
    },
    "containment": {
        "name": "Self-Containment",
        "description": "Check for ../ references outside domains",
        "severity": "BLOCKING",
    },
    "sync_status": {
        "name": "Sync Status",
        "description": "Check if domains need syncing",
        "severity": "WARNING",
    },
    "skill_structure": {
        "name": "Skill Structure",
        "description": "Check skills have required files",
        "severity": "WARNING",
    },
}


# ============================================================================
# Session Lock Check
# ============================================================================

def check_session_lock() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if previous session completed properly.

    Returns:
        (passed, message, details)
    """
    if not SESSION_LOCK_PATH.exists():
        return True, "No active session lock", {"status": "NONE"}

    try:
        lock_data = json.loads(SESSION_LOCK_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False, "Session lock file is corrupt", {"status": "CORRUPT"}

    status = lock_data.get("status", "UNKNOWN")
    session_start = lock_data.get("session_start")

    if status == "COMPLETE":
        return True, f"Previous session completed at {lock_data.get('completed_at')}", {
            "status": "COMPLETE",
            "completed_at": lock_data.get("completed_at"),
        }

    if status == "ACTIVE":
        # Check if stale (>24 hours)
        if session_start:
            try:
                start_time = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                age_hours = (datetime.now(timezone.utc) - start_time).total_seconds() / 3600
                if age_hours > 24:
                    return False, f"STALE lock from {age_hours:.1f}h ago - use --clear-lock", {
                        "status": "STALE",
                        "age_hours": age_hours,
                        "session_start": session_start,
                    }
            except (ValueError, TypeError):
                pass

        return False, f"Previous session started {session_start} but did not complete", {
            "status": "ACTIVE",
            "session_start": session_start,
            "required_action": "Run: python3 tools/post_hook.py",
        }

    return False, f"Unknown lock status: {status}", {"status": status}


# ============================================================================
# Containment Check
# ============================================================================

def check_containment() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check for ../ references that break self-containment.

    Returns:
        (passed, message, details)
    """
    violations = []
    checked_files = 0

    domains = ["skills", "commands", "mcp-servers"]

    for domain in domains:
        domain_path = REPO_ROOT / domain
        if not domain_path.exists():
            continue

        for file_path in domain_path.rglob("*"):
            if file_path.is_file() and file_path.suffix in [".py", ".md", ".json", ".yaml", ".yml"]:
                try:
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    checked_files += 1

                    # Check for ../ references that go outside domain
                    if "../" in content:
                        # Count how many levels up
                        lines = content.split("\n")
                        for line_num, line in enumerate(lines, 1):
                            if "../" in line:
                                # Check if it escapes the domain
                                rel_path = file_path.relative_to(REPO_ROOT)
                                depth = len(rel_path.parts) - 1  # depth within domain
                                escapes = line.count("../")
                                if escapes >= depth:
                                    violations.append({
                                        "file": str(rel_path),
                                        "line": line_num,
                                        "content": line.strip()[:100],
                                    })
                except Exception:
                    continue

    if violations:
        return False, f"{len(violations)} containment violations found", {
            "violations": violations[:10],  # Limit to 10
            "total": len(violations),
            "checked_files": checked_files,
        }

    return True, f"Containment OK ({checked_files} files checked)", {
        "checked_files": checked_files,
        "violations": 0,
    }


# ============================================================================
# Sync Status Check
# ============================================================================

def check_sync_status() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if domains need syncing.

    Returns:
        (passed, message, details)
    """
    try:
        result = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "post_hook.py"), "--check"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=60,
        )

        if result.returncode == 0:
            return True, "All domains in sync", {"sync_needed": False}
        else:
            # Parse output to find what needs syncing
            return True, "Sync may be needed (warning)", {
                "sync_needed": True,
                "hint": "Run: python3 tools/post_hook.py",
            }
    except subprocess.TimeoutExpired:
        return True, "Sync check timed out (warning)", {"timeout": True}
    except Exception as e:
        return True, f"Sync check failed: {e}", {"error": str(e)}


# ============================================================================
# Skill Structure Check
# ============================================================================

def check_skill_structure() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check that skills have required files.

    Returns:
        (passed, message, details)
    """
    skills_dir = REPO_ROOT / "skills"
    if not skills_dir.exists():
        return True, "No skills directory", {}

    issues = []
    checked = 0

    for skill_dir in skills_dir.iterdir():
        if skill_dir.is_dir() and not skill_dir.name.startswith("."):
            # Skip non-skill directories
            if skill_dir.name in ["scripts", "reference", "__pycache__"]:
                continue

            checked += 1
            skill_md = skill_dir / "SKILL.md"

            if not skill_md.exists():
                issues.append({
                    "skill": skill_dir.name,
                    "issue": "Missing SKILL.md",
                })

    if issues:
        return True, f"{len(issues)} skills missing SKILL.md (warning)", {
            "issues": issues[:10],
            "total_issues": len(issues),
            "skills_checked": checked,
        }

    return True, f"All {checked} skills have SKILL.md", {
        "skills_checked": checked,
        "issues": 0,
    }


# ============================================================================
# Main Preflight Gate
# ============================================================================

def run_preflight_gate(validate_all: bool = False) -> Tuple[int, Dict[str, Any]]:
    """
    Run all preflight checks.

    Args:
        validate_all: If True, run all checks. If False, only blocking checks.

    Returns:
        (exit_code, report)
    """
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "passed": True,
        "blocked": False,
        "warnings": [],
    }

    checks_to_run = VALIDATION_CHECKS if validate_all else {
        k: v for k, v in VALIDATION_CHECKS.items() if v["severity"] == "BLOCKING"
    }

    for check_id, check_config in checks_to_run.items():
        print(f"[preflight] Checking {check_config['name']}...")

        # Run the appropriate check
        if check_id == "session_lock":
            passed, message, details = check_session_lock()
        elif check_id == "containment":
            passed, message, details = check_containment()
        elif check_id == "sync_status":
            passed, message, details = check_sync_status()
        elif check_id == "skill_structure":
            passed, message, details = check_skill_structure()
        else:
            continue

        report["checks"][check_id] = {
            "name": check_config["name"],
            "passed": passed,
            "message": message,
            "severity": check_config["severity"],
            "details": details,
        }

        if not passed:
            if check_config["severity"] == "BLOCKING":
                report["passed"] = False
                report["blocked"] = True
                print(f"[preflight] ⛔ {check_config['name']}: {message}")
            else:
                report["warnings"].append(f"{check_config['name']}: {message}")
                print(f"[preflight] ⚠️  {check_config['name']}: {message}")
        else:
            print(f"[preflight] ✅ {check_config['name']}: {message}")

    # Save report
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    PREFLIGHT_REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")

    # Determine exit code
    if report["blocked"]:
        return 1, report
    elif report["warnings"]:
        return 3, report
    else:
        return 0, report


def clear_session_lock(force: bool = False) -> Tuple[bool, str]:
    """Clear the session lock (emergency use only)."""
    if not SESSION_LOCK_PATH.exists():
        return True, "No session lock to clear"

    if not force:
        # Check if lock is stale
        try:
            lock_data = json.loads(SESSION_LOCK_PATH.read_text(encoding="utf-8"))
            if lock_data.get("status") == "ACTIVE":
                session_start = lock_data.get("session_start")
                if session_start:
                    start_time = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                    age_hours = (datetime.now(timezone.utc) - start_time).total_seconds() / 3600
                    if age_hours < 24:
                        return False, f"Lock is only {age_hours:.1f}h old. Use --force to clear."
        except Exception:
            pass

    try:
        SESSION_LOCK_PATH.unlink()
        return True, "Session lock cleared"
    except OSError as e:
        return False, f"Failed to clear lock: {e}"


# ============================================================================
# CLI Interface
# ============================================================================

def print_header():
    """Print CLI header."""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║            Preflight Gate - Universal Enforcement            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()


def print_report(report: Dict[str, Any]):
    """Print preflight report."""
    print()
    print("━━━ Preflight Report ━━━")

    for check_id, check_result in report["checks"].items():
        status = "✅" if check_result["passed"] else ("⛔" if check_result["severity"] == "BLOCKING" else "⚠️")
        print(f"   {status} {check_result['name']}: {check_result['message']}")

    print()

    if report["blocked"]:
        print("⛔ BLOCKED - Cannot proceed until issues are resolved")
        print()
        print("   Required actions:")
        for check_id, check_result in report["checks"].items():
            if not check_result["passed"] and check_result["severity"] == "BLOCKING":
                if "required_action" in check_result.get("details", {}):
                    print(f"   → {check_result['details']['required_action']}")
    elif report["warnings"]:
        print("⚠️  WARNINGS - Proceed with caution")
        for warning in report["warnings"]:
            print(f"   → {warning}")
    else:
        print("✅ ALL CHECKS PASSED - Ready to proceed")


def main():
    parser = argparse.ArgumentParser(
        description="Preflight Gate - Universal enforcement for all AI coding tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 tools/preflight_gate.py              # Quick check (blocking only)
    python3 tools/preflight_gate.py --validate   # Full validation
    python3 tools/preflight_gate.py --status     # Show current status
    python3 tools/preflight_gate.py --clear-lock # Clear stale lock

⛔ ALL AI tools (Claude, Cursor, Gemini, Codex, Antigravity) should call this
   at session start to ensure rules are followed.
        """
    )

    parser.add_argument(
        "--validate", "-v",
        action="store_true",
        help="Run full validation (all checks, not just blocking)"
    )

    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show current preflight status without running checks"
    )

    parser.add_argument(
        "--clear-lock",
        action="store_true",
        help="Clear the session lock (emergency use only)"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force clear lock even if not stale"
    )

    args = parser.parse_args()

    print_header()

    if args.clear_lock:
        success, message = clear_session_lock(force=args.force)
        print(f"{'✅' if success else '❌'} {message}")
        sys.exit(0 if success else 1)

    if args.status:
        # Just show status from last report
        if PREFLIGHT_REPORT_PATH.exists():
            try:
                report = json.loads(PREFLIGHT_REPORT_PATH.read_text(encoding="utf-8"))
                print(f"Last check: {report.get('timestamp', 'unknown')}")
                print_report(report)
            except Exception as e:
                print(f"Could not read status: {e}")
        else:
            print("No previous preflight check found.")
            print("Run: python3 tools/preflight_gate.py")
        sys.exit(0)

    # Run preflight checks
    exit_code, report = run_preflight_gate(validate_all=args.validate)
    print_report(report)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
