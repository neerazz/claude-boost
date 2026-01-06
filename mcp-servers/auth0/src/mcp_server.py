#!/usr/bin/env python3
"""
Auth0 MCP Server

A self-contained MCP server for Auth0 Management API operations.
Uses client credentials flow for authentication.

Environment Variables:
- AUTH0_DOMAIN: Your Auth0 domain (e.g., your-tenant.auth0.com)
- AUTH0_CLIENT_ID: Management API client ID
- AUTH0_CLIENT_SECRET: Management API client secret

Tools:
- list_users: List users
- get_user: Get user details
- create_user: Create a new user
- update_user: Update user
- delete_user: Delete user
- list_applications: List applications/clients
- get_application: Get application details
- list_connections: List identity connections
- list_roles: List roles
- get_role: Get role details
- assign_roles: Assign roles to user
- list_apis: List APIs/resource servers
- get_logs: Get authentication logs
- get_stats: Get tenant statistics
"""

from __future__ import annotations

import json
import sys
import os
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List

# Cache for access token
_token_cache: Dict[str, Any] = {}


def _get_domain() -> str:
    """Get Auth0 domain."""
    domain = os.environ.get("AUTH0_DOMAIN", "")
    if not domain:
        raise ValueError("AUTH0_DOMAIN environment variable not set")
    return domain.rstrip("/")


def _get_client_id() -> str:
    """Get Auth0 client ID."""
    client_id = os.environ.get("AUTH0_CLIENT_ID", "")
    if not client_id:
        raise ValueError("AUTH0_CLIENT_ID environment variable not set")
    return client_id


def _get_client_secret() -> str:
    """Get Auth0 client secret."""
    secret = os.environ.get("AUTH0_CLIENT_SECRET", "")
    if not secret:
        raise ValueError("AUTH0_CLIENT_SECRET environment variable not set")
    return secret


def _get_access_token() -> str:
    """Get a valid access token using client credentials."""
    global _token_cache
    
    # Check if we have a valid cached token
    if _token_cache.get("token") and _token_cache.get("expiry"):
        if datetime.now() < _token_cache["expiry"]:
            return _token_cache["token"]
    
    domain = _get_domain()
    client_id = _get_client_id()
    client_secret = _get_client_secret()
    
    url = f"https://{domain}/oauth/token"
    
    data = urllib.parse.urlencode({
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": f"https://{domain}/api/v2/"
    }).encode()
    
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
        
        _token_cache["token"] = result["access_token"]
        _token_cache["expiry"] = datetime.now() + timedelta(seconds=result.get("expires_in", 86400) - 60)
        
        return _token_cache["token"]
    
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise Exception(f"Auth0 authentication failed ({e.code}): {error_body}")
    except Exception as e:
        raise Exception(f"Auth0 authentication failed: {e}")


