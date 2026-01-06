#!/usr/bin/env python3
"""
Google Drive MCP Server

A self-contained MCP server for Google Drive operations.
Uses YOUR own OAuth credentials - no external package dependencies.

Environment Variables:
- GOOGLE_OAUTH_CREDENTIALS: Path to your OAuth credentials JSON file
- GOOGLE_DRIVE_TOKEN_PATH: (optional) Custom path for token storage

Tools:
- list_files: List files and folders
- get_file: Get file metadata
- search_files: Search for files
- read_file: Read file content (text files, Google Docs/Sheets/Slides)
- create_file: Create a new file
- create_folder: Create a new folder
- update_file: Update file content
- delete_file: Delete a file (trash or permanent)
- move_file: Move file to a different folder
- copy_file: Copy a file
- share_file: Share a file with users
- get_file_permissions: Get file sharing permissions
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
import socket
import mimetypes

# Google Drive API endpoints
DRIVE_API_BASE = "https://www.googleapis.com/drive/v3"
DRIVE_UPLOAD_BASE = "https://www.googleapis.com/upload/drive/v3"
OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive.metadata.readonly"
]

# MIME type mappings for Google Workspace files
GOOGLE_MIME_TYPES = {
    "application/vnd.google-apps.document": {"export": "text/plain", "extension": ".txt"},
    "application/vnd.google-apps.spreadsheet": {"export": "text/csv", "extension": ".csv"},
    "application/vnd.google-apps.presentation": {"export": "text/plain", "extension": ".txt"},
    "application/vnd.google-apps.drawing": {"export": "image/png", "extension": ".png"},
}

# Default paths
DEFAULT_CREDENTIALS_PATH = Path(__file__).parent.parent.parent / "google-calendar" / "gcp-oauth.keys.json"
DEFAULT_TOKEN_PATH = Path(__file__).parent.parent / "tokens.json"


class OAuthHandler:
    """Handle OAuth 2.0 flow for Google Drive API."""
    
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
                        <h1>Google Drive Authorization Successful!</h1>
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
        
        print(f"Opening browser for Google Drive authorization...", file=sys.stderr)
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
        token_path = Path(os.environ.get("GOOGLE_DRIVE_TOKEN_PATH", DEFAULT_TOKEN_PATH))
        _oauth_handler = OAuthHandler(creds_path, token_path)
    
    return _oauth_handler


def _drive_api(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    raw_response: bool = False,
    upload: bool = False,
    file_content: Optional[bytes] = None,
    content_type: Optional[str] = None
) -> Any:
    """Make a Google Drive API request."""
    try:
        oauth = _get_oauth_handler()
        access_token = oauth.get_access_token()
    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Authentication failed: {e}"}
    
    base = DRIVE_UPLOAD_BASE if upload else DRIVE_API_BASE
    url = f"{base}/{endpoint}"
    
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        data = None
        
        if upload and file_content:
            # Multipart upload for file with metadata
            if body:
                boundary = "===boundary==="
                headers["Content-Type"] = f"multipart/related; boundary={boundary}"
                
                parts = []
                parts.append(f"--{boundary}")
                parts.append("Content-Type: application/json; charset=UTF-8")
                parts.append("")
                parts.append(json.dumps(body))
                parts.append(f"--{boundary}")
                parts.append(f"Content-Type: {content_type or 'application/octet-stream'}")
                parts.append("")
                
                data = "\r\n".join(parts).encode() + b"\r\n" + file_content + f"\r\n--{boundary}--".encode()
            else:
                headers["Content-Type"] = content_type or "application/octet-stream"
                data = file_content
        elif body:
            headers["Content-Type"] = "application/json"
            data = json.dumps(body).encode()
        
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        
        with urllib.request.urlopen(req, timeout=60) as response:
            response_data = response.read()
            if raw_response:
                return response_data
            if response_data:
                return json.loads(response_data.decode())
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


def _format_file(file: Dict[str, Any]) -> Dict[str, Any]:
    """Format file metadata for output."""
    return {
        "id": file.get("id"),
        "name": file.get("name"),
        "mime_type": file.get("mimeType"),
        "size": file.get("size"),
        "created_time": file.get("createdTime"),
        "modified_time": file.get("modifiedTime"),
        "parents": file.get("parents", []),
        "web_view_link": file.get("webViewLink"),
        "web_content_link": file.get("webContentLink"),
        "owners": [o.get("emailAddress") for o in file.get("owners", [])],
        "shared": file.get("shared", False),
        "starred": file.get("starred", False),
        "trashed": file.get("trashed", False),
        "is_folder": file.get("mimeType") == "application/vnd.google-apps.folder",
        "drive_id": file.get("driveId"),  # Shared Drive ID (None for My Drive)
    }


# ============================================================================
# GOOGLE DRIVE TOOLS
# ============================================================================

def list_files(
    folder_id: Optional[str] = None,
    query: Optional[str] = None,
    max_results: int = 50,
    order_by: str = "modifiedTime desc",
    include_trashed: bool = False
) -> Dict[str, Any]:
    """List files and folders.
    
    Args:
        folder_id: Folder ID to list contents of (default: root)
        query: Additional query filter
        max_results: Maximum files to return (default: 50)
        order_by: Sort order (e.g., "name", "modifiedTime desc")
        include_trashed: Include trashed files
    """
    q_parts = []
    
    if folder_id:
        q_parts.append(f"'{folder_id}' in parents")
    
    if not include_trashed:
        q_parts.append("trashed = false")
    
    if query:
        q_parts.append(query)
    
    params = {
        "pageSize": min(max_results, 1000),
        "orderBy": order_by,
        "fields": "files(id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink,webContentLink,owners,shared,starred,trashed,driveId)",
        # Support Shared Drives (Team Drives)
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
    }
    
    if q_parts:
        params["q"] = " and ".join(q_parts)
    
    result = _drive_api("files", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    files = [_format_file(f) for f in result.get("files", [])]
    
    return {
        "success": True,
        "files": files,
        "count": len(files)
    }


def get_file(file_id: str) -> Dict[str, Any]:
    """Get file metadata.
    
    Args:
        file_id: The file ID
    """
    params = {
        "fields": "id,name,mimeType,size,createdTime,modifiedTime,parents,webViewLink,webContentLink,owners,shared,starred,trashed,description,driveId",
        # Support Shared Drives (Team Drives)
        "supportsAllDrives": "true",
    }
    
    result = _drive_api(f"files/{file_id}", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "file": _format_file(result)
    }


def search_files(
    query: str,
    max_results: int = 50,
    file_type: Optional[str] = None
) -> Dict[str, Any]:
    """Search for files.
    
    Args:
        query: Search query (searches name and content)
        max_results: Maximum results
        file_type: Filter by type: "folder", "document", "spreadsheet", "presentation", "pdf", "image"
    """
    q_parts = [f"fullText contains '{query}'", "trashed = false"]
    
    type_map = {
        "folder": "mimeType = 'application/vnd.google-apps.folder'",
        "document": "mimeType = 'application/vnd.google-apps.document'",
        "spreadsheet": "mimeType = 'application/vnd.google-apps.spreadsheet'",
        "presentation": "mimeType = 'application/vnd.google-apps.presentation'",
        "pdf": "mimeType = 'application/pdf'",
        "image": "mimeType contains 'image/'"
    }
    
    if file_type and file_type in type_map:
        q_parts.append(type_map[file_type])
    
    params = {
        "q": " and ".join(q_parts),
        "pageSize": min(max_results, 1000),
        "fields": "files(id,name,mimeType,size,modifiedTime,webViewLink,owners,driveId)",
        # Support Shared Drives (Team Drives)
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
    }
    
    result = _drive_api("files", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    files = [_format_file(f) for f in result.get("files", [])]
    
    return {
        "success": True,
        "query": query,
        "files": files,
        "count": len(files)
    }


def read_file(file_id: str, max_size: int = 1000000) -> Dict[str, Any]:
    """Read file content.
    
    Args:
        file_id: The file ID
        max_size: Maximum content size to return (default: 1MB)
    
    Note: For Google Docs/Sheets/Slides, exports as plain text/CSV.
          For binary files, returns base64 encoded content.
    """
    # First get file metadata (with Shared Drive support)
    meta_result = _drive_api(f"files/{file_id}", params={
        "fields": "id,name,mimeType,size",
        "supportsAllDrives": "true",
    })
    
    if "error" in meta_result:
        return {"success": False, "error": meta_result.get("error")}
    
    mime_type = meta_result.get("mimeType", "")
    name = meta_result.get("name", "")
    size = int(meta_result.get("size", 0))
    
    # Check size
    if size > max_size:
        return {
            "success": False,
            "error": f"File too large ({size} bytes). Max: {max_size} bytes"
        }
    
    # Handle Google Workspace files
    if mime_type in GOOGLE_MIME_TYPES:
        export_type = GOOGLE_MIME_TYPES[mime_type]["export"]
        content = _drive_api(
            f"files/{file_id}/export",
            params={"mimeType": export_type},
            raw_response=True
        )
        
        if isinstance(content, dict) and "error" in content:
            return {"success": False, "error": content.get("error")}
        
        try:
            text_content = content.decode('utf-8')
            return {
                "success": True,
                "file_id": file_id,
                "name": name,
                "mime_type": mime_type,
                "exported_as": export_type,
                "content": text_content,
                "encoding": "utf-8"
            }
        except:
            return {
                "success": True,
                "file_id": file_id,
                "name": name,
                "mime_type": mime_type,
                "exported_as": export_type,
                "content": base64.b64encode(content).decode(),
                "encoding": "base64"
            }
    
    # Handle regular files
    content = _drive_api(f"files/{file_id}", params={"alt": "media"}, raw_response=True)
    
    if isinstance(content, dict) and "error" in content:
        return {"success": False, "error": content.get("error")}
    
    # Try to decode as text
    if mime_type.startswith("text/") or mime_type in ["application/json", "application/xml"]:
        try:
            text_content = content.decode('utf-8')
            return {
                "success": True,
                "file_id": file_id,
                "name": name,
                "mime_type": mime_type,
                "content": text_content,
                "encoding": "utf-8"
            }
        except:
            pass
    
    # Return as base64 for binary files
    return {
        "success": True,
        "file_id": file_id,
        "name": name,
        "mime_type": mime_type,
        "content": base64.b64encode(content).decode(),
        "encoding": "base64",
        "size": len(content)
    }


def create_file(
    name: str,
    content: str,
    parent_id: Optional[str] = None,
    mime_type: str = "text/plain",
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new file.
    
    Args:
        name: File name
        content: File content (text)
        parent_id: Parent folder ID (default: root)
        mime_type: MIME type (default: text/plain)
        description: File description
    """
    metadata = {"name": name}
    
    if parent_id:
        metadata["parents"] = [parent_id]
    
    if description:
        metadata["description"] = description
    
    result = _drive_api(
        "files",
        method="POST",
        params={"uploadType": "multipart"},
        body=metadata,
        upload=True,
        file_content=content.encode('utf-8'),
        content_type=mime_type
    )
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "file": _format_file(result),
        "message": f"Created file '{name}'"
    }


