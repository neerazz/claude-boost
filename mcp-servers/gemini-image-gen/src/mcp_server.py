#!/usr/bin/env python3
"""
Gemini Image Generation MCP Server

Exposes image generation via Google's Gemini API as an MCP tool.
- Free tier: gemini-2.5-flash-image, gemini-3-pro-image-preview (uses generate_content)
- Paid tier: imagen-4.0-* models (uses generate_images)

FALLBACK: When API quota/capacity is exhausted, automatically falls back to Gemini CLI
if available (requires gcloud + gemini CLI + pro subscription).

Default output: /Users/neeraj/Pictures
"""

from __future__ import annotations

import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Optional, Dict
from io import BytesIO

# ============================================================================
# CONFIGURATION
# ============================================================================
# API key loaded from environment variable for security
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
DEFAULT_OUTPUT_DIR = Path(os.environ.get("GEMINI_OUTPUT_DIR", "/Users/neeraj/Pictures"))
DEFAULT_MODEL = "gemini-3-pro-image-preview"  # Free tier model (best quality)

# CLI Fallback settings (ADC = Application Default Credentials)
CLI_FALLBACK_ENABLED = os.environ.get("GEMINI_CLI_FALLBACK", "true").lower() == "true"
CLI_FALLBACK_MODEL = os.environ.get("GEMINI_CLI_MODEL", "gemini-2.0-flash-exp-image-generation")
# ============================================================================

AVAILABLE_MODELS = {
    "gemini-2.5-flash-image": "Free tier - Best quality image generation",
    "gemini-3-pro-image-preview": "Free tier - Nano Banana Pro, latest model",
    "gemini-2.0-flash-exp-image-generation": "Free tier - Experimental flash model",
    "models/imagen-4.0-ultra-generate-001": "Paid - Imagen 4 Ultra, maximum detail",
    "models/imagen-4.0-generate-001": "Paid - Imagen 4 Standard",
    "models/imagen-4.0-fast-generate-001": "Paid - Imagen 4 Fast",
}

# Import CLI fallback module (optional - graceful degradation if not available)
try:
    from cli_fallback import (
        should_use_cli_fallback,
        generate_image_via_cli,
        get_cli_status,
        install_gemini_cli,
        initiate_login,
    )
    CLI_FALLBACK_AVAILABLE = True
except ImportError:
    CLI_FALLBACK_AVAILABLE = False


def get_output_path(output_arg: Optional[str] = None) -> Path:
    """Determine output path. Default: /Users/neeraj/Pictures with timestamp."""
    if output_arg:
        output_path = Path(output_arg).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return output_path
    
    DEFAULT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = DEFAULT_OUTPUT_DIR / f"gemini_{timestamp}.png"
    
    counter = 1
    while output_path.exists():
        output_path = DEFAULT_OUTPUT_DIR / f"gemini_{timestamp}_{counter}.png"
        counter += 1
    
    return output_path


