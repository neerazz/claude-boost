#!/usr/bin/env python3
"""
Slack MCP Server

Exposes Slack API operations as MCP tools for AI assistants.
Supports: messaging, channel management, user lookup, reactions, search, DMs, and auth.

Security: Token loaded from SLACK_BOT_TOKEN environment variable.

Tools:
- auth_test: Get current bot/user info (who am I)
- list_channels: List public/private channels
- list_conversations: List all conversations (channels, DMs, group DMs)
- send_message: Send a message to a channel or thread
- get_channel_history: Get messages from a channel (includes reactions)
- get_thread_replies: Get replies in a thread
- search_messages: Search messages workspace-wide
- list_users: List workspace users
- get_user_info: Get detailed user info
- add_reaction: Add reaction to a message
- remove_reaction: Remove reaction from a message
- get_reactions: Get all reactions on a message
- get_channel_info: Get channel details
- join_channel: Join a public channel
- set_channel_topic: Set channel topic
- get_permalink: Get message permalink
- open_conversation: Open a DM with a user
- get_conversation_members: Get members of a channel
"""

from __future__ import annotations

import json
import sys
import os
from typing import Any, Optional, Dict
from datetime import datetime
import urllib.request
import urllib.parse
import urllib.error

SLACK_API_BASE = "https://slack.com/api"


def _get_token() -> str:
    """Get the Slack bot token from environment."""
    return os.environ.get("SLACK_BOT_TOKEN", "")


def _slack_api(method: str, params: Optional[Dict[str, Any]] = None, post_json: bool = False) -> Dict[str, Any]:
    """Make a Slack API request."""
    token = _get_token()
    if not token:
        return {"ok": False, "error": "SLACK_BOT_TOKEN not configured"}

    url = f"{SLACK_API_BASE}/{method}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8" if post_json else "application/x-www-form-urlencoded"
    }

    try:
        if params:
            if post_json:
                data = json.dumps(params).encode('utf-8')
            else:
                data = urllib.parse.urlencode(params).encode('utf-8')
        else:
            data = None

        req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")

        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))

    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"ok": False, "error": f"Network error: {e.reason}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _format_timestamp(ts: str) -> str:
    """Convert Slack timestamp to readable format."""
    try:
        unix_ts = float(ts.split('.')[0])
        return datetime.fromtimestamp(unix_ts).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return ts


# ============================================================================
# SLACK TOOLS
# ============================================================================

def auth_test() -> Dict[str, Any]:
    """Get information about the current bot/user (who am I)."""
    result = _slack_api("auth.test")

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    return {
        "success": True,
        "user_id": result.get("user_id"),
        "user": result.get("user"),
        "team_id": result.get("team_id"),
        "team": result.get("team"),
        "bot_id": result.get("bot_id"),
        "is_enterprise_install": result.get("is_enterprise_install", False)
    }


def list_channels(
    types: str = "public_channel,private_channel",
    exclude_archived: bool = True,
    limit: int = 100
) -> Dict[str, Any]:
    """List channels in the workspace."""
    result = _slack_api("conversations.list", {
        "types": types,
        "exclude_archived": exclude_archived,
        "limit": min(limit, 1000)
    })

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    channels = []
    for ch in result.get("channels", []):
        channels.append({
            "id": ch.get("id"),
            "name": ch.get("name"),
            "is_private": ch.get("is_private", False),
            "is_member": ch.get("is_member", False),
            "is_im": ch.get("is_im", False),
            "is_mpim": ch.get("is_mpim", False),
            "topic": ch.get("topic", {}).get("value", ""),
            "purpose": ch.get("purpose", {}).get("value", ""),
            "num_members": ch.get("num_members", 0)
        })

    return {
        "success": True,
        "channels": channels,
        "count": len(channels)
    }


def list_conversations(
    types: str = "public_channel,private_channel,mpim,im",
    exclude_archived: bool = True,
    limit: int = 200
) -> Dict[str, Any]:
    """List all conversations including channels, DMs, and group DMs."""
    result = _slack_api("conversations.list", {
        "types": types,
        "exclude_archived": exclude_archived,
        "limit": min(limit, 1000)
    })

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    conversations = []
    for conv in result.get("channels", []):
        conv_type = "channel"
        if conv.get("is_im"):
            conv_type = "dm"
        elif conv.get("is_mpim"):
            conv_type = "group_dm"
        elif conv.get("is_private"):
            conv_type = "private_channel"

        conversations.append({
            "id": conv.get("id"),
            "name": conv.get("name", conv.get("user", "")),
            "type": conv_type,
            "is_member": conv.get("is_member", False),
            "user": conv.get("user"),  # For DMs, the other user's ID
            "topic": conv.get("topic", {}).get("value", ""),
            "purpose": conv.get("purpose", {}).get("value", ""),
            "num_members": conv.get("num_members", 0)
        })

    return {
        "success": True,
        "conversations": conversations,
        "count": len(conversations),
        "by_type": {
            "channels": len([c for c in conversations if c["type"] == "channel"]),
            "private_channels": len([c for c in conversations if c["type"] == "private_channel"]),
            "dms": len([c for c in conversations if c["type"] == "dm"]),
            "group_dms": len([c for c in conversations if c["type"] == "group_dm"])
        }
    }