def create_folder(
    name: str,
    parent_id: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new folder.
    
    Args:
        name: Folder name
        parent_id: Parent folder ID (default: root)
        description: Folder description
    """
    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    
    if parent_id:
        metadata["parents"] = [parent_id]
    
    if description:
        metadata["description"] = description
    
    result = _drive_api("files", method="POST", body=metadata)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "folder": _format_file(result),
        "message": f"Created folder '{name}'"
    }


def update_file(
    file_id: str,
    content: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Update file content or metadata.
    
    Args:
        file_id: The file ID
        content: New file content
        name: New file name
        description: New description
    """
    if content:
        # Update content (with Shared Drive support)
        result = _drive_api(
            f"files/{file_id}",
            method="PATCH",
            params={"uploadType": "media", "supportsAllDrives": "true"},
            upload=True,
            file_content=content.encode('utf-8'),
            content_type="text/plain"
        )
    else:
        # Update metadata only (with Shared Drive support)
        metadata = {}
        if name:
            metadata["name"] = name
        if description:
            metadata["description"] = description
        
        if not metadata:
            return {"success": False, "error": "No updates specified"}
        
        result = _drive_api(f"files/{file_id}", method="PATCH", params={"supportsAllDrives": "true"}, body=metadata)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "file": _format_file(result),
        "message": "File updated"
    }


