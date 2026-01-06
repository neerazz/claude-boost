#!/usr/bin/env python3
"""
Gmail MCP Server

A self-contained MCP server for Gmail operations.
Uses YOUR own OAuth credentials - no external package dependencies.

Environment Variables:
- GOOGLE_OAUTH_CREDENTIALS: Path to your OAuth credentials JSON file
- GMAIL_TOKEN_PATH: (optional) Custom path for token storage

Tools:
- list_messages: List messages in inbox or with query
- get_message: Get full message content
- send_message: Send an email
- reply_to_message: Reply to an existing email thread
- search_messages: Search messages with Gmail query syntax
- list_labels: List all labels
- modify_labels: Add/remove labels from messages
- create_draft: Create a draft email
- delete_message: Delete (trash) a message
- get_thread: Get all messages in a thread
"""

from __future__ import annotations

import json
import sys
import os
import base64
import webbrowser
import http.server
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional, Dict, List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import mimetypes
import socket

# Gmail API endpoints
GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1"
OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify"
]

# Default paths
DEFAULT_CREDENTIALS_PATH = Path(__file__).parent.parent.parent / "google-calendar" / "gcp-oauth.keys.json"
DEFAULT_TOKEN_PATH = Path(__file__).parent.parent / "tokens.json"


