#!/usr/bin/env python3
"""
Free Image Generation Fallback

Uses Pollinations.ai - completely FREE, no API key required.
Just a URL-based image generation service.

Example: https://image.pollinations.ai/prompt/A%20red%20apple
"""

import os
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Tuple

DEFAULT_OUTPUT_DIR = Path(os.environ.get("GEMINI_OUTPUT_DIR", "/Users/neeraj/Pictures"))


def generate_image_via_cli(
    prompt: str,
    output_path: Path,
    model: str = "flux",  # Pollinations default model
    aspect_ratio: str = "1:1",
) -> Dict[str, Any]:
    """
    Generate image using Pollinations.ai (FREE, no API key).
    
    Args:
        prompt: Image description
        output_path: Where to save the image
        model: Model name (flux, turbo, etc.)
        aspect_ratio: Image ratio (converted to width/height)
    
    Returns:
        Dict with success status and path
    """
    try:
        # Parse aspect ratio to dimensions
        width, height = 1024, 1024  # Default square
        if aspect_ratio == "16:9":
            width, height = 1280, 720
        elif aspect_ratio == "9:16":
            width, height = 720, 1280
        elif aspect_ratio == "4:3":
            width, height = 1024, 768
        elif aspect_ratio == "3:4":
            width, height = 768, 1024
        
        # URL encode the prompt
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Pollinations.ai URL - completely free, no API key
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&model={model}&nologo=true"
        
        # Download the image
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create request with user agent
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        
        with urllib.request.urlopen(req, timeout=120) as response:
            image_data = response.read()
        
        # Save the image
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return {
            "success": True,
            "path": str(output_path),
            "model": f"pollinations-{model}",
            "method": "pollinations_free",
            "prompt_used": prompt[:200] + "..." if len(prompt) > 200 else prompt
        }
        
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"Network error: {e.reason}",
            "method": "pollinations_free"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "method": "pollinations_free"
        }


def get_cli_status() -> Dict[str, Any]:
    """Check if Pollinations.ai is accessible."""
    try:
        # Quick check if service is up
        req = urllib.request.Request(
            "https://image.pollinations.ai/prompt/test?width=64&height=64",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        urllib.request.urlopen(req, timeout=10)
        return {
            "ready": True,
            "method": "pollinations_free",
            "components": {
                "pollinations": {"available": True, "message": "Pollinations.ai is accessible"}
            }
        }
    except Exception as e:
        return {
            "ready": False,
            "method": "pollinations_free", 
            "components": {
                "pollinations": {"available": False, "message": str(e)}
            }
        }


def should_use_cli_fallback(error_message: str) -> Tuple[bool, str]:
    """Always fallback on quota/capacity errors."""
    error_lower = error_message.lower()
    if any(p in error_lower for p in ["quota", "rate limit", "429", "exhausted", "capacity"]):
        return True, "Quota error - using free fallback"
    return False, "Not a quota error"


# Legacy compatibility aliases
def check_gemini_cli_installed():
    status = get_cli_status()
    return status["ready"], status["components"]["pollinations"]["message"]

def check_authentication_status():
    return True, "No auth needed - Pollinations is free", None

def install_gemini_cli(interactive=True):
    return {"message": "No installation needed - Pollinations is free"}

def initiate_login():
    return {"message": "No login needed - Pollinations is free"}

def get_fallback_status():
    return get_cli_status()

def check_gcloud_installed():
    return check_gemini_cli_installed()

def check_adc_authentication():
    return check_authentication_status()