def delete_file(file_id: str, permanent: bool = False) -> Dict[str, Any]:
    """Delete a file.
    
    Args:
        file_id: The file ID
        permanent: Permanently delete instead of trash (DANGEROUS)
    """
    if permanent:
        result = _drive_api(f"files/{file_id}", method="DELETE", params={"supportsAllDrives": "true"})
    else:
        result = _drive_api(f"files/{file_id}", method="PATCH", params={"supportsAllDrives": "true"}, body={"trashed": True})
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "file_id": file_id,
        "action": "permanently deleted" if permanent else "moved to trash"
    }


def move_file(file_id: str, new_parent_id: str) -> Dict[str, Any]:
    """Move file to a different folder.
    
    Args:
        file_id: The file ID
        new_parent_id: New parent folder ID
    """
    # Get current parents (with Shared Drive support)
    current = _drive_api(f"files/{file_id}", params={"fields": "parents", "supportsAllDrives": "true"})
    if "error" in current:
        return {"success": False, "error": current.get("error")}
    
    current_parents = ",".join(current.get("parents", []))
    
    result = _drive_api(
        f"files/{file_id}",
        method="PATCH",
        params={
            "addParents": new_parent_id,
            "removeParents": current_parents,
            "supportsAllDrives": "true",
        }
    )
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "file_id": file_id,
        "new_parent_id": new_parent_id,
        "message": "File moved successfully"
    }