def open_conversation(users: str) -> Dict[str, Any]:
    """Open a direct message conversation with one or more users.

    Args:
        users: Comma-separated list of user IDs (e.g., "U12345" for DM, "U12345,U67890" for group DM)
    """
    result = _slack_api("conversations.open", {"users": users}, post_json=True)

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    channel = result.get("channel", {})
    return {
        "success": True,
        "channel_id": channel.get("id"),
        "is_im": channel.get("is_im", False),
        "is_mpim": channel.get("is_mpim", False),
        "already_open": result.get("already_open", False)
    }


def send_message(
    channel: str,
    text: str,
    thread_ts: Optional[str] = None,
    unfurl_links: bool = True,
    unfurl_media: bool = True
) -> Dict[str, Any]:
    """Send a message to a channel or thread."""
    params = {
        "channel": channel,
        "text": text,
        "unfurl_links": unfurl_links,
        "unfurl_media": unfurl_media
    }

    if thread_ts:
        params["thread_ts"] = thread_ts

    result = _slack_api("chat.postMessage", params, post_json=True)

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    return {
        "success": True,
        "channel": result.get("channel"),
        "ts": result.get("ts"),
        "message_url": f"https://slack.com/archives/{result.get('channel')}/p{result.get('ts', '').replace('.', '')}"
    }


def get_channel_history(
    channel: str,
    limit: int = 20,
    oldest: Optional[str] = None,
    latest: Optional[str] = None,
    inclusive: bool = True
) -> Dict[str, Any]:
    """Get message history from a channel, including reactions."""
    params = {
        "channel": channel,
        "limit": min(limit, 100),
        "inclusive": inclusive
    }

    if oldest:
        params["oldest"] = oldest
    if latest:
        params["latest"] = latest

    result = _slack_api("conversations.history", params)

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    messages = []
    for msg in result.get("messages", []):
        messages.append({
            "ts": msg.get("ts"),
            "time": _format_timestamp(msg.get("ts", "")),
            "user": msg.get("user"),
            "text": msg.get("text", ""),
            "thread_ts": msg.get("thread_ts"),
            "reply_count": msg.get("reply_count", 0),
            "reply_users_count": msg.get("reply_users_count", 0),
            "reactions": [
                {
                    "name": r.get("name"),
                    "count": r.get("count"),
                    "users": r.get("users", [])
                }
                for r in msg.get("reactions", [])
            ],
            "has_reactions": len(msg.get("reactions", [])) > 0,
            "subtype": msg.get("subtype"),
            "bot_id": msg.get("bot_id"),
            "attachments": len(msg.get("attachments", [])),
            "files": len(msg.get("files", []))
        })

    return {
        "success": True,
        "channel": channel,
        "messages": messages,
        "has_more": result.get("has_more", False),
        "response_metadata": result.get("response_metadata", {})
    }


def get_thread_replies(
    channel: str,
    thread_ts: str,
    limit: int = 50,
    oldest: Optional[str] = None,
    latest: Optional[str] = None
) -> Dict[str, Any]:
    """Get replies in a message thread, including reactions."""
    params = {
        "channel": channel,
        "ts": thread_ts,
        "limit": min(limit, 100)
    }

    if oldest:
        params["oldest"] = oldest
    if latest:
        params["latest"] = latest

    result = _slack_api("conversations.replies", params)

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    messages = []
    for msg in result.get("messages", []):
        messages.append({
            "ts": msg.get("ts"),
            "time": _format_timestamp(msg.get("ts", "")),
            "user": msg.get("user"),
            "text": msg.get("text", ""),
            "is_parent": msg.get("ts") == thread_ts,
            "reactions": [
                {
                    "name": r.get("name"),
                    "count": r.get("count"),
                    "users": r.get("users", [])
                }
                for r in msg.get("reactions", [])
            ]
        })

    return {
        "success": True,
        "channel": channel,
        "thread_ts": thread_ts,
        "messages": messages,
        "reply_count": len(messages) - 1,  # Exclude parent
        "has_more": result.get("has_more", False)
    }