class OAuthHandler:
    """Handle OAuth 2.0 flow for Gmail API."""
    
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
        os.chmod(self.token_path, 0o600)
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
            
            if "refresh_token" not in token_data and "refresh_token" in self.token:
                token_data["refresh_token"] = self.token["refresh_token"]
            
            if "expires_in" in token_data:
                token_data["expiry"] = (datetime.now() + timedelta(seconds=token_data["expires_in"])).isoformat()
            
            self._save_token(token_data)
            return True
            
        except Exception as e:
            print(f"Token refresh failed: {e}", file=sys.stderr)
            return False
    
    def _is_token_expired(self) -> bool:
        """Check if the current token is expired."""
        if not self.token:
            return True
        
        if "expiry" not in self.token:
            return False
        
        try:
            expiry = datetime.fromisoformat(self.token["expiry"].replace("Z", "+00:00"))
            return datetime.now(expiry.tzinfo) >= expiry - timedelta(minutes=5)
        except:
            return False
    
    def authorize(self) -> bool:
        """Perform OAuth authorization flow."""
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
                        <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                        <h1>Gmail Authorization Successful!</h1>
                        <p>You can close this window and return to your application.</p>
                        </body></html>
                    """)
                elif "error" in params:
                    server_error[0] = params.get("error_description", params["error"])[0]
                    self.send_response(400)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(f"""
                        <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                        <h1>Authorization Failed</h1><p>Error: {server_error[0]}</p>
                        </body></html>
                    """.encode())
            
            def log_message(self, format, *args):
                pass
        
        server = http.server.HTTPServer(("localhost", port), OAuthCallbackHandler)
        server.timeout = 120
        
        print(f"Opening browser for Gmail authorization...", file=sys.stderr)
        print(f"If browser doesn't open, visit: {auth_url}", file=sys.stderr)
        webbrowser.open(auth_url)
        
        server.handle_request()
        server.server_close()
        
        if server_error[0]:
            raise Exception(f"OAuth error: {server_error[0]}")
        
        if not received_code[0]:
            raise Exception("No authorization code received")
        
        token = self._exchange_code(received_code[0], redirect_uri)
        self._save_token(token)
        
        return True
    
    def get_access_token(self) -> str:
        """Get a valid access token."""
        if self._is_token_expired():
            if not self._refresh_token():
                self.authorize()
        
        if not self.token or "access_token" not in self.token:
            self.authorize()
        
        return self.token["access_token"]


_oauth_handler: Optional[OAuthHandler] = None


def _get_oauth_handler() -> OAuthHandler:
    """Get or create the OAuth handler."""
    global _oauth_handler
    
    if _oauth_handler is None:
        creds_path = Path(os.environ.get("GOOGLE_OAUTH_CREDENTIALS", DEFAULT_CREDENTIALS_PATH))
        token_path = Path(os.environ.get("GMAIL_TOKEN_PATH", DEFAULT_TOKEN_PATH))
        _oauth_handler = OAuthHandler(creds_path, token_path)
    
    return _oauth_handler


def _gmail_api(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    raw_body: Optional[bytes] = None
) -> Dict[str, Any]:
    """Make a Gmail API request."""
    try:
        oauth = _get_oauth_handler()
        access_token = oauth.get_access_token()
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Authentication failed: {e}"}
    
    url = f"{GMAIL_API_BASE}/{endpoint}"
    
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        if raw_body:
            data = raw_body
            headers["Content-Type"] = "message/rfc822"
        elif body:
            data = json.dumps(body).encode()
        else:
            data = None
            
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


def _decode_base64(data: str) -> str:
    """Decode base64url encoded data."""
    try:
        # Add padding if needed
        padded = data + "=" * (4 - len(data) % 4)
        return base64.urlsafe_b64decode(padded).decode('utf-8', errors='replace')
    except:
        return data


def _get_message_body(payload: Dict[str, Any]) -> str:
    """Extract message body from payload."""
    if "body" in payload and payload["body"].get("data"):
        return _decode_base64(payload["body"]["data"])
    
    if "parts" in payload:
        for part in payload["parts"]:
            mime_type = part.get("mimeType", "")
            if mime_type == "text/plain":
                if part.get("body", {}).get("data"):
                    return _decode_base64(part["body"]["data"])
            elif mime_type == "text/html":
                if part.get("body", {}).get("data"):
                    return _decode_base64(part["body"]["data"])
            elif mime_type.startswith("multipart/"):
                body = _get_message_body(part)
                if body:
                    return body
    
    return ""


def _get_header(headers: List[Dict[str, str]], name: str) -> str:
    """Get header value by name."""
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _format_message(msg: Dict[str, Any], include_body: bool = False) -> Dict[str, Any]:
    """Format message for output."""
    payload = msg.get("payload", {})
    headers = payload.get("headers", [])
    
    result = {
        "id": msg.get("id"),
        "thread_id": msg.get("threadId"),
        "label_ids": msg.get("labelIds", []),
        "snippet": msg.get("snippet", ""),
        "subject": _get_header(headers, "Subject"),
        "from": _get_header(headers, "From"),
        "to": _get_header(headers, "To"),
        "cc": _get_header(headers, "Cc"),
        "date": _get_header(headers, "Date"),
        "is_unread": "UNREAD" in msg.get("labelIds", []),
        "is_starred": "STARRED" in msg.get("labelIds", []),
        "size_estimate": msg.get("sizeEstimate", 0)
    }
    
    if include_body:
        result["body"] = _get_message_body(payload)
        result["attachments"] = []
        
        def find_attachments(part: Dict[str, Any]):
            if part.get("filename") and part.get("body", {}).get("attachmentId"):
                result["attachments"].append({
                    "filename": part["filename"],
                    "mime_type": part.get("mimeType"),
                    "size": part.get("body", {}).get("size", 0),
                    "attachment_id": part["body"]["attachmentId"]
                })
            for p in part.get("parts", []):
                find_attachments(p)
        
        find_attachments(payload)
    
    return result


# ============================================================================
# GMAIL TOOLS
# ============================================================================

def list_messages(
    query: str = "",
    max_results: int = 20,
    label_ids: Optional[List[str]] = None,
    include_spam_trash: bool = False
) -> Dict[str, Any]:
    """List messages in the mailbox.
    
    Args:
        query: Gmail search query (e.g., "from:user@example.com", "is:unread", "subject:hello")
        max_results: Maximum number of messages to return (default: 20, max: 500)
        label_ids: Filter by label IDs (e.g., ["INBOX", "UNREAD"])
        include_spam_trash: Include messages from SPAM and TRASH
    """
    params = {
        "maxResults": min(max_results, 500),
        "includeSpamTrash": str(include_spam_trash).lower()
    }
    
    if query:
        params["q"] = query
    
    if label_ids:
        params["labelIds"] = ",".join(label_ids)
    
    result = _gmail_api("users/me/messages", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    messages = []
    for msg in result.get("messages", []):
        # Get message details
        msg_detail = _gmail_api(f"users/me/messages/{msg['id']}", params={"format": "metadata"})
        if "error" not in msg_detail:
            messages.append(_format_message(msg_detail, include_body=False))
    
    return {
        "success": True,
        "messages": messages,
        "count": len(messages),
        "result_size_estimate": result.get("resultSizeEstimate", 0)
    }


def get_message(message_id: str, format: str = "full") -> Dict[str, Any]:
    """Get full message content.
    
    Args:
        message_id: The message ID
        format: Response format - "full", "metadata", "minimal", "raw"
    """
    result = _gmail_api(f"users/me/messages/{message_id}", params={"format": format})
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "message": _format_message(result, include_body=True)
    }


def send_message(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = False
) -> Dict[str, Any]:
    """Send an email.
    
    Args:
        to: Recipient email address(es), comma-separated
        subject: Email subject
        body: Email body (plain text or HTML)
        cc: CC recipients, comma-separated
        bcc: BCC recipients, comma-separated
        html: Whether body is HTML (default: False)
    """
    # Get sender's email
    profile = _gmail_api("users/me/profile")
    if "error" in profile:
        return {"success": False, "error": profile.get("error")}
    
    sender = profile.get("emailAddress", "me")
    
    # Create message
    if html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "html"))
    else:
        msg = MIMEText(body)
    
    msg["to"] = to
    msg["from"] = sender
    msg["subject"] = subject
    
    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    
    # Encode message
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    
    result = _gmail_api("users/me/messages/send", method="POST", body={"raw": raw})
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "message_id": result.get("id"),
        "thread_id": result.get("threadId"),
        "sent_to": to
    }


def reply_to_message(
    message_id: str,
    body: str,
    reply_all: bool = False,
    html: bool = False
) -> Dict[str, Any]:
    """Reply to an existing email thread.
    
    Args:
        message_id: ID of the message to reply to
        body: Reply body
        reply_all: Reply to all recipients (default: False)
        html: Whether body is HTML (default: False)
    """
    # Get original message
    original = _gmail_api(f"users/me/messages/{message_id}", params={"format": "full"})
    if "error" in original:
        return {"success": False, "error": original.get("error")}
    
    payload = original.get("payload", {})
    headers = payload.get("headers", [])
    
    # Get original headers
    orig_from = _get_header(headers, "From")
    orig_to = _get_header(headers, "To")
    orig_cc = _get_header(headers, "Cc")
    orig_subject = _get_header(headers, "Subject")
    orig_message_id = _get_header(headers, "Message-ID")
    thread_id = original.get("threadId")
    
    # Get sender's email
    profile = _gmail_api("users/me/profile")
    if "error" in profile:
        return {"success": False, "error": profile.get("error")}
    sender = profile.get("emailAddress", "me")
    
    # Determine recipients
    to = orig_from
    cc = None
    
    if reply_all:
        # Add original To and Cc, excluding ourselves
        all_recipients = []
        for addr in (orig_to + "," + orig_cc).split(","):
            addr = addr.strip()
            if addr and sender.lower() not in addr.lower():
                all_recipients.append(addr)
        if all_recipients:
            cc = ", ".join(all_recipients)
    
    # Create reply
    if html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "html"))
    else:
        msg = MIMEText(body)
    
    # Add Re: prefix if not present
    if not orig_subject.lower().startswith("re:"):
        orig_subject = f"Re: {orig_subject}"
    
    msg["to"] = to
    msg["from"] = sender
    msg["subject"] = orig_subject
    msg["In-Reply-To"] = orig_message_id
    msg["References"] = orig_message_id
    
    if cc:
        msg["cc"] = cc
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    
    result = _gmail_api("users/me/messages/send", method="POST", body={
        "raw": raw,
        "threadId": thread_id
    })
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "message_id": result.get("id"),
        "thread_id": result.get("threadId"),
        "replied_to": to
    }


def search_messages(
    query: str,
    max_results: int = 20
) -> Dict[str, Any]:
    """Search messages using Gmail query syntax.
    
    Args:
        query: Gmail search query. Examples:
            - "from:user@example.com" - From specific sender
            - "to:user@example.com" - To specific recipient
            - "subject:meeting" - Subject contains word
            - "is:unread" - Unread messages
            - "is:starred" - Starred messages
            - "has:attachment" - Has attachments
            - "after:2024/01/01" - After date
            - "before:2024/12/31" - Before date
            - "label:important" - Has label
            - "in:inbox" - In inbox
        max_results: Maximum results (default: 20)
    """
    return list_messages(query=query, max_results=max_results)


def list_labels() -> Dict[str, Any]:
    """List all labels in the mailbox."""
    result = _gmail_api("users/me/labels")
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    labels = []
    for label in result.get("labels", []):
        labels.append({
            "id": label.get("id"),
            "name": label.get("name"),
            "type": label.get("type"),
            "message_list_visibility": label.get("messageListVisibility"),
            "label_list_visibility": label.get("labelListVisibility")
        })
    
    return {
        "success": True,
        "labels": labels,
        "count": len(labels)
    }


def modify_labels(
    message_id: str,
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Add or remove labels from a message.
    
    Args:
        message_id: The message ID
        add_labels: Label IDs to add (e.g., ["STARRED", "IMPORTANT"])
        remove_labels: Label IDs to remove (e.g., ["UNREAD"])
    """
    body = {}
    if add_labels:
        body["addLabelIds"] = add_labels
    if remove_labels:
        body["removeLabelIds"] = remove_labels
    
    if not body:
        return {"success": False, "error": "Must specify add_labels or remove_labels"}
    
    result = _gmail_api(f"users/me/messages/{message_id}/modify", method="POST", body=body)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "message_id": message_id,
        "label_ids": result.get("labelIds", [])
    }


