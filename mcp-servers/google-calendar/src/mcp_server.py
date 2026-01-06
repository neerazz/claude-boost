#!/usr/bin/env python3
"""
Google Calendar MCP Server

A self-contained MCP server for Google Calendar operations.
Uses YOUR own OAuth credentials - no external package dependencies for auth.

Environment Variables:
- GOOGLE_OAUTH_CREDENTIALS: Path to your OAuth credentials JSON file
- GOOGLE_CALENDAR_TOKEN_PATH: (optional) Custom path for token storage

Tools:
- list_calendars: List all accessible calendars
- list_events: List events from a calendar
- get_event: Get details of a specific event
- create_event: Create a new calendar event
- update_event: Update an existing event
- delete_event: Delete an event
- search_events: Search events by text query
"""

from __future__ import annotations

import json
import sys
import os
import webbrowser
import http.server
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List
import threading
import socket

# Google Calendar API endpoints
CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = ["https://www.googleapis.com/auth/calendar"]

# Default paths
DEFAULT_CREDENTIALS_PATH = Path(__file__).parent.parent / "gcp-oauth.keys.json"
DEFAULT_TOKEN_PATH = Path(__file__).parent.parent / "tokens.json"


class OAuthHandler:
    """Handle OAuth 2.0 flow for Google Calendar API."""
    
    def __init__(self, credentials_path: Path, token_path: Path):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.credentials = self._load_credentials()
        self.token = self._load_token()
    
    def _load_credentials(self) -> Dict[str, Any]:
        """Load OAuth credentials from file."""
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"OAuth credentials file not found: {self.credentials_path}")
        
        with open(self.credentials_path) as f:
            data = json.load(f)
        
        # Handle both "installed" (desktop) and "web" credential types
        if "installed" in data:
            return data["installed"]
        elif "web" in data:
            return data["web"]
        else:
            return data
    
    def _load_token(self) -> Optional[Dict[str, Any]]:
        """Load existing token from file."""
        if not self.token_path.exists():
            return None
        
        try:
            with open(self.token_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    
    def _save_token(self, token: Dict[str, Any]):
        """Save token to file."""
        self.token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_path, "w") as f:
            json.dump(token, f, indent=2)
        os.chmod(self.token_path, 0o600)  # Secure permissions
        self.token = token
    
    def _find_free_port(self) -> int:
        """Find a free port for the OAuth callback server."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', 0))
            return s.getsockname()[1]
    
    def _exchange_code(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """Exchange authorization code for tokens."""
        data = urllib.parse.urlencode({
            "code": code,
            "client_id": self.credentials["client_id"],
            "client_secret": self.credentials["client_secret"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }).encode()
        
        req = urllib.request.Request(OAUTH_TOKEN_URL, data=data, method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
        
        with urllib.request.urlopen(req, timeout=30) as response:
            token_data = json.loads(response.read().decode())
        
        # Add expiry timestamp
        if "expires_in" in token_data:
            token_data["expiry"] = (datetime.now() + timedelta(seconds=token_data["expires_in"])).isoformat()
        
        return token_data
    
    def _refresh_token(self) -> bool:
        """Refresh the access token using refresh token."""
        if not self.token or "refresh_token" not in self.token:
            return False
        
        try:
            data = urllib.parse.urlencode({
                "refresh_token": self.token["refresh_token"],
                "client_id": self.credentials["client_id"],
                "client_secret": self.credentials["client_secret"],
                "grant_type": "refresh_token"
            }).encode()
            
            req = urllib.request.Request(OAUTH_TOKEN_URL, data=data, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            
            with urllib.request.urlopen(req, timeout=30) as response:
                token_data = json.loads(response.read().decode())
            
            # Preserve refresh token if not returned
            if "refresh_token" not in token_data and "refresh_token" in self.token:
                token_data["refresh_token"] = self.token["refresh_token"]
            
            # Add expiry timestamp
            if "expires_in" in token_data:
                token_data["expiry"] = (datetime.now() + timedelta(seconds=token_data["expires_in"])).isoformat()
            
            self._save_token(token_data)
            return True
            
        except Exception as e:
            print(f"Token refresh failed: {e}", file=sys.stderr)
            return False
    
    def _is_token_expired(self) -> bool:
        """Check if the current token is expired or about to expire."""
        if not self.token:
            return True
        
        if "expiry" not in self.token:
            return False  # Assume valid if no expiry
        
        try:
            expiry = datetime.fromisoformat(self.token["expiry"].replace("Z", "+00:00"))
            # Consider expired if less than 5 minutes remaining
            return datetime.now(expiry.tzinfo) >= expiry - timedelta(minutes=5)
        except:
            return False
    
    def authorize(self) -> bool:
        """
        Perform OAuth authorization flow.
        Returns True if authorization was successful.
        """
        port = self._find_free_port()
        redirect_uri = f"http://localhost:{port}"
        
        auth_params = {
            "client_id": self.credentials["client_id"],
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent"
        }
        
        auth_url = f"{OAUTH_AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
        
        # Store received code
        received_code = [None]
        server_error = [None]
        
        class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                
                if "code" in params:
                    received_code[0] = params["code"][0]
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(b"""
                        <html>
                        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                        <h1>Authorization Successful!</h1>
                        <p>You can close this window and return to your application.</p>
                        </body>
                        </html>
                    """)
                elif "error" in params:
                    server_error[0] = params.get("error_description", params["error"])[0]
                    self.send_response(400)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(f"""
                        <html>
                        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                        <h1>Authorization Failed</h1>
                        <p>Error: {server_error[0]}</p>
                        </body>
                        </html>
                    """.encode())
                else:
                    self.send_response(400)
                    self.end_headers()
            
            def log_message(self, format, *args):
                pass  # Suppress logs
        
        # Start callback server
        server = http.server.HTTPServer(("localhost", port), OAuthCallbackHandler)
        server.timeout = 120  # 2 minute timeout
        
        # Open browser for auth
        print(f"Opening browser for Google Calendar authorization...", file=sys.stderr)
        print(f"If browser doesn't open, visit: {auth_url}", file=sys.stderr)
        webbrowser.open(auth_url)
        
        # Wait for callback
        server.handle_request()
        server.server_close()
        
        if server_error[0]:
            raise Exception(f"OAuth error: {server_error[0]}")
        
        if not received_code[0]:
            raise Exception("No authorization code received")
        
        # Exchange code for token
        token = self._exchange_code(received_code[0], redirect_uri)
        self._save_token(token)
        
        return True
    
    def get_access_token(self) -> str:
        """Get a valid access token, refreshing or re-authorizing if needed."""
        # Check if we need to refresh or authorize
        if self._is_token_expired():
            if not self._refresh_token():
                # Refresh failed, need to re-authorize
                self.authorize()
        
        if not self.token or "access_token" not in self.token:
            self.authorize()
        
        return self.token["access_token"]


# Global OAuth handler
_oauth_handler: Optional[OAuthHandler] = None


def _get_oauth_handler() -> OAuthHandler:
    """Get or create the OAuth handler."""
    global _oauth_handler
    
    if _oauth_handler is None:
        creds_path = Path(os.environ.get("GOOGLE_OAUTH_CREDENTIALS", DEFAULT_CREDENTIALS_PATH))
        token_path = Path(os.environ.get("GOOGLE_CALENDAR_TOKEN_PATH", DEFAULT_TOKEN_PATH))
        _oauth_handler = OAuthHandler(creds_path, token_path)
    
    return _oauth_handler


def _calendar_api(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make a Google Calendar API request."""
    try:
        oauth = _get_oauth_handler()
        access_token = oauth.get_access_token()
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Authentication failed: {e}"}
    
    url = f"{CALENDAR_API_BASE}/{endpoint}"
    
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = response.read().decode()
            if response_data:
                return json.loads(response_data)
            return {"success": True}
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        try:
            error_data = json.loads(error_body)
            error_msg = error_data.get("error", {}).get("message", str(e))
        except:
            error_msg = error_body or str(e)
        return {"success": False, "error": f"API Error ({e.code}): {error_msg}"}
    
    except urllib.error.URLError as e:
        return {"success": False, "error": f"Network error: {e.reason}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def _parse_datetime(dt_obj: Dict[str, Any]) -> str:
    """Parse Google Calendar datetime object to readable string."""
    if "dateTime" in dt_obj:
        return dt_obj["dateTime"]
    elif "date" in dt_obj:
        return dt_obj["date"]
    return ""


def _format_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Format event for output."""
    return {
        "id": event.get("id"),
        "summary": event.get("summary", "(No title)"),
        "description": event.get("description", ""),
        "location": event.get("location", ""),
        "start": _parse_datetime(event.get("start", {})),
        "end": _parse_datetime(event.get("end", {})),
        "status": event.get("status"),
        "html_link": event.get("htmlLink"),
        "creator": event.get("creator", {}).get("email"),
        "organizer": event.get("organizer", {}).get("email"),
        "attendees": [
            {
                "email": a.get("email"),
                "name": a.get("displayName"),
                "response_status": a.get("responseStatus"),
                "optional": a.get("optional", False)
            }
            for a in event.get("attendees", [])
        ],
        "recurrence": event.get("recurrence"),
        "conference_data": event.get("conferenceData", {}).get("entryPoints", [])
    }


# ============================================================================
# CALENDAR TOOLS
# ============================================================================

def list_calendars() -> Dict[str, Any]:
    """List all accessible calendars."""
    result = _calendar_api("users/me/calendarList")
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    calendars = []
    for cal in result.get("items", []):
        calendars.append({
            "id": cal.get("id"),
            "summary": cal.get("summary"),
            "description": cal.get("description", ""),
            "primary": cal.get("primary", False),
            "access_role": cal.get("accessRole"),
            "background_color": cal.get("backgroundColor"),
            "time_zone": cal.get("timeZone")
        })
    
    return {
        "success": True,
        "calendars": calendars,
        "count": len(calendars)
    }


def list_events(
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 50,
    single_events: bool = True,
    order_by: str = "startTime"
) -> Dict[str, Any]:
    """List events from a calendar.
    
    Args:
        calendar_id: Calendar ID (default: "primary")
        time_min: Start time in ISO format (default: now)
        time_max: End time in ISO format
        max_results: Maximum number of events (default: 50)
        single_events: Expand recurring events (default: True)
        order_by: Order by "startTime" or "updated"
    """
    if not time_min:
        time_min = datetime.utcnow().isoformat() + "Z"
    
    params = {
        "timeMin": time_min,
        "maxResults": min(max_results, 2500),
        "singleEvents": str(single_events).lower(),
        "orderBy": order_by
    }
    
    if time_max:
        params["timeMax"] = time_max
    
    result = _calendar_api(f"calendars/{urllib.parse.quote(calendar_id)}/events", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    events = [_format_event(e) for e in result.get("items", [])]
    
    return {
        "success": True,
        "calendar_id": calendar_id,
        "events": events,
        "count": len(events),
        "time_zone": result.get("timeZone")
    }


def get_event(calendar_id: str, event_id: str) -> Dict[str, Any]:
    """Get details of a specific event.
    
    Args:
        calendar_id: Calendar ID
        event_id: Event ID
    """
    result = _calendar_api(f"calendars/{urllib.parse.quote(calendar_id)}/events/{urllib.parse.quote(event_id)}")
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "event": _format_event(result)
    }


def create_event(
    summary: str,
    start: str,
    end: str,
    calendar_id: str = "primary",
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    time_zone: Optional[str] = None,
    all_day: bool = False,
    reminders: Optional[List[Dict[str, Any]]] = None,
    conference: bool = False
) -> Dict[str, Any]:
    """Create a new calendar event.
    
    Args:
        summary: Event title
        start: Start time (ISO format for timed events, YYYY-MM-DD for all-day)
        end: End time (ISO format for timed events, YYYY-MM-DD for all-day)
        calendar_id: Calendar ID (default: "primary")
        description: Event description
        location: Event location
        attendees: List of attendee email addresses
        time_zone: Time zone (e.g., "America/Los_Angeles")
        all_day: Whether this is an all-day event
        reminders: Custom reminders [{"method": "popup/email", "minutes": N}]
        conference: Add Google Meet conference
    """
    event_body: Dict[str, Any] = {
        "summary": summary
    }
    
    # Handle start/end times
    if all_day:
        event_body["start"] = {"date": start}
        event_body["end"] = {"date": end}
    else:
        event_body["start"] = {"dateTime": start}
        event_body["end"] = {"dateTime": end}
        if time_zone:
            event_body["start"]["timeZone"] = time_zone
            event_body["end"]["timeZone"] = time_zone
    
    if description:
        event_body["description"] = description
    
    if location:
        event_body["location"] = location
    
    if attendees:
        event_body["attendees"] = [{"email": email} for email in attendees]
    
    if reminders:
        event_body["reminders"] = {
            "useDefault": False,
            "overrides": reminders
        }
    
    if conference:
        event_body["conferenceData"] = {
            "createRequest": {
                "requestId": f"meet-{datetime.now().timestamp()}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"}
            }
        }
    
    params = {}
    if conference:
        params["conferenceDataVersion"] = "1"
    
    result = _calendar_api(
        f"calendars/{urllib.parse.quote(calendar_id)}/events",
        method="POST",
        params=params if params else None,
        body=event_body
    )
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "event": _format_event(result),
        "message": f"Event '{summary}' created successfully"
    }


def update_event(
    calendar_id: str,
    event_id: str,
    summary: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    description: Optional[str] = None,
    location: Optional[str] = None,
    attendees: Optional[List[str]] = None,
    time_zone: Optional[str] = None,
    all_day: Optional[bool] = None
) -> Dict[str, Any]:
    """Update an existing event.
    
    Args:
        calendar_id: Calendar ID
        event_id: Event ID to update
        summary: New event title
        start: New start time
        end: New end time
        description: New description
        location: New location
        attendees: New list of attendee emails
        time_zone: Time zone
        all_day: Whether this is an all-day event
    """
    # First get the existing event
    existing = _calendar_api(
        f"calendars/{urllib.parse.quote(calendar_id)}/events/{urllib.parse.quote(event_id)}"
    )
    
    if "error" in existing:
        return {"success": False, "error": existing.get("error")}
    
    # Update fields
    if summary is not None:
        existing["summary"] = summary
    
    if description is not None:
        existing["description"] = description
    
    if location is not None:
        existing["location"] = location
    
    if attendees is not None:
        existing["attendees"] = [{"email": email} for email in attendees]
    
    if start is not None:
        if all_day:
            existing["start"] = {"date": start}
        else:
            existing["start"] = {"dateTime": start}
            if time_zone:
                existing["start"]["timeZone"] = time_zone
    
    if end is not None:
        if all_day:
            existing["end"] = {"date": end}
        else:
            existing["end"] = {"dateTime": end}
            if time_zone:
                existing["end"]["timeZone"] = time_zone
    
    result = _calendar_api(
        f"calendars/{urllib.parse.quote(calendar_id)}/events/{urllib.parse.quote(event_id)}",
        method="PUT",
        body=existing
    )
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "event": _format_event(result),
        "message": "Event updated successfully"
    }


def delete_event(calendar_id: str, event_id: str) -> Dict[str, Any]:
    """Delete an event.
    
    Args:
        calendar_id: Calendar ID
        event_id: Event ID to delete
    """
    result = _calendar_api(
        f"calendars/{urllib.parse.quote(calendar_id)}/events/{urllib.parse.quote(event_id)}",
        method="DELETE"
    )
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "message": f"Event {event_id} deleted successfully"
    }


def search_events(
    query: str,
    calendar_id: str = "primary",
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
    max_results: int = 50
) -> Dict[str, Any]:
    """Search events by text query.
    
    Args:
        query: Search text (matches summary, description, location, attendees)
        calendar_id: Calendar ID (default: "primary")
        time_min: Start time boundary
        time_max: End time boundary
        max_results: Maximum results
    """
    if not time_min:
        time_min = datetime.utcnow().isoformat() + "Z"
    
    params = {
        "q": query,
        "timeMin": time_min,
        "maxResults": min(max_results, 2500),
        "singleEvents": "true",
        "orderBy": "startTime"
    }
    
    if time_max:
        params["timeMax"] = time_max
    
    result = _calendar_api(f"calendars/{urllib.parse.quote(calendar_id)}/events", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    events = [_format_event(e) for e in result.get("items", [])]
    
    return {
        "success": True,
        "query": query,
        "calendar_id": calendar_id,
        "events": events,
        "count": len(events)
    }


def get_free_busy(
    time_min: str,
    time_max: str,
    calendar_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Get free/busy information for calendars.
    
    Args:
        time_min: Start of time range (ISO format)
        time_max: End of time range (ISO format)
        calendar_ids: List of calendar IDs (default: ["primary"])
    """
    if not calendar_ids:
        calendar_ids = ["primary"]
    
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": cal_id} for cal_id in calendar_ids]
    }
    
    result = _calendar_api("freeBusy", method="POST", body=body)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    calendars = {}
    for cal_id, cal_data in result.get("calendars", {}).items():
        busy_times = []
        for busy in cal_data.get("busy", []):
            busy_times.append({
                "start": busy.get("start"),
                "end": busy.get("end")
            })
        calendars[cal_id] = {
            "busy": busy_times,
            "errors": cal_data.get("errors", [])
        }
    
    return {
        "success": True,
        "time_min": time_min,
        "time_max": time_max,
        "calendars": calendars
    }


