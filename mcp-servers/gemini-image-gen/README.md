# Gemini Image Generation MCP Server

## Table of Contents
- [Features](#features)
- [Quick Start](#quick-start)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [Available Tools](#available-tools)
- [Models](#models)
- [Configuration](#configuration)
- [Fallback Details](#fallback-details)
- [Troubleshooting](#troubleshooting)
- [File Structure](#file-structure)



Generate images using Google's Gemini API with **FREE Pollinations.ai fallback** when quota is exhausted.

## Features

- **Primary**: Gemini API (free tier models)
- **Fallback**: Pollinations.ai (FREE, no API key needed!)
- **Zero Config Fallback**: Works automatically, no setup required

## Quick Start

```bash
# Install dependencies
pip install google-genai pillow

# Set API key
export GEMINI_API_KEY="your-key"

# That's it! Fallback works automatically.
```

## How It Works

```
1. Try Gemini API
   ↓
   Quota exceeded?
   ↓
2. Fallback to Pollinations.ai (FREE)
   ↓
   ✅ Image generated!
```

## Usage

### Generate Image

```json
{
  "name": "generate_image",
  "arguments": {
    "prompt": "A red apple on white background",
    "output_path": "/Users/neeraj/Pictures/apple.png"
  }
}
```

### Response (with fallback)

```json
{
  "success": true,
  "path": "/Users/neeraj/Pictures/apple.png",
  "method": "pollinations_free",
  "fallback_used": true,
  "note": "Generated via CLI fallback (API error: capacity)"
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `generate_image` | Generate image (auto-fallback) |
| `list_models` | List available models |
| `get_fallback_status` | Check fallback status |

## Models

### Gemini API (Primary)
- `gemini-2.5-flash-image` - Best quality
- `gemini-2.0-flash-exp-image-generation` - Experimental

### Pollinations.ai (Fallback)
- `flux` - Default, high quality
- `turbo` - Faster generation

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | (required) | Gemini API key |
| `GEMINI_OUTPUT_DIR` | `/Users/neeraj/Pictures` | Output directory |
| `GEMINI_CLI_FALLBACK` | `true` | Enable fallback |

## Fallback Details

**Pollinations.ai** - https://pollinations.ai
- ✅ Completely FREE
- ✅ No API key required
- ✅ No registration needed
- ✅ High quality images
- ⏱️ Takes 30-90 seconds per image

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Gemini quota exceeded | Fallback activates automatically |
| Fallback timeout | Normal - takes up to 2 minutes |
| No image generated | Check prompt for blocked content |

## File Structure

```
gemini-image-gen/
├── README.md
├── requirements.txt
└── src/
    ├── mcp_server.py      # Main server
    └── cli_fallback.py    # Pollinations fallback
```