def search_messages(
    query: str,
    sort: str = "timestamp",
    sort_dir: str = "desc",
    count: int = 20
) -> Dict[str, Any]:
    """Search messages in the workspace."""
    result = _slack_api("search.messages", {
        "query": query,
        "sort": sort,
        "sort_dir": sort_dir,
        "count": min(count, 100)
    })

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    matches = []
    for match in result.get("messages", {}).get("matches", []):
        matches.append({
            "ts": match.get("ts"),
            "time": _format_timestamp(match.get("ts", "")),
            "user": match.get("user"),
            "username": match.get("username"),
            "text": match.get("text", ""),
            "channel_id": match.get("channel", {}).get("id"),
            "channel_name": match.get("channel", {}).get("name"),
            "permalink": match.get("permalink")
        })

    return {
        "success": True,
        "query": query,
        "matches": matches,
        "total": result.get("messages", {}).get("total", 0)
    }


def list_users(limit: int = 100) -> Dict[str, Any]:
    """List users in the workspace."""
    result = _slack_api("users.list", {"limit": min(limit, 200)})

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    users = []
    for user in result.get("members", []):
        if user.get("deleted"):
            continue

        profile = user.get("profile", {})
        users.append({
            "id": user.get("id"),
            "name": user.get("name"),
            "real_name": profile.get("real_name", ""),
            "display_name": profile.get("display_name", ""),
            "email": profile.get("email", ""),
            "title": profile.get("title", ""),
            "is_admin": user.get("is_admin", False),
            "is_bot": user.get("is_bot", False),
            "timezone": user.get("tz", "")
        })

    return {
        "success": True,
        "users": users,
        "count": len(users)
    }


def get_user_info(user_id: str) -> Dict[str, Any]:
    """Get detailed information about a user."""
    result = _slack_api("users.info", {"user": user_id})

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    user = result.get("user", {})
    profile = user.get("profile", {})

    return {
        "success": True,
        "user": {
            "id": user.get("id"),
            "name": user.get("name"),
            "real_name": profile.get("real_name", ""),
            "display_name": profile.get("display_name", ""),
            "email": profile.get("email", ""),
            "title": profile.get("title", ""),
            "phone": profile.get("phone", ""),
            "status_text": profile.get("status_text", ""),
            "status_emoji": profile.get("status_emoji", ""),
            "is_admin": user.get("is_admin", False),
            "is_owner": user.get("is_owner", False),
            "is_bot": user.get("is_bot", False),
            "timezone": user.get("tz", ""),
            "timezone_label": user.get("tz_label", "")
        }
    }


def add_reaction(
    channel: str,
    timestamp: str,
    name: str
) -> Dict[str, Any]:
    """Add a reaction to a message."""
    result = _slack_api("reactions.add", {
        "channel": channel,
        "timestamp": timestamp,
        "name": name  # Without colons, e.g., "thumbsup" not ":thumbsup:"
    }, post_json=True)

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    return {
        "success": True,
        "channel": channel,
        "timestamp": timestamp,
        "reaction": name
    }


def remove_reaction(
    channel: str,
    timestamp: str,
    name: str
) -> Dict[str, Any]:
    """Remove a reaction from a message."""
    result = _slack_api("reactions.remove", {
        "channel": channel,
        "timestamp": timestamp,
        "name": name
    }, post_json=True)

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    return {
        "success": True,
        "channel": channel,
        "timestamp": timestamp,
        "reaction_removed": name
    }


def get_reactions(
    channel: str,
    timestamp: str,
    full: bool = True
) -> Dict[str, Any]:
    """Get all reactions on a specific message."""
    result = _slack_api("reactions.get", {
        "channel": channel,
        "timestamp": timestamp,
        "full": full
    })

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    message = result.get("message", {})
    reactions = []

    for r in message.get("reactions", []):
        reactions.append({
            "name": r.get("name"),
            "count": r.get("count"),
            "users": r.get("users", [])
        })

    return {
        "success": True,
        "channel": channel,
        "timestamp": timestamp,
        "message_text": message.get("text", ""),
        "message_user": message.get("user"),
        "reactions": reactions,
        "total_reactions": len(reactions)
    }