def generate_image_api(
    prompt: str,
    output_path: Path,
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
) -> Dict[str, Any]:
    """
    Generate an image using Google's Gemini API (primary method).
    
    Args:
        prompt: Detailed image description
        output_path: Where to save the image
        model: Model ID (default: gemini-2.5-flash-image)
        aspect_ratio: Image ratio for Imagen models (1:1, 3:4, 4:3, 9:16, 16:9)
        resolution: 1K, 2K, or 4K for Imagen models
    
    Returns:
        Dict with success status, path, and details
    """
    try:
        from google import genai
        from google.genai import types
        from PIL import Image
    except ImportError:
        return {
            "success": False,
            "error": "Missing packages. Run: pip install google-genai pillow",
            "recoverable": False
        }
    
    if not GEMINI_API_KEY:
        return {
            "success": False,
            "error": "Gemini API key not configured. Set GEMINI_API_KEY environment variable.",
            "recoverable": False
        }
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        if model.startswith("models/imagen"):
            # Paid tier: Imagen models using generate_images API
            result = client.models.generate_images(
                model=model,
                prompt=prompt,
                config=dict(
                    number_of_images=1,
                    output_mime_type="image/jpeg",
                    aspect_ratio=aspect_ratio,
                    image_size=resolution,
                ),
            )
            
            if not result.generated_images:
                return {
                    "success": False,
                    "error": "No image generated - prompt may have been filtered",
                    "recoverable": False
                }
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result.generated_images[0].image.save(str(output_path))
            
        else:
            # Free tier: Gemini models using generate_content API
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=['TEXT', 'IMAGE'],
                ),
            )
            
            image_saved = False
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    image_data = part.inline_data.data
                    image = Image.open(BytesIO(image_data))
                    
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    image.save(str(output_path))
                    image_saved = True
                    break
            
            if not image_saved:
                return {
                    "success": False,
                    "error": "No image generated - prompt may have been filtered",
                    "recoverable": False
                }
        
        return {
            "success": True,
            "path": str(output_path),
            "model": model,
            "method": "api",
            "prompt_used": prompt[:200] + "..." if len(prompt) > 200 else prompt
        }
        
    except Exception as e:
        error_msg = str(e).lower()
        original_error = str(e)
        
        # Classify the error
        if "api key" in error_msg or "authentication" in error_msg:
            return {
                "success": False,
                "error": "Invalid API key",
                "original_error": original_error,
                "recoverable": False
            }
        elif "safety" in error_msg or "blocked" in error_msg:
            return {
                "success": False,
                "error": "Content blocked by safety filters - modify prompt",
                "original_error": original_error,
                "recoverable": False
            }
        elif "not found" in error_msg:
            return {
                "success": False,
                "error": f"Model '{model}' not found",
                "original_error": original_error,
                "recoverable": False
            }
        elif "billed" in error_msg:
            return {
                "success": False,
                "error": "This model requires a billed account. Use gemini-2.5-flash-image for free tier.",
                "original_error": original_error,
                "recoverable": False
            }
        # Capacity/quota errors - these ARE recoverable via CLI fallback
        elif any(pattern in error_msg for pattern in [
            "rate limit", "quota", "resource_exhausted", "capacity",
            "overloaded", "503", "service unavailable", "tokens",
            "too many requests", "limit exceeded"
        ]):
            return {
                "success": False,
                "error": "API quota/capacity exceeded",
                "original_error": original_error,
                "recoverable": True,  # CLI fallback can handle this
                "error_type": "capacity"
            }
        else:
            return {
                "success": False,
                "error": original_error,
                "recoverable": False
            }


def generate_image(
    prompt: str,
    output_path: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    aspect_ratio: str = "1:1",
    resolution: str = "1K",
    use_cli_fallback: bool = True,
) -> Dict[str, Any]:
    """
    Generate an image using Google's Gemini API with CLI fallback.
    
    Primary flow:
    1. Try API generation
    2. If API fails with capacity/quota error AND CLI fallback is enabled:
       - Check CLI availability
       - Fall back to CLI generation
    
    Args:
        prompt: Detailed image description
        output_path: Where to save (default: /Users/neeraj/Pictures)
        model: Model ID (default: gemini-2.5-flash-image)
        aspect_ratio: Image ratio (1:1, 3:4, 4:3, 9:16, 16:9)
        resolution: 1K, 2K, or 4K for Imagen models
        use_cli_fallback: Whether to attempt CLI fallback on API failure
    
    Returns:
        Dict with success status, path, and details
    """
    final_path = get_output_path(output_path)
    
    # Step 1: Try API generation (primary method)
    api_result = generate_image_api(
        prompt=prompt,
        output_path=final_path,
        model=model,
        aspect_ratio=aspect_ratio,
        resolution=resolution,
    )
    
    # If API succeeded, return result
    if api_result.get("success"):
        return api_result
    
    # Step 2: Check if we should try CLI fallback
    should_fallback = (
        use_cli_fallback and
        CLI_FALLBACK_ENABLED and
        CLI_FALLBACK_AVAILABLE and
        api_result.get("recoverable", False)
    )
    
    if not should_fallback:
        # Cannot or should not use fallback
        if not CLI_FALLBACK_AVAILABLE:
            api_result["fallback_note"] = "CLI fallback module not available"
        elif not CLI_FALLBACK_ENABLED:
            api_result["fallback_note"] = "CLI fallback disabled via GEMINI_CLI_FALLBACK env var"
        elif not api_result.get("recoverable"):
            api_result["fallback_note"] = "Error type not suitable for CLI fallback"
        return api_result
    
    # Step 3: Attempt CLI fallback
    api_result["attempting_cli_fallback"] = True
    
    # Check CLI status first
    cli_status = get_cli_status()
    
    if not cli_status.get("ready"):
        # CLI not ready - return API error with setup instructions
        api_result["cli_fallback_failed"] = True
        api_result["cli_status"] = cli_status
        api_result["fallback_note"] = "CLI fallback not ready - see cli_status for setup instructions"
        return api_result
    
    # Step 4: Execute CLI fallback
    cli_result = generate_image_via_cli(
        prompt=prompt,
        output_path=final_path,
        model=CLI_FALLBACK_MODEL,
        aspect_ratio=aspect_ratio,
    )
    
    if cli_result.get("success"):
        cli_result["api_error"] = api_result.get("error")
        cli_result["fallback_used"] = True
        cli_result["note"] = f"Generated via CLI fallback (API error: {api_result.get('error_type', 'capacity')})"
        return cli_result
    else:
        # Both API and CLI failed
        return {
            "success": False,
            "error": "Both API and CLI fallback failed",
            "api_error": api_result.get("error"),
            "cli_error": cli_result.get("error"),
            "cli_details": cli_result.get("details"),
            "suggestion": "Check your subscription status and quota limits"
        }