def _auth0_api(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Make an Auth0 Management API request."""
    try:
        token = _get_access_token()
        domain = _get_domain()
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"Authentication failed: {e}"}
    
    url = f"https://{domain}/api/v2/{endpoint}"
    
    if params:
        url += "?" + urllib.parse.urlencode(params)
    
    headers = {
        "Authorization": f"Bearer {token}",
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
            error_msg = error_data.get("message", error_data.get("error_description", str(e)))
        except:
            error_msg = error_body or str(e)
        return {"success": False, "error": f"API Error ({e.code}): {error_msg}"}
    
    except urllib.error.URLError as e:
        return {"success": False, "error": f"Network error: {e.reason}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def _format_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Format user for output."""
    return {
        "user_id": user.get("user_id"),
        "email": user.get("email"),
        "email_verified": user.get("email_verified"),
        "name": user.get("name"),
        "nickname": user.get("nickname"),
        "picture": user.get("picture"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
        "last_login": user.get("last_login"),
        "logins_count": user.get("logins_count"),
        "blocked": user.get("blocked", False),
        "identities": user.get("identities", []),
        "app_metadata": user.get("app_metadata", {}),
        "user_metadata": user.get("user_metadata", {})
    }


# ============================================================================
# AUTH0 TOOLS
# ============================================================================

def list_users(
    page: int = 0,
    per_page: int = 50,
    search_engine: str = "v3",
    query: Optional[str] = None,
    sort: Optional[str] = None,
    fields: Optional[str] = None,
    include_totals: bool = True
) -> Dict[str, Any]:
    """List users in Auth0.
    
    Args:
        page: Page number (0-indexed)
        per_page: Users per page (max 100)
        search_engine: Search engine version (v3 recommended)
        query: Lucene query string (e.g., "email:*@example.com")
        sort: Field to sort by (e.g., "created_at:-1" for descending)
        fields: Comma-separated list of fields to include
        include_totals: Include total count
    """
    params = {
        "page": page,
        "per_page": min(per_page, 100),
        "search_engine": search_engine,
        "include_totals": str(include_totals).lower()
    }
    
    if query:
        params["q"] = query
    
    if sort:
        params["sort"] = sort
    
    if fields:
        params["fields"] = fields
    
    result = _auth0_api("users", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    # Handle paginated response
    if isinstance(result, dict) and "users" in result:
        users = [_format_user(u) for u in result.get("users", [])]
        return {
            "success": True,
            "users": users,
            "total": result.get("total", len(users)),
            "start": result.get("start", page * per_page),
            "limit": result.get("limit", per_page),
            "count": len(users)
        }
    elif isinstance(result, list):
        users = [_format_user(u) for u in result]
        return {
            "success": True,
            "users": users,
            "count": len(users)
        }
    
    return {"success": True, "users": [], "count": 0}


def get_user(user_id: str) -> Dict[str, Any]:
    """Get user details.
    
    Args:
        user_id: The user ID (e.g., "auth0|123456")
    """
    result = _auth0_api(f"users/{urllib.parse.quote(user_id, safe='')}")
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "user": _format_user(result)
    }


def create_user(
    email: str,
    connection: str,
    password: Optional[str] = None,
    email_verified: bool = False,
    name: Optional[str] = None,
    nickname: Optional[str] = None,
    user_metadata: Optional[Dict[str, Any]] = None,
    app_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new user.
    
    Args:
        email: User's email address
        connection: Identity connection name (e.g., "Username-Password-Authentication")
        password: User's password (required for database connections)
        email_verified: Whether email is verified
        name: User's full name
        nickname: User's nickname
        user_metadata: Custom user data
        app_metadata: Custom app data
    """
    body = {
        "email": email,
        "connection": connection,
        "email_verified": email_verified
    }
    
    if password:
        body["password"] = password
    
    if name:
        body["name"] = name
    
    if nickname:
        body["nickname"] = nickname
    
    if user_metadata:
        body["user_metadata"] = user_metadata
    
    if app_metadata:
        body["app_metadata"] = app_metadata
    
    result = _auth0_api("users", method="POST", body=body)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "user": _format_user(result),
        "message": f"User created: {email}"
    }


def update_user(
    user_id: str,
    email: Optional[str] = None,
    password: Optional[str] = None,
    email_verified: Optional[bool] = None,
    blocked: Optional[bool] = None,
    name: Optional[str] = None,
    nickname: Optional[str] = None,
    user_metadata: Optional[Dict[str, Any]] = None,
    app_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update a user.
    
    Args:
        user_id: The user ID
        email: New email address
        password: New password
        email_verified: Email verification status
        blocked: Block/unblock user
        name: New name
        nickname: New nickname
        user_metadata: Updated user metadata
        app_metadata: Updated app metadata
    """
    body = {}
    
    if email is not None:
        body["email"] = email
    if password is not None:
        body["password"] = password
    if email_verified is not None:
        body["email_verified"] = email_verified
    if blocked is not None:
        body["blocked"] = blocked
    if name is not None:
        body["name"] = name
    if nickname is not None:
        body["nickname"] = nickname
    if user_metadata is not None:
        body["user_metadata"] = user_metadata
    if app_metadata is not None:
        body["app_metadata"] = app_metadata
    
    if not body:
        return {"success": False, "error": "No updates specified"}
    
    result = _auth0_api(f"users/{urllib.parse.quote(user_id, safe='')}", method="PATCH", body=body)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "user": _format_user(result),
        "message": "User updated"
    }


def delete_user(user_id: str) -> Dict[str, Any]:
    """Delete a user.
    
    Args:
        user_id: The user ID
    
    WARNING: This permanently deletes the user!
    """
    result = _auth0_api(f"users/{urllib.parse.quote(user_id, safe='')}", method="DELETE")
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "message": f"User {user_id} deleted"
    }


def list_applications(
    page: int = 0,
    per_page: int = 50,
    include_totals: bool = True
) -> Dict[str, Any]:
    """List Auth0 applications/clients.
    
    Args:
        page: Page number
        per_page: Applications per page
        include_totals: Include total count
    """
    params = {
        "page": page,
        "per_page": min(per_page, 100),
        "include_totals": str(include_totals).lower()
    }
    
    result = _auth0_api("clients", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    clients = result.get("clients", result) if isinstance(result, dict) else result
    if not isinstance(clients, list):
        clients = []
    
    apps = []
    for c in clients:
        apps.append({
            "client_id": c.get("client_id"),
            "name": c.get("name"),
            "app_type": c.get("app_type"),
            "is_first_party": c.get("is_first_party"),
            "is_token_endpoint_ip_header_trusted": c.get("is_token_endpoint_ip_header_trusted"),
            "callbacks": c.get("callbacks", []),
            "allowed_origins": c.get("allowed_origins", []),
            "web_origins": c.get("web_origins", []),
            "grant_types": c.get("grant_types", [])
        })
    
    return {
        "success": True,
        "applications": apps,
        "total": result.get("total", len(apps)) if isinstance(result, dict) else len(apps),
        "count": len(apps)
    }


def get_application(client_id: str) -> Dict[str, Any]:
    """Get application details.
    
    Args:
        client_id: The application client ID
    """
    result = _auth0_api(f"clients/{client_id}")
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "application": {
            "client_id": result.get("client_id"),
            "name": result.get("name"),
            "description": result.get("description"),
            "app_type": result.get("app_type"),
            "is_first_party": result.get("is_first_party"),
            "callbacks": result.get("callbacks", []),
            "allowed_origins": result.get("allowed_origins", []),
            "web_origins": result.get("web_origins", []),
            "allowed_logout_urls": result.get("allowed_logout_urls", []),
            "grant_types": result.get("grant_types", []),
            "jwt_configuration": result.get("jwt_configuration", {}),
            "token_endpoint_auth_method": result.get("token_endpoint_auth_method")
        }
    }


def list_connections(
    page: int = 0,
    per_page: int = 50,
    strategy: Optional[str] = None
) -> Dict[str, Any]:
    """List identity connections.
    
    Args:
        page: Page number
        per_page: Connections per page
        strategy: Filter by strategy (e.g., "auth0", "google-oauth2", "samlp")
    """
    params = {
        "page": page,
        "per_page": min(per_page, 100),
        "include_totals": "true"
    }
    
    if strategy:
        params["strategy"] = strategy
    
    result = _auth0_api("connections", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    connections = result.get("connections", result) if isinstance(result, dict) else result
    if not isinstance(connections, list):
        connections = []
    
    conns = []
    for c in connections:
        conns.append({
            "id": c.get("id"),
            "name": c.get("name"),
            "strategy": c.get("strategy"),
            "enabled_clients": c.get("enabled_clients", []),
            "is_domain_connection": c.get("is_domain_connection", False),
            "realms": c.get("realms", [])
        })
    
    return {
        "success": True,
        "connections": conns,
        "count": len(conns)
    }


def list_roles(
    page: int = 0,
    per_page: int = 50
) -> Dict[str, Any]:
    """List roles.
    
    Args:
        page: Page number
        per_page: Roles per page
    """
    params = {
        "page": page,
        "per_page": min(per_page, 100),
        "include_totals": "true"
    }
    
    result = _auth0_api("roles", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    roles = result.get("roles", result) if isinstance(result, dict) else result
    if not isinstance(roles, list):
        roles = []
    
    role_list = []
    for r in roles:
        role_list.append({
            "id": r.get("id"),
            "name": r.get("name"),
            "description": r.get("description")
        })
    
    return {
        "success": True,
        "roles": role_list,
        "total": result.get("total", len(role_list)) if isinstance(result, dict) else len(role_list),
        "count": len(role_list)
    }


def get_role(role_id: str) -> Dict[str, Any]:
    """Get role details.
    
    Args:
        role_id: The role ID
    """
    result = _auth0_api(f"roles/{role_id}")
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "role": {
            "id": result.get("id"),
            "name": result.get("name"),
            "description": result.get("description")
        }
    }


def assign_roles(user_id: str, role_ids: List[str]) -> Dict[str, Any]:
    """Assign roles to a user.
    
    Args:
        user_id: The user ID
        role_ids: List of role IDs to assign
    """
    result = _auth0_api(
        f"users/{urllib.parse.quote(user_id, safe='')}/roles",
        method="POST",
        body={"roles": role_ids}
    )
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "message": f"Assigned {len(role_ids)} role(s) to user"
    }


def list_apis(
    page: int = 0,
    per_page: int = 50
) -> Dict[str, Any]:
    """List APIs/Resource Servers.
    
    Args:
        page: Page number
        per_page: APIs per page
    """
    params = {
        "page": page,
        "per_page": min(per_page, 100),
        "include_totals": "true"
    }
    
    result = _auth0_api("resource-servers", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    apis = result if isinstance(result, list) else result.get("resource_servers", [])
    
    api_list = []
    for api in apis:
        api_list.append({
            "id": api.get("id"),
            "name": api.get("name"),
            "identifier": api.get("identifier"),
            "is_system": api.get("is_system", False),
            "scopes": api.get("scopes", []),
            "signing_alg": api.get("signing_alg"),
            "token_lifetime": api.get("token_lifetime")
        })
    
    return {
        "success": True,
        "apis": api_list,
        "count": len(api_list)
    }


def get_logs(
    page: int = 0,
    per_page: int = 50,
    sort: str = "date:-1",
    query: Optional[str] = None,
    from_log_id: Optional[str] = None
) -> Dict[str, Any]:
    """Get authentication logs.
    
    Args:
        page: Page number
        per_page: Logs per page
        sort: Sort order (e.g., "date:-1" for newest first)
        query: Lucene query string
        from_log_id: Start from specific log ID
    """
    params = {
        "page": page,
        "per_page": min(per_page, 100),
        "sort": sort,
        "include_totals": "true"
    }
    
    if query:
        params["q"] = query
    
    if from_log_id:
        params["from"] = from_log_id
    
    result = _auth0_api("logs", params=params)
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    logs = result.get("logs", result) if isinstance(result, dict) else result
    if not isinstance(logs, list):
        logs = []
    
    log_list = []
    for log in logs:
        log_list.append({
            "log_id": log.get("log_id"),
            "date": log.get("date"),
            "type": log.get("type"),
            "description": log.get("description"),
            "client_id": log.get("client_id"),
            "client_name": log.get("client_name"),
            "ip": log.get("ip"),
            "user_id": log.get("user_id"),
            "user_name": log.get("user_name")
        })
    
    return {
        "success": True,
        "logs": log_list,
        "count": len(log_list)
    }


def get_stats(days: int = 30) -> Dict[str, Any]:
    """Get tenant statistics.
    
    Args:
        days: Number of days to include (max 30)
    """
    result = _auth0_api("stats/active-users")
    
    if "error" in result:
        return {"success": False, "error": result.get("error")}
    
    # Get daily stats
    daily_result = _auth0_api("stats/daily", params={"from": f"-{min(days, 30)}d"})
    
    return {
        "success": True,
        "active_users": result,
        "daily_stats": daily_result if "error" not in daily_result else None
    }


# ============================================================================
# MCP PROTOCOL IMPLEMENTATION
# ============================================================================

TOOLS = [
    {
        "name": "list_users",
        "description": "List users in Auth0. Supports search queries and pagination.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number (0-indexed)", "default": 0},
                "per_page": {"type": "integer", "description": "Users per page (max 100)", "default": 50},
                "query": {"type": "string", "description": "Lucene query (e.g., 'email:*@example.com')"},
                "sort": {"type": "string", "description": "Sort field (e.g., 'created_at:-1')"},
                "fields": {"type": "string", "description": "Comma-separated fields to include"}
            }
        }
    },
    {
        "name": "get_user",
        "description": "Get detailed information about a specific user.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The user ID (e.g., 'auth0|123456')"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "create_user",
        "description": "Create a new user in Auth0.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "User's email address"},
                "connection": {"type": "string", "description": "Identity connection name"},
                "password": {"type": "string", "description": "Password (required for database connections)"},
                "email_verified": {"type": "boolean", "description": "Email verification status", "default": False},
                "name": {"type": "string", "description": "User's full name"},
                "nickname": {"type": "string", "description": "User's nickname"},
                "user_metadata": {"type": "object", "description": "Custom user data"},
                "app_metadata": {"type": "object", "description": "Custom app data"}
            },
            "required": ["email", "connection"]
        }
    },
    {
        "name": "update_user",
        "description": "Update an existing user.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The user ID"},
                "email": {"type": "string", "description": "New email"},
                "password": {"type": "string", "description": "New password"},
                "email_verified": {"type": "boolean", "description": "Email verification status"},
                "blocked": {"type": "boolean", "description": "Block/unblock user"},
                "name": {"type": "string", "description": "New name"},
                "nickname": {"type": "string", "description": "New nickname"},
                "user_metadata": {"type": "object", "description": "Updated user metadata"},
                "app_metadata": {"type": "object", "description": "Updated app metadata"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "delete_user",
        "description": "Delete a user. WARNING: Permanent deletion!",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The user ID to delete"}
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "list_applications",
        "description": "List Auth0 applications/clients.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number", "default": 0},
                "per_page": {"type": "integer", "description": "Applications per page", "default": 50}
            }
        }
    },
    {
        "name": "get_application",
        "description": "Get application details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "The application client ID"}
            },
            "required": ["client_id"]
        }
    },
    {
        "name": "list_connections",
        "description": "List identity connections (e.g., database, social, enterprise).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number", "default": 0},
                "per_page": {"type": "integer", "description": "Connections per page", "default": 50},
                "strategy": {"type": "string", "description": "Filter by strategy (auth0, google-oauth2, samlp, etc.)"}
            }
        }
    },
    {
        "name": "list_roles",
        "description": "List roles defined in Auth0.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number", "default": 0},
                "per_page": {"type": "integer", "description": "Roles per page", "default": 50}
            }
        }
    },
    {
        "name": "get_role",
        "description": "Get role details.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "role_id": {"type": "string", "description": "The role ID"}
            },
            "required": ["role_id"]
        }
    },
    {
        "name": "assign_roles",
        "description": "Assign roles to a user.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "The user ID"},
                "role_ids": {"type": "array", "items": {"type": "string"}, "description": "Role IDs to assign"}
            },
            "required": ["user_id", "role_ids"]
        }
    },
    {
        "name": "list_apis",
        "description": "List APIs/Resource Servers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number", "default": 0},
                "per_page": {"type": "integer", "description": "APIs per page", "default": 50}
            }
        }
    },
    {
        "name": "get_logs",
        "description": "Get authentication logs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "page": {"type": "integer", "description": "Page number", "default": 0},
                "per_page": {"type": "integer", "description": "Logs per page", "default": 50},
                "sort": {"type": "string", "description": "Sort order", "default": "date:-1"},
                "query": {"type": "string", "description": "Lucene query string"},
                "from_log_id": {"type": "string", "description": "Start from specific log ID"}
            }
        }
    },
    {
        "name": "get_stats",
        "description": "Get tenant statistics (active users, daily stats).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Number of days (max 30)", "default": 30}
            }
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
                "serverInfo": {"name": "auth0", "version": "1.0.0"}
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
            "list_users": list_users,
            "get_user": get_user,
            "create_user": create_user,
            "update_user": update_user,
            "delete_user": delete_user,
            "list_applications": list_applications,
            "get_application": get_application,
            "list_connections": list_connections,
            "list_roles": list_roles,
            "get_role": get_role,
            "assign_roles": assign_roles,
            "list_apis": list_apis,
            "get_logs": get_logs,
            "get_stats": get_stats
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