def get_channel_info(channel: str) -> Dict[str, Any]:
    """Get detailed information about a channel."""
    result = _slack_api("conversations.info", {"channel": channel})

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    ch = result.get("channel", {})

    return {
        "success": True,
        "channel": {
            "id": ch.get("id"),
            "name": ch.get("name"),
            "is_private": ch.get("is_private", False),
            "is_archived": ch.get("is_archived", False),
            "is_member": ch.get("is_member", False),
            "is_im": ch.get("is_im", False),
            "is_mpim": ch.get("is_mpim", False),
            "topic": ch.get("topic", {}).get("value", ""),
            "purpose": ch.get("purpose", {}).get("value", ""),
            "creator": ch.get("creator"),
            "created": _format_timestamp(str(ch.get("created", ""))),
            "num_members": ch.get("num_members", 0)
        }
    }


def join_channel(channel: str) -> Dict[str, Any]:
    """Join a public channel."""
    result = _slack_api("conversations.join", {"channel": channel}, post_json=True)

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    return {
        "success": True,
        "channel": result.get("channel", {}).get("id"),
        "channel_name": result.get("channel", {}).get("name")
    }


def set_channel_topic(channel: str, topic: str) -> Dict[str, Any]:
    """Set the topic of a channel."""
    result = _slack_api("conversations.setTopic", {
        "channel": channel,
        "topic": topic
    }, post_json=True)

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    return {
        "success": True,
        "channel": channel,
        "topic": topic
    }


def get_permalink(channel: str, message_ts: str) -> Dict[str, Any]:
    """Get a permalink URL for a message."""
    result = _slack_api("chat.getPermalink", {
        "channel": channel,
        "message_ts": message_ts
    })

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    return {
        "success": True,
        "permalink": result.get("permalink"),
        "channel": channel,
        "message_ts": message_ts
    }


def get_conversation_members(channel: str, limit: int = 100) -> Dict[str, Any]:
    """Get all members of a channel/conversation."""
    result = _slack_api("conversations.members", {
        "channel": channel,
        "limit": min(limit, 1000)
    })

    if not result.get("ok"):
        return {"success": False, "error": result.get("error", "Unknown error")}

    return {
        "success": True,
        "channel": channel,
        "members": result.get("members", []),
        "count": len(result.get("members", []))
    }


# ============================================================================
# MCP PROTOCOL IMPLEMENTATION
# ============================================================================