def list_models() -> Dict[str, Any]:
    """List available models and CLI fallback status."""
    result = {
        "models": AVAILABLE_MODELS,
        "default": DEFAULT_MODEL,
        "default_output_dir": str(DEFAULT_OUTPUT_DIR),
        "cli_fallback": {
            "enabled": CLI_FALLBACK_ENABLED,
            "module_available": CLI_FALLBACK_AVAILABLE,
            "default_model": CLI_FALLBACK_MODEL,
        }
    }
    
    # Add CLI status if available
    if CLI_FALLBACK_AVAILABLE:
        result["cli_fallback"]["status"] = get_cli_status()
    
    return result


def setup_cli_fallback() -> Dict[str, Any]:
    """
    Setup Gemini CLI for fallback image generation.
    
    This tool helps users set up the CLI fallback by:
    1. Checking current status
    2. Installing Gemini CLI if needed
    3. Providing login instructions
    
    Returns:
        Dict with setup status and next steps
    """
    if not CLI_FALLBACK_AVAILABLE:
        return {
            "success": False,
            "error": "CLI fallback module not available",
            "suggestion": "Ensure cli_fallback.py is in the same directory as mcp_server.py"
        }
    
    status = get_cli_status()
    
    if status.get("ready"):
        return {
            "success": True,
            "message": "CLI fallback is already configured and ready",
            "status": status
        }
    
    # Determine what needs to be done
    components = status.get("components", {})
    
    # Check gcloud
    if not components.get("gcloud_sdk", {}).get("installed"):
        return {
            "success": False,
            "step": "install_gcloud",
            "message": "Google Cloud SDK needs to be installed first",
            "instructions": [
                "macOS: brew install --cask google-cloud-sdk",
                "Linux: curl https://sdk.cloud.google.com | bash",
                "Windows: https://cloud.google.com/sdk/docs/install",
                "",
                "After installation, restart your terminal and run: gcloud init"
            ],
            "status": status
        }
    
    # Check Gemini CLI
    if not components.get("gemini_cli", {}).get("installed"):
        # Try to install it
        install_result = install_gemini_cli(interactive=False)
        if install_result.get("success"):
            return {
                "success": True,
                "step": "cli_installed",
                "message": "Gemini CLI installed successfully",
                "next_step": "Run 'gcloud auth login' to authenticate",
                "status": get_cli_status()  # Refresh status
            }
        else:
            return {
                "success": False,
                "step": "install_cli",
                "message": "Failed to auto-install Gemini CLI",
                "manual_command": "gcloud components install gemini",
                "error": install_result.get("error"),
                "status": status
            }
    
    # Check authentication
    if not components.get("authentication", {}).get("authenticated"):
        login_info = initiate_login()
        return {
            "success": False,
            "step": "authenticate",
            "message": "Authentication required",
            "instructions": login_info.get("instructions", []),
            "command": login_info.get("command", "gcloud auth login"),
            "note": "Ensure you sign in with an account that has Gemini Pro subscription",
            "status": status
        }
    
    # Should be ready now
    return {
        "success": True,
        "message": "CLI fallback setup complete",
        "status": get_cli_status()
    }