def copy_file(
    file_id: str,
    new_name: Optional[str] = None,
    parent_id: Optional[str] = None
) -> Dict[str, Any]:
    """Copy a file.
    
    Args:
        file_id: The file ID to copy
        new_name: Name for the copy (default: "Copy of {original}")
        parent_id: Parent folder for the copy
    """
    body = {}
    if new_name:
        body["name"] = new_name
    if parent_id:
        body["parents"] = [parent_id]
    
    result = _drive_api(f"files/{file_id}/copy", method="POST", params={"supportsAllDrives": "true"}, body=body if body else None)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "original_id": file_id,
        "copy": _format_file(result)
    }


def share_file(
    file_id: str,
    email: str,
    role: str = "reader",
    notify: bool = True,
    message: Optional[str] = None
) -> Dict[str, Any]:
    """Share a file with a user.
    
    Args:
        file_id: The file ID
        email: Email address to share with
        role: Permission role - "reader", "writer", "commenter"
        notify: Send notification email
        message: Custom message for notification
    """
    body = {
        "type": "user",
        "role": role,
        "emailAddress": email
    }
    
    params = {
        "sendNotificationEmail": str(notify).lower(),
        "supportsAllDrives": "true",
    }
    
    if message:
        params["emailMessage"] = message
    
    result = _drive_api(f"files/{file_id}/permissions", method="POST", params=params, body=body)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "file_id": file_id,
        "shared_with": email,
        "role": role,
        "permission_id": result.get("id")
    }


def get_file_permissions(file_id: str) -> Dict[str, Any]:
    """Get file sharing permissions.
    
    Args:
        file_id: The file ID
    """
    result = _drive_api(
        f"files/{file_id}/permissions",
        params={
            "fields": "permissions(id,type,role,emailAddress,displayName)",
            "supportsAllDrives": "true",
        }
    )
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    permissions = []
    for p in result.get("permissions", []):
        permissions.append({
            "id": p.get("id"),
            "type": p.get("type"),
            "role": p.get("role"),
            "email": p.get("emailAddress"),
            "name": p.get("displayName")
        })
    
    return {
        "success": True,
        "file_id": file_id,
        "permissions": permissions,
        "count": len(permissions)
    }


# ============================================================================
# MCP PROTOCOL IMPLEMENTATION
# ============================================================================