def create_draft(
    to: str,
    subject: str,
    body: str,
    cc: Optional[str] = None,
    bcc: Optional[str] = None,
    html: bool = False
) -> Dict[str, Any]:
    """Create a draft email.
    
    Args:
        to: Recipient email address(es)
        subject: Email subject
        body: Email body
        cc: CC recipients
        bcc: BCC recipients
        html: Whether body is HTML
    """
    profile = _gmail_api("users/me/profile")
    if "error" in profile:
        return {"success": False, "error": profile.get("error")}
    sender = profile.get("emailAddress", "me")
    
    if html:
        msg = MIMEMultipart("alternative")
        msg.attach(MIMEText(body, "html"))
    else:
        msg = MIMEText(body)
    
    msg["to"] = to
    msg["from"] = sender
    msg["subject"] = subject
    
    if cc:
        msg["cc"] = cc
    if bcc:
        msg["bcc"] = bcc
    
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    
    result = _gmail_api("users/me/drafts", method="POST", body={
        "message": {"raw": raw}
    })
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "draft_id": result.get("id"),
        "message_id": result.get("message", {}).get("id")
    }


def delete_message(message_id: str, permanent: bool = False) -> Dict[str, Any]:
    """Delete (trash) a message.
    
    Args:
        message_id: The message ID
        permanent: If True, permanently delete instead of trash (DANGEROUS)
    """
    if permanent:
        result = _gmail_api(f"users/me/messages/{message_id}", method="DELETE")
    else:
        result = _gmail_api(f"users/me/messages/{message_id}/trash", method="POST")
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "message_id": message_id,
        "action": "permanently deleted" if permanent else "moved to trash"
    }