def get_fallback_status() -> Dict[str, Any]:
    """
    Get detailed status of the CLI fallback system.
    
    Returns:
        Dict with comprehensive fallback status
    """
    if not CLI_FALLBACK_AVAILABLE:
        return {
            "available": False,
            "reason": "CLI fallback module not loaded",
            "suggestion": "Check that cli_fallback.py exists in the src directory"
        }
    
    status = get_cli_status()
    
    return {
        "available": True,
        "enabled": CLI_FALLBACK_ENABLED,
        "ready": status.get("ready", False),
        "cli_model": CLI_FALLBACK_MODEL,
        "components": status.get("components", {}),
        "required_actions": status.get("required_actions", [])
    }


# MCP Protocol Implementation
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
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "gemini-image-gen",
                    "version": "3.0.0"  # Version bump for CLI fallback
                }
            }
        }
    
    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "generate_image",
                        "description": f"""Generate an image using Google Gemini API with automatic CLI fallback.

Primary: Uses Gemini API (model: {DEFAULT_MODEL})
Fallback: Uses Gemini CLI when API quota/capacity is exhausted (requires pro subscription)

Output saves to {DEFAULT_OUTPUT_DIR} by default.

If API fails due to quota/rate limits, automatically attempts CLI fallback if configured.""",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "prompt": {
                                    "type": "string",
                                    "description": "Detailed image description. Include: subject, style, environment, lighting, mood. Be specific for best results."
                                },
                                "model": {
                                    "type": "string",
                                    "description": f"Model ID for API (default: {DEFAULT_MODEL}). CLI fallback uses {CLI_FALLBACK_MODEL}.",
                                    "default": DEFAULT_MODEL
                                },
                                "output_path": {
                                    "type": "string",
                                    "description": f"Full path to save image. Defaults to {DEFAULT_OUTPUT_DIR}/gemini_<timestamp>.png"
                                },
                                "aspect_ratio": {
                                    "type": "string",
                                    "description": "Image ratio: 1:1 (square), 3:4 (portrait), 4:3 (landscape), 9:16 (mobile), 16:9 (widescreen)",
                                    "default": "1:1"
                                },
                                "resolution": {
                                    "type": "string",
                                    "description": "Image resolution for Imagen models: 1K, 2K, or 4K",
                                    "default": "1K"
                                },
                                "use_cli_fallback": {
                                    "type": "boolean",
                                    "description": "Whether to attempt CLI fallback if API fails with quota/capacity error",
                                    "default": True
                                }
                            },
                            "required": ["prompt"]
                        }
                    },
                    {
                        "name": "list_models",
                        "description": "List available Gemini image generation models and CLI fallback status.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "setup_cli_fallback",
                        "description": """Setup Gemini CLI for fallback image generation.

Use this when you want to configure CLI fallback for when API quota is exhausted.

Requirements:
1. Google Cloud SDK (gcloud)
2. Gemini CLI component
3. Google account with Gemini Pro subscription

This tool will guide you through the setup process step by step.""",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    },
                    {
                        "name": "get_fallback_status",
                        "description": "Get detailed status of the CLI fallback system including component readiness and required actions.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {}
                        }
                    }
                ]
            }
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "generate_image":
            result = generate_image(
                prompt=arguments.get("prompt", ""),
                output_path=arguments.get("output_path"),
                model=arguments.get("model", DEFAULT_MODEL),
                aspect_ratio=arguments.get("aspect_ratio", "1:1"),
                resolution=arguments.get("resolution", "1K"),
                use_cli_fallback=arguments.get("use_cli_fallback", True),
            )
        elif tool_name == "list_models":
            result = list_models()
        elif tool_name == "setup_cli_fallback":
            result = setup_cli_fallback()
        elif tool_name == "get_fallback_status":
            result = get_fallback_status()
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        }
    
    elif method == "notifications/initialized":
        return None  # No response needed for notifications
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
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
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            sys.stdout.write(json.dumps(error_response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