TOOLS = [
    {
        "name": "list_files",
        "description": "List files and folders in Google Drive. Can filter by folder.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "folder_id": {
                    "type": "string",
                    "description": "Folder ID to list contents of (default: root)"
                },
                "query": {
                    "type": "string",
                    "description": "Additional query filter"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum files to return (default: 50)",
                    "default": 50
                },
                "order_by": {
                    "type": "string",
                    "description": "Sort order (e.g., 'name', 'modifiedTime desc')",
                    "default": "modifiedTime desc"
                },
                "include_trashed": {
                    "type": "boolean",
                    "description": "Include trashed files",
                    "default": False
                }
            }
        }
    },
    {
        "name": "get_file",
        "description": "Get metadata for a specific file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The file ID"
                }
            },
            "required": ["file_id"]
        }
    },
    {
        "name": "search_files",
        "description": "Search for files by name or content.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum results",
                    "default": 50
                },
                "file_type": {
                    "type": "string",
                    "description": "Filter by type: 'folder', 'document', 'spreadsheet', 'presentation', 'pdf', 'image'"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "read_file",
        "description": "Read file content. For Google Docs/Sheets/Slides, exports as text/CSV. For binary files, returns base64.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The file ID"
                },
                "max_size": {
                    "type": "integer",
                    "description": "Maximum content size (default: 1MB)",
                    "default": 1000000
                }
            },
            "required": ["file_id"]
        }
    },
    {
        "name": "create_file",
        "description": "Create a new file in Google Drive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "File name"
                },
                "content": {
                    "type": "string",
                    "description": "File content (text)"
                },
                "parent_id": {
                    "type": "string",
                    "description": "Parent folder ID (default: root)"
                },
                "mime_type": {
                    "type": "string",
                    "description": "MIME type (default: text/plain)",
                    "default": "text/plain"
                },
                "description": {
                    "type": "string",
                    "description": "File description"
                }
            },
            "required": ["name", "content"]
        }
    },
    {
        "name": "create_folder",
        "description": "Create a new folder in Google Drive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Folder name"
                },
                "parent_id": {
                    "type": "string",
                    "description": "Parent folder ID (default: root)"
                },
                "description": {
                    "type": "string",
                    "description": "Folder description"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "update_file",
        "description": "Update file content or metadata.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The file ID"
                },
                "content": {
                    "type": "string",
                    "description": "New file content"
                },
                "name": {
                    "type": "string",
                    "description": "New file name"
                },
                "description": {
                    "type": "string",
                    "description": "New description"
                }
            },
            "required": ["file_id"]
        }
    },
    {
        "name": "delete_file",
        "description": "Delete (trash) a file. Use permanent=true for permanent deletion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The file ID"
                },
                "permanent": {
                    "type": "boolean",
                    "description": "Permanently delete (DANGEROUS)",
                    "default": False
                }
            },
            "required": ["file_id"]
        }
    },
    {
        "name": "move_file",
        "description": "Move a file to a different folder.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The file ID"
                },
                "new_parent_id": {
                    "type": "string",
                    "description": "New parent folder ID"
                }
            },
            "required": ["file_id", "new_parent_id"]
        }
    },
    {
        "name": "copy_file",
        "description": "Copy a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The file ID to copy"
                },
                "new_name": {
                    "type": "string",
                    "description": "Name for the copy"
                },
                "parent_id": {
                    "type": "string",
                    "description": "Parent folder for the copy"
                }
            },
            "required": ["file_id"]
        }
    },
    {
        "name": "share_file",
        "description": "Share a file with a user.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The file ID"
                },
                "email": {
                    "type": "string",
                    "description": "Email address to share with"
                },
                "role": {
                    "type": "string",
                    "description": "Permission: 'reader', 'writer', 'commenter'",
                    "default": "reader"
                },
                "notify": {
                    "type": "boolean",
                    "description": "Send notification email",
                    "default": True
                },
                "message": {
                    "type": "string",
                    "description": "Custom message for notification"
                }
            },
            "required": ["file_id", "email"]
        }
    },
    {
        "name": "get_file_permissions",
        "description": "Get sharing permissions for a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file_id": {
                    "type": "string",
                    "description": "The file ID"
                }
            },
            "required": ["file_id"]
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
                "serverInfo": {"name": "google-drive", "version": "1.0.0"}
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
            "list_files": list_files,
            "get_file": get_file,
            "search_files": search_files,
            "read_file": read_file,
            "create_file": create_file,
            "create_folder": create_folder,
            "update_file": update_file,
            "delete_file": delete_file,
            "move_file": move_file,
            "copy_file": copy_file,
            "share_file": share_file,
            "get_file_permissions": get_file_permissions
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