def get_thread(thread_id: str) -> Dict[str, Any]:
    """Get all messages in a thread.
    
    Args:
        thread_id: The thread ID
    """
    result = _gmail_api(f"users/me/threads/{thread_id}", params={"format": "full"})
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    messages = [_format_message(msg, include_body=True) for msg in result.get("messages", [])]
    
    return {
        "success": True,
        "thread_id": thread_id,
        "messages": messages,
        "count": len(messages)
    }


# ============================================================================
# MCP PROTOCOL IMPLEMENTATION
# ============================================================================

TOOLS = [
    {
        "name": "list_messages",
        "description": "List messages in Gmail inbox or with a search query. Returns message metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query (e.g., 'from:user@example.com', 'is:unread', 'subject:hello')"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of messages (default: 20, max: 500)",
                    "default": 20
                },
                "label_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by label IDs (e.g., ['INBOX', 'UNREAD'])"
                },
                "include_spam_trash": {
                    "type": "boolean",
                    "description": "Include SPAM and TRASH messages",
                    "default": False
                }
            }
        }
    },
    {
        "name": "get_message",
        "description": "Get full content of a specific email message including body and attachments info.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "The message ID"
                },
                "format": {
                    "type": "string",
                    "description": "Response format: 'full', 'metadata', 'minimal', 'raw'",
                    "default": "full"
                }
            },
            "required": ["message_id"]
        }
    },
    {
        "name": "send_message",
        "description": "Send an email message.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address(es), comma-separated"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body content"
                },
                "cc": {
                    "type": "string",
                    "description": "CC recipients, comma-separated"
                },
                "bcc": {
                    "type": "string",
                    "description": "BCC recipients, comma-separated"
                },
                "html": {
                    "type": "boolean",
                    "description": "Whether body is HTML",
                    "default": False
                }
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "reply_to_message",
        "description": "Reply to an existing email thread.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "ID of the message to reply to"
                },
                "body": {
                    "type": "string",
                    "description": "Reply body"
                },
                "reply_all": {
                    "type": "boolean",
                    "description": "Reply to all recipients",
                    "default": False
                },
                "html": {
                    "type": "boolean",
                    "description": "Whether body is HTML",
                    "default": False
                }
            },
            "required": ["message_id", "body"]
        }
    },
    {
        "name": "search_messages",
        "description": "Search messages using Gmail query syntax. Examples: 'from:user@example.com', 'is:unread', 'has:attachment', 'after:2024/01/01'",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Gmail search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 20
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "list_labels",
        "description": "List all Gmail labels in the mailbox.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "modify_labels",
        "description": "Add or remove labels from a message. Use to mark as read/unread, star, etc.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "The message ID"
                },
                "add_labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Label IDs to add (e.g., ['STARRED', 'IMPORTANT'])"
                },
                "remove_labels": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Label IDs to remove (e.g., ['UNREAD'])"
                }
            },
            "required": ["message_id"]
        }
    },
    {
        "name": "create_draft",
        "description": "Create a draft email to be sent later.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address(es)"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body": {
                    "type": "string",
                    "description": "Email body"
                },
                "cc": {
                    "type": "string",
                    "description": "CC recipients"
                },
                "bcc": {
                    "type": "string",
                    "description": "BCC recipients"
                },
                "html": {
                    "type": "boolean",
                    "description": "Whether body is HTML",
                    "default": False
                }
            },
            "required": ["to", "subject", "body"]
        }
    },
    {
        "name": "delete_message",
        "description": "Delete (trash) a message. Use permanent=true for permanent deletion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message_id": {
                    "type": "string",
                    "description": "The message ID"
                },
                "permanent": {
                    "type": "boolean",
                    "description": "Permanently delete instead of trash (DANGEROUS)",
                    "default": False
                }
            },
            "required": ["message_id"]
        }
    },
    {
        "name": "get_thread",
        "description": "Get all messages in an email thread/conversation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "thread_id": {
                    "type": "string",
                    "description": "The thread ID"
                }
            },
            "required": ["thread_id"]
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
                "serverInfo": {"name": "gmail", "version": "1.0.0"}
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
            "list_messages": list_messages,
            "get_message": get_message,
            "send_message": send_message,
            "reply_to_message": reply_to_message,
            "search_messages": search_messages,
            "list_labels": list_labels,
            "modify_labels": modify_labels,
            "create_draft": create_draft,
            "delete_message": delete_message,
            "get_thread": get_thread
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