TOOLS = [
    {
        "name": "auth_test",
        "description": "Get information about the current bot/user - answers 'who am I?' Returns user ID, username, team info.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "list_channels",
        "description": "List channels in the Slack workspace. Returns channel names, IDs, topics, and member counts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "types": {
                    "type": "string",
                    "description": "Channel types to list: public_channel, private_channel, mpim, im",
                    "default": "public_channel,private_channel"
                },
                "exclude_archived": {
                    "type": "boolean",
                    "description": "Exclude archived channels",
                    "default": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum channels to return (max 1000)",
                    "default": 100
                }
            }
        }
    },
    {
        "name": "list_conversations",
        "description": "List ALL conversations including channels, DMs, and group DMs. More comprehensive than list_channels.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "types": {
                    "type": "string",
                    "description": "Conversation types: public_channel, private_channel, mpim (group DM), im (DM)",
                    "default": "public_channel,private_channel,mpim,im"
                },
                "exclude_archived": {
                    "type": "boolean",
                    "description": "Exclude archived conversations",
                    "default": True
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum conversations to return (max 1000)",
                    "default": 200
                }
            }
        }
    },
    {
        "name": "open_conversation",
        "description": "Open a direct message conversation with one or more users. Use this to get a DM channel ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "users": {
                    "type": "string",
                    "description": "Comma-separated user IDs (e.g., 'U12345' for DM, 'U12345,U67890' for group DM)"
                }
            },
            "required": ["users"]
        }
    },
    {
        "name": "send_message",
        "description": "Send a message to a Slack channel or thread.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID or name (e.g., C1234567890 or #general)"
                },
                "text": {
                    "type": "string",
                    "description": "Message text (supports Slack markdown)"
                },
                "thread_ts": {
                    "type": "string",
                    "description": "Thread timestamp to reply to (makes this a threaded reply)"
                },
                "unfurl_links": {
                    "type": "boolean",
                    "description": "Enable link previews",
                    "default": True
                },
                "unfurl_media": {
                    "type": "boolean",
                    "description": "Enable media previews",
                    "default": True
                }
            },
            "required": ["channel", "text"]
        }
    },
    {
        "name": "get_channel_history",
        "description": "Get recent messages from a Slack channel. Includes reactions on each message.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID (e.g., C1234567890)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of messages to return (max 100)",
                    "default": 20
                },
                "oldest": {
                    "type": "string",
                    "description": "Only return messages after this timestamp"
                },
                "latest": {
                    "type": "string",
                    "description": "Only return messages before this timestamp"
                }
            },
            "required": ["channel"]
        }
    },
    {
        "name": "get_thread_replies",
        "description": "Get all replies in a message thread. Includes reactions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID containing the thread"
                },
                "thread_ts": {
                    "type": "string",
                    "description": "Timestamp of the parent message"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum replies to return (max 100)",
                    "default": 50
                }
            },
            "required": ["channel", "thread_ts"]
        }
    },
    {
        "name": "search_messages",
        "description": "Search for messages across the Slack workspace. Supports Slack search modifiers like 'from:@user' or 'in:#channel'.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (supports Slack search syntax)"
                },
                "sort": {
                    "type": "string",
                    "description": "Sort by: timestamp or score",
                    "default": "timestamp"
                },
                "sort_dir": {
                    "type": "string",
                    "description": "Sort direction: asc or desc",
                    "default": "desc"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of results (max 100)",
                    "default": 20
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_users",
        "description": "List users in the Slack workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum users to return (max 200)",
                    "default": 100
                }
            }
        }
    },
    {
        "name": "get_user_info",
        "description": "Get detailed information about a Slack user.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User ID (e.g., U1234567890)"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "add_reaction",
        "description": "Add an emoji reaction to a message.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID containing the message"
                },
                "timestamp": {
                    "type": "string",
                    "description": "Message timestamp"
                },
                "name": {
                    "type": "string",
                    "description": "Emoji name without colons (e.g., 'thumbsup' not ':thumbsup:')"
                }
            },
            "required": ["channel", "timestamp", "name"]
        }
    },
    {
        "name": "remove_reaction",
        "description": "Remove an emoji reaction from a message.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID containing the message"
                },
                "timestamp": {
                    "type": "string",
                    "description": "Message timestamp"
                },
                "name": {
                    "type": "string",
                    "description": "Emoji name to remove"
                }
            },
            "required": ["channel", "timestamp", "name"]
        }
    },
    {
        "name": "get_reactions",
        "description": "Get all reactions on a specific message, including which users reacted.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID containing the message"
                },
                "timestamp": {
                    "type": "string",
                    "description": "Message timestamp"
                },
                "full": {
                    "type": "boolean",
                    "description": "Include full user IDs for reactions",
                    "default": True
                }
            },
            "required": ["channel", "timestamp"]
        }
    },
    {
        "name": "get_channel_info",
        "description": "Get detailed information about a channel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID"
                }
            },
            "required": ["channel"]
        }
    },
    {
        "name": "join_channel",
        "description": "Join a public Slack channel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID to join"
                }
            },
            "required": ["channel"]
        }
    },
    {
        "name": "set_channel_topic",
        "description": "Set the topic of a Slack channel.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID"
                },
                "topic": {
                    "type": "string",
                    "description": "New channel topic"
                }
            },
            "required": ["channel", "topic"]
        }
    },
    {
        "name": "get_permalink",
        "description": "Get a permalink URL for a specific message.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID"
                },
                "message_ts": {
                    "type": "string",
                    "description": "Message timestamp"
                }
            },
            "required": ["channel", "message_ts"]
        }
    },
    {
        "name": "get_conversation_members",
        "description": "Get all members of a channel or conversation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Channel ID"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum members to return (max 1000)",
                    "default": 100
                }
            },
            "required": ["channel"]
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
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "slack",
                    "version": "1.2.0"
                }
            }
        }

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": TOOLS
            }
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Map tool names to functions
        tool_functions = {
            "auth_test": auth_test,
            "list_channels": list_channels,
            "list_conversations": list_conversations,
            "open_conversation": open_conversation,
            "send_message": send_message,
            "get_channel_history": get_channel_history,
            "get_thread_replies": get_thread_replies,
            "search_messages": search_messages,
            "list_users": list_users,
            "get_user_info": get_user_info,
            "add_reaction": add_reaction,
            "remove_reaction": remove_reaction,
            "get_reactions": get_reactions,
            "get_channel_info": get_channel_info,
            "join_channel": join_channel,
            "set_channel_topic": set_channel_topic,
            "get_permalink": get_permalink,
            "get_conversation_members": get_conversation_members
        }

        if tool_name in tool_functions:
            try:
                result = tool_functions[tool_name](**arguments)
            except TypeError as e:
                result = {"success": False, "error": f"Invalid arguments: {e}"}
        else:
            result = {"success": False, "error": f"Unknown tool: {tool_name}"}

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