# ============================================================================
# MCP PROTOCOL IMPLEMENTATION
# ============================================================================

TOOLS = [
    {
        "name": "list_calendars",
        "description": "List all accessible Google Calendars for the user.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "list_events",
        "description": "List events from a Google Calendar. Defaults to primary calendar and events from now onwards.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "calendar_id": {
                    "type": "string",
                    "description": "Calendar ID (default: 'primary')",
                    "default": "primary"
                },
                "time_min": {
                    "type": "string",
                    "description": "Start time in ISO format (default: now). Example: 2024-01-01T00:00:00Z"
                },
                "time_max": {
                    "type": "string",
                    "description": "End time in ISO format. Example: 2024-12-31T23:59:59Z"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of events to return (default: 50)",
                    "default": 50
                },
                "single_events": {
                    "type": "boolean",
                    "description": "Expand recurring events into individual instances (default: true)",
                    "default": True
                },
                "order_by": {
                    "type": "string",
                    "description": "Order by 'startTime' or 'updated'",
                    "default": "startTime"
                }
            }
        }
    },
    {
        "name": "get_event",
        "description": "Get details of a specific calendar event.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "calendar_id": {
                    "type": "string",
                    "description": "Calendar ID"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID to retrieve"
                }
            },
            "required": ["calendar_id", "event_id"]
        }
    },
    {
        "name": "create_event",
        "description": "Create a new calendar event. Use ISO format for times (e.g., 2024-01-15T10:00:00-08:00) or YYYY-MM-DD for all-day events.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "Event title"
                },
                "start": {
                    "type": "string",
                    "description": "Start time (ISO format) or date (YYYY-MM-DD for all-day)"
                },
                "end": {
                    "type": "string",
                    "description": "End time (ISO format) or date (YYYY-MM-DD for all-day)"
                },
                "calendar_id": {
                    "type": "string",
                    "description": "Calendar ID (default: 'primary')",
                    "default": "primary"
                },
                "description": {
                    "type": "string",
                    "description": "Event description"
                },
                "location": {
                    "type": "string",
                    "description": "Event location"
                },
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of attendee email addresses"
                },
                "time_zone": {
                    "type": "string",
                    "description": "Time zone (e.g., 'America/Los_Angeles')"
                },
                "all_day": {
                    "type": "boolean",
                    "description": "Whether this is an all-day event",
                    "default": False
                },
                "conference": {
                    "type": "boolean",
                    "description": "Add Google Meet conference link",
                    "default": False
                }
            },
            "required": ["summary", "start", "end"]
        }
    },
    {
        "name": "update_event",
        "description": "Update an existing calendar event. Only specified fields will be updated.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "calendar_id": {
                    "type": "string",
                    "description": "Calendar ID"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID to update"
                },
                "summary": {
                    "type": "string",
                    "description": "New event title"
                },
                "start": {
                    "type": "string",
                    "description": "New start time"
                },
                "end": {
                    "type": "string",
                    "description": "New end time"
                },
                "description": {
                    "type": "string",
                    "description": "New description"
                },
                "location": {
                    "type": "string",
                    "description": "New location"
                },
                "attendees": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "New list of attendee emails"
                },
                "time_zone": {
                    "type": "string",
                    "description": "Time zone"
                }
            },
            "required": ["calendar_id", "event_id"]
        }
    },
    {
        "name": "delete_event",
        "description": "Delete a calendar event.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "calendar_id": {
                    "type": "string",
                    "description": "Calendar ID"
                },
                "event_id": {
                    "type": "string",
                    "description": "Event ID to delete"
                }
            },
            "required": ["calendar_id", "event_id"]
        }
    },
    {
        "name": "search_events",
        "description": "Search events by text query. Searches summary, description, location, and attendees.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search text"
                },
                "calendar_id": {
                    "type": "string",
                    "description": "Calendar ID (default: 'primary')",
                    "default": "primary"
                },
                "time_min": {
                    "type": "string",
                    "description": "Start time boundary (ISO format)"
                },
                "time_max": {
                    "type": "string",
                    "description": "End time boundary (ISO format)"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 50
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_free_busy",
        "description": "Get free/busy information for calendars in a time range.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "time_min": {
                    "type": "string",
                    "description": "Start of time range (ISO format)"
                },
                "time_max": {
                    "type": "string",
                    "description": "End of time range (ISO format)"
                },
                "calendar_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of calendar IDs (default: ['primary'])"
                }
            },
            "required": ["time_min", "time_max"]
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
                    "name": "google-calendar",
                    "version": "1.0.0"
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
            "list_calendars": list_calendars,
            "list_events": list_events,
            "get_event": get_event,
            "create_event": create_event,
            "update_event": update_event,
            "delete_event": delete_event,
            "search_events": search_events,
            "get_free_busy": get_free_busy
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

