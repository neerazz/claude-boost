#!/usr/bin/env python3
"""
GitHub MCP Server

A comprehensive MCP server for GitHub operations.
Uses GitHub REST API - works independently of any admin-controlled integrations.

Environment Variables:
- GITHUB_TOKEN: Personal Access Token (required)
- GITHUB_ORG: Default organization (optional)
- GITHUB_USER: Default username (optional)

Scopes needed for PAT:
- repo (full access to repositories)
- read:org (organization access)
- read:user (user profile)
- security_events (security alerts)
- workflow (actions/workflows)
- read:discussion (discussions)

Tools:
PRs: list_prs, get_pr, search_prs, create_pr, merge_pr, pr_reviews, request_reviewers
Issues: list_issues, get_issue, search_issues, create_issue, update_issue, add_comment
Repos: list_repos, get_repo, list_commits, list_releases, get_file, list_branches
Security: dependabot_alerts, code_scanning_alerts, secret_scanning_alerts
CI/CD: list_workflow_runs, get_workflow_run, list_workflows, rerun_workflow
User: get_user, get_authenticated_user, list_orgs, list_notifications
Search: search_code, search_repos, search_users
"""

from __future__ import annotations

import json
import sys
import os
import base64
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List, Union

# GitHub API base URL
GITHUB_API = "https://api.github.com"


def _get_token() -> str:
    """Get GitHub token."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable not set. Get a PAT from: https://github.com/settings/tokens")
    return token


def _get_default_org() -> Optional[str]:
    """Get default organization."""
    return os.environ.get("GITHUB_ORG")


def _get_default_user() -> Optional[str]:
    """Get default username."""
    return os.environ.get("GITHUB_USER")


def _github_api(
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    body: Optional[Dict[str, Any]] = None,
    accept: str = "application/vnd.github+json"
) -> Union[Dict[str, Any], List[Any]]:
    """Make a GitHub API request."""
    try:
        token = _get_token()
    except ValueError as e:
        return {"success": False, "error": str(e)}
    
    url = f"{GITHUB_API}/{endpoint}"
    
    if params:
        # Filter out None values
        params = {k: v for k, v in params.items() if v is not None}
        if params:
            url += "?" + urllib.parse.urlencode(params)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": accept,
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "GitHub-MCP-Server/1.0"
    }
    
    if body:
        headers["Content-Type"] = "application/json"
    
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
            error_msg = error_data.get("message", str(e))
            if "documentation_url" in error_data:
                error_msg += f" (see: {error_data['documentation_url']})"
        except:
            error_msg = error_body or str(e)
        return {"success": False, "error": f"GitHub API Error ({e.code}): {error_msg}"}
    
    except urllib.error.URLError as e:
        return {"success": False, "error": f"Network error: {e.reason}"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


def _paginate_api(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    max_items: int = 100
) -> List[Any]:
    """Paginate through GitHub API results."""
    results = []
    params = params or {}
    params["per_page"] = min(100, max_items)
    page = 1
    
    while len(results) < max_items:
        params["page"] = page
        response = _github_api(endpoint, params=params)
        
        if isinstance(response, dict) and "error" in response:
            return response
        
        if isinstance(response, dict) and "items" in response:
            items = response["items"]
        elif isinstance(response, list):
            items = response
        else:
            break
        
        if not items:
            break
        
        results.extend(items)
        
        if len(items) < params["per_page"]:
            break
        
        page += 1
    
    return results[:max_items]


# ============================================================================
# PULL REQUESTS
# ============================================================================

def list_prs(
    owner: str,
    repo: str,
    state: str = "open",
    sort: str = "updated",
    direction: str = "desc",
    per_page: int = 30
) -> Dict[str, Any]:
    """List pull requests for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        state: PR state - "open", "closed", "all"
        sort: Sort by - "created", "updated", "popularity", "long-running"
        direction: Sort direction - "asc", "desc"
        per_page: Number of results (max 100)
    """
    result = _paginate_api(
        f"repos/{owner}/{repo}/pulls",
        params={"state": state, "sort": sort, "direction": direction},
        max_items=per_page
    )
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    prs = []
    for pr in result:
        prs.append({
            "number": pr.get("number"),
            "title": pr.get("title"),
            "state": pr.get("state"),
            "user": pr.get("user", {}).get("login"),
            "created_at": pr.get("created_at"),
            "updated_at": pr.get("updated_at"),
            "merged_at": pr.get("merged_at"),
            "draft": pr.get("draft"),
            "labels": [l.get("name") for l in pr.get("labels", [])],
            "head_ref": pr.get("head", {}).get("ref"),
            "base_ref": pr.get("base", {}).get("ref"),
            "url": pr.get("html_url"),
            "review_comments": pr.get("review_comments", 0),
            "commits": pr.get("commits", 0),
            "additions": pr.get("additions", 0),
            "deletions": pr.get("deletions", 0)
        })
    
    return {"success": True, "pull_requests": prs, "count": len(prs)}


def get_pr(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """Get detailed information about a pull request.
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
    """
    result = _github_api(f"repos/{owner}/{repo}/pulls/{pr_number}")
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "pull_request": {
            "number": result.get("number"),
            "title": result.get("title"),
            "body": result.get("body"),
            "state": result.get("state"),
            "user": result.get("user", {}).get("login"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "merged_at": result.get("merged_at"),
            "merged_by": result.get("merged_by", {}).get("login") if result.get("merged_by") else None,
            "draft": result.get("draft"),
            "mergeable": result.get("mergeable"),
            "mergeable_state": result.get("mergeable_state"),
            "labels": [l.get("name") for l in result.get("labels", [])],
            "assignees": [a.get("login") for a in result.get("assignees", [])],
            "requested_reviewers": [r.get("login") for r in result.get("requested_reviewers", [])],
            "head_ref": result.get("head", {}).get("ref"),
            "base_ref": result.get("base", {}).get("ref"),
            "url": result.get("html_url"),
            "commits": result.get("commits"),
            "additions": result.get("additions"),
            "deletions": result.get("deletions"),
            "changed_files": result.get("changed_files")
        }
    }


def search_prs(
    query: str,
    sort: str = "updated",
    order: str = "desc",
    per_page: int = 30
) -> Dict[str, Any]:
    """Search pull requests across GitHub.
    
    Args:
        query: Search query. Examples:
            - "is:open author:username org:orgname"
            - "is:open review-requested:username"
            - "is:merged merged:>2024-01-01"
            - "label:bug org:orgname"
        sort: Sort by - "created", "updated", "comments"
        order: Sort order - "asc", "desc"
        per_page: Number of results
    """
    params = {
        "q": f"type:pr {query}",
        "sort": sort,
        "order": order,
        "per_page": min(per_page, 100)
    }
    
    result = _github_api("search/issues", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    prs = []
    for item in result.get("items", []):
        prs.append({
            "number": item.get("number"),
            "title": item.get("title"),
            "state": item.get("state"),
            "user": item.get("user", {}).get("login"),
            "repository": item.get("repository_url", "").split("/")[-1],
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "labels": [l.get("name") for l in item.get("labels", [])],
            "url": item.get("html_url"),
            "comments": item.get("comments")
        })
    
    return {
        "success": True,
        "pull_requests": prs,
        "total_count": result.get("total_count", 0),
        "count": len(prs)
    }


def create_pr(
    owner: str,
    repo: str,
    title: str,
    head: str,
    base: str,
    body: Optional[str] = None,
    draft: bool = False
) -> Dict[str, Any]:
    """Create a pull request.
    
    Args:
        owner: Repository owner
        repo: Repository name
        title: PR title
        head: Branch containing changes
        base: Branch to merge into
        body: PR description
        draft: Create as draft PR
    """
    data = {
        "title": title,
        "head": head,
        "base": base,
        "draft": draft
    }
    
    if body:
        data["body"] = body
    
    result = _github_api(f"repos/{owner}/{repo}/pulls", method="POST", body=data)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "pull_request": {
            "number": result.get("number"),
            "title": result.get("title"),
            "url": result.get("html_url"),
            "state": result.get("state")
        }
    }


def merge_pr(
    owner: str,
    repo: str,
    pr_number: int,
    merge_method: str = "squash",
    commit_title: Optional[str] = None,
    commit_message: Optional[str] = None
) -> Dict[str, Any]:
    """Merge a pull request.
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
        merge_method: "merge", "squash", or "rebase"
        commit_title: Custom commit title
        commit_message: Custom commit message
    """
    data = {"merge_method": merge_method}
    
    if commit_title:
        data["commit_title"] = commit_title
    if commit_message:
        data["commit_message"] = commit_message
    
    result = _github_api(f"repos/{owner}/{repo}/pulls/{pr_number}/merge", method="PUT", body=data)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "merged": result.get("merged"),
        "sha": result.get("sha"),
        "message": result.get("message")
    }


def pr_reviews(owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
    """Get reviews for a pull request.
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
    """
    result = _github_api(f"repos/{owner}/{repo}/pulls/{pr_number}/reviews")
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    reviews = []
    for r in result:
        reviews.append({
            "id": r.get("id"),
            "user": r.get("user", {}).get("login"),
            "state": r.get("state"),
            "body": r.get("body"),
            "submitted_at": r.get("submitted_at"),
            "commit_id": r.get("commit_id")
        })
    
    return {"success": True, "reviews": reviews, "count": len(reviews)}


def request_reviewers(
    owner: str,
    repo: str,
    pr_number: int,
    reviewers: List[str]
) -> Dict[str, Any]:
    """Request reviewers for a pull request.
    
    Args:
        owner: Repository owner
        repo: Repository name
        pr_number: Pull request number
        reviewers: List of usernames to request review from
    """
    result = _github_api(
        f"repos/{owner}/{repo}/pulls/{pr_number}/requested_reviewers",
        method="POST",
        body={"reviewers": reviewers}
    )
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "requested_reviewers": [r.get("login") for r in result.get("requested_reviewers", [])]
    }


# ============================================================================
# ISSUES
# ============================================================================

def list_issues(
    owner: str,
    repo: str,
    state: str = "open",
    assignee: Optional[str] = None,
    labels: Optional[str] = None,
    sort: str = "updated",
    direction: str = "desc",
    per_page: int = 30
) -> Dict[str, Any]:
    """List issues for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        state: Issue state - "open", "closed", "all"
        assignee: Filter by assignee username
        labels: Comma-separated list of labels
        sort: Sort by - "created", "updated", "comments"
        direction: Sort direction - "asc", "desc"
        per_page: Number of results
    """
    params = {
        "state": state,
        "sort": sort,
        "direction": direction,
        "assignee": assignee,
        "labels": labels
    }
    
    result = _paginate_api(f"repos/{owner}/{repo}/issues", params=params, max_items=per_page)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    issues = []
    for issue in result:
        # Filter out PRs (they're included in issues endpoint)
        if "pull_request" in issue:
            continue
        
        issues.append({
            "number": issue.get("number"),
            "title": issue.get("title"),
            "state": issue.get("state"),
            "user": issue.get("user", {}).get("login"),
            "assignees": [a.get("login") for a in issue.get("assignees", [])],
            "labels": [l.get("name") for l in issue.get("labels", [])],
            "created_at": issue.get("created_at"),
            "updated_at": issue.get("updated_at"),
            "comments": issue.get("comments"),
            "url": issue.get("html_url")
        })
    
    return {"success": True, "issues": issues, "count": len(issues)}


def get_issue(owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
    """Get detailed information about an issue.
    
    Args:
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
    """
    result = _github_api(f"repos/{owner}/{repo}/issues/{issue_number}")
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "issue": {
            "number": result.get("number"),
            "title": result.get("title"),
            "body": result.get("body"),
            "state": result.get("state"),
            "user": result.get("user", {}).get("login"),
            "assignees": [a.get("login") for a in result.get("assignees", [])],
            "labels": [l.get("name") for l in result.get("labels", [])],
            "milestone": result.get("milestone", {}).get("title") if result.get("milestone") else None,
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "closed_at": result.get("closed_at"),
            "comments": result.get("comments"),
            "url": result.get("html_url")
        }
    }


def search_issues(
    query: str,
    sort: str = "updated",
    order: str = "desc",
    per_page: int = 30
) -> Dict[str, Any]:
    """Search issues across GitHub.
    
    Args:
        query: Search query. Examples:
            - "is:open assignee:username org:orgname"
            - "is:issue label:bug org:orgname"
            - "mentions:username org:orgname"
        sort: Sort by - "created", "updated", "comments"
        order: Sort order - "asc", "desc"
        per_page: Number of results
    """
    params = {
        "q": f"type:issue {query}",
        "sort": sort,
        "order": order,
        "per_page": min(per_page, 100)
    }
    
    result = _github_api("search/issues", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    issues = []
    for item in result.get("items", []):
        issues.append({
            "number": item.get("number"),
            "title": item.get("title"),
            "state": item.get("state"),
            "user": item.get("user", {}).get("login"),
            "repository": item.get("repository_url", "").split("/")[-1],
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
            "labels": [l.get("name") for l in item.get("labels", [])],
            "url": item.get("html_url"),
            "comments": item.get("comments")
        })
    
    return {
        "success": True,
        "issues": issues,
        "total_count": result.get("total_count", 0),
        "count": len(issues)
    }


def create_issue(
    owner: str,
    repo: str,
    title: str,
    body: Optional[str] = None,
    assignees: Optional[List[str]] = None,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Create an issue.
    
    Args:
        owner: Repository owner
        repo: Repository name
        title: Issue title
        body: Issue body
        assignees: List of usernames to assign
        labels: List of label names
    """
    data = {"title": title}
    
    if body:
        data["body"] = body
    if assignees:
        data["assignees"] = assignees
    if labels:
        data["labels"] = labels
    
    result = _github_api(f"repos/{owner}/{repo}/issues", method="POST", body=data)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "issue": {
            "number": result.get("number"),
            "title": result.get("title"),
            "url": result.get("html_url")
        }
    }


def update_issue(
    owner: str,
    repo: str,
    issue_number: int,
    title: Optional[str] = None,
    body: Optional[str] = None,
    state: Optional[str] = None,
    assignees: Optional[List[str]] = None,
    labels: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Update an issue.
    
    Args:
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        title: New title
        body: New body
        state: New state - "open" or "closed"
        assignees: New assignees
        labels: New labels
    """
    data = {}
    
    if title is not None:
        data["title"] = title
    if body is not None:
        data["body"] = body
    if state is not None:
        data["state"] = state
    if assignees is not None:
        data["assignees"] = assignees
    if labels is not None:
        data["labels"] = labels
    
    if not data:
        return {"success": False, "error": "No updates specified"}
    
    result = _github_api(f"repos/{owner}/{repo}/issues/{issue_number}", method="PATCH", body=data)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {"success": True, "issue": {"number": result.get("number"), "url": result.get("html_url")}}


def add_comment(
    owner: str,
    repo: str,
    issue_number: int,
    body: str
) -> Dict[str, Any]:
    """Add a comment to an issue or PR.
    
    Args:
        owner: Repository owner
        repo: Repository name
        issue_number: Issue or PR number
        body: Comment body
    """
    result = _github_api(
        f"repos/{owner}/{repo}/issues/{issue_number}/comments",
        method="POST",
        body={"body": body}
    )
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "comment": {
            "id": result.get("id"),
            "url": result.get("html_url"),
            "created_at": result.get("created_at")
        }
    }


# ============================================================================
# REPOSITORIES
# ============================================================================

def list_repos(
    owner: Optional[str] = None,
    org: Optional[str] = None,
    type: str = "all",
    sort: str = "updated",
    per_page: int = 30
) -> Dict[str, Any]:
    """List repositories for a user or organization.
    
    Args:
        owner: Username (for user repos)
        org: Organization name (for org repos)
        type: Repo type - "all", "public", "private", "forks", "sources", "member"
        sort: Sort by - "created", "updated", "pushed", "full_name"
        per_page: Number of results
    """
    if org:
        endpoint = f"orgs/{org}/repos"
    elif owner:
        endpoint = f"users/{owner}/repos"
    else:
        org = _get_default_org()
        owner = _get_default_user()
        if org:
            endpoint = f"orgs/{org}/repos"
        elif owner:
            endpoint = f"users/{owner}/repos"
        else:
            return {"success": False, "error": "Must specify owner or org"}
    
    result = _paginate_api(endpoint, params={"type": type, "sort": sort}, max_items=per_page)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    repos = []
    for repo in result:
        repos.append({
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "description": repo.get("description"),
            "private": repo.get("private"),
            "fork": repo.get("fork"),
            "created_at": repo.get("created_at"),
            "updated_at": repo.get("updated_at"),
            "pushed_at": repo.get("pushed_at"),
            "language": repo.get("language"),
            "default_branch": repo.get("default_branch"),
            "url": repo.get("html_url"),
            "open_issues_count": repo.get("open_issues_count"),
            "stargazers_count": repo.get("stargazers_count")
        })
    
    return {"success": True, "repositories": repos, "count": len(repos)}


def get_repo(owner: str, repo: str) -> Dict[str, Any]:
    """Get repository details.
    
    Args:
        owner: Repository owner
        repo: Repository name
    """
    result = _github_api(f"repos/{owner}/{repo}")
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "repository": {
            "name": result.get("name"),
            "full_name": result.get("full_name"),
            "description": result.get("description"),
            "private": result.get("private"),
            "fork": result.get("fork"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "pushed_at": result.get("pushed_at"),
            "language": result.get("language"),
            "default_branch": result.get("default_branch"),
            "url": result.get("html_url"),
            "clone_url": result.get("clone_url"),
            "open_issues_count": result.get("open_issues_count"),
            "forks_count": result.get("forks_count"),
            "stargazers_count": result.get("stargazers_count"),
            "watchers_count": result.get("watchers_count"),
            "size": result.get("size"),
            "topics": result.get("topics", [])
        }
    }


def list_commits(
    owner: str,
    repo: str,
    sha: Optional[str] = None,
    author: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    per_page: int = 30
) -> Dict[str, Any]:
    """List commits for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        sha: SHA or branch to start from
        author: Filter by author username or email
        since: ISO 8601 date - commits after this date
        until: ISO 8601 date - commits before this date
        per_page: Number of results
    """
    params = {"sha": sha, "author": author, "since": since, "until": until}
    
    result = _paginate_api(f"repos/{owner}/{repo}/commits", params=params, max_items=per_page)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    commits = []
    for commit in result:
        commits.append({
            "sha": commit.get("sha")[:7],
            "full_sha": commit.get("sha"),
            "message": commit.get("commit", {}).get("message", "").split("\n")[0],
            "author": commit.get("commit", {}).get("author", {}).get("name"),
            "author_login": commit.get("author", {}).get("login") if commit.get("author") else None,
            "date": commit.get("commit", {}).get("author", {}).get("date"),
            "url": commit.get("html_url")
        })
    
    return {"success": True, "commits": commits, "count": len(commits)}


def list_releases(owner: str, repo: str, per_page: int = 10) -> Dict[str, Any]:
    """List releases for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        per_page: Number of results
    """
    result = _paginate_api(f"repos/{owner}/{repo}/releases", max_items=per_page)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    releases = []
    for release in result:
        releases.append({
            "tag_name": release.get("tag_name"),
            "name": release.get("name"),
            "draft": release.get("draft"),
            "prerelease": release.get("prerelease"),
            "created_at": release.get("created_at"),
            "published_at": release.get("published_at"),
            "author": release.get("author", {}).get("login"),
            "url": release.get("html_url"),
            "body": release.get("body", "")[:500]
        })
    
    return {"success": True, "releases": releases, "count": len(releases)}


def get_file(
    owner: str,
    repo: str,
    path: str,
    ref: Optional[str] = None
) -> Dict[str, Any]:
    """Get file contents from a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        path: File path
        ref: Branch, tag, or commit SHA
    """
    params = {"ref": ref} if ref else None
    
    result = _github_api(f"repos/{owner}/{repo}/contents/{path}", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    if result.get("type") == "file":
        content = ""
        if result.get("encoding") == "base64" and result.get("content"):
            try:
                content = base64.b64decode(result["content"]).decode("utf-8")
            except:
                content = "[Binary file - cannot decode]"
        
        return {
            "success": True,
            "file": {
                "name": result.get("name"),
                "path": result.get("path"),
                "sha": result.get("sha"),
                "size": result.get("size"),
                "url": result.get("html_url"),
                "content": content
            }
        }
    elif result.get("type") == "dir" or isinstance(result, list):
        items = result if isinstance(result, list) else [result]
        return {
            "success": True,
            "directory": {
                "path": path,
                "items": [{"name": i.get("name"), "type": i.get("type"), "path": i.get("path")} for i in items]
            }
        }
    
    return {"success": True, "content": result}


def list_branches(owner: str, repo: str, per_page: int = 30) -> Dict[str, Any]:
    """List branches for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        per_page: Number of results
    """
    result = _paginate_api(f"repos/{owner}/{repo}/branches", max_items=per_page)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    branches = []
    for branch in result:
        branches.append({
            "name": branch.get("name"),
            "protected": branch.get("protected"),
            "sha": branch.get("commit", {}).get("sha", "")[:7]
        })
    
    return {"success": True, "branches": branches, "count": len(branches)}


# ============================================================================
# SECURITY ALERTS
# ============================================================================

def dependabot_alerts(
    owner: str,
    repo: str,
    state: str = "open",
    severity: Optional[str] = None,
    per_page: int = 30
) -> Dict[str, Any]:
    """Get Dependabot security alerts for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        state: Alert state - "open", "dismissed", "fixed"
        severity: Filter by severity - "critical", "high", "medium", "low"
        per_page: Number of results
    """
    params = {"state": state, "per_page": min(per_page, 100)}
    if severity:
        params["severity"] = severity
    
    result = _github_api(f"repos/{owner}/{repo}/dependabot/alerts", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    alerts = []
    for alert in result if isinstance(result, list) else []:
        alerts.append({
            "number": alert.get("number"),
            "state": alert.get("state"),
            "severity": alert.get("security_vulnerability", {}).get("severity"),
            "package": alert.get("dependency", {}).get("package", {}).get("name"),
            "ecosystem": alert.get("dependency", {}).get("package", {}).get("ecosystem"),
            "manifest_path": alert.get("dependency", {}).get("manifest_path"),
            "summary": alert.get("security_advisory", {}).get("summary"),
            "description": alert.get("security_advisory", {}).get("description", "")[:200],
            "created_at": alert.get("created_at"),
            "url": alert.get("html_url")
        })
    
    return {"success": True, "alerts": alerts, "count": len(alerts)}


def code_scanning_alerts(
    owner: str,
    repo: str,
    state: str = "open",
    severity: Optional[str] = None,
    per_page: int = 30
) -> Dict[str, Any]:
    """Get code scanning alerts for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        state: Alert state - "open", "closed", "dismissed", "fixed"
        severity: Filter by severity - "critical", "high", "medium", "low", "warning", "note"
        per_page: Number of results
    """
    params = {"state": state, "per_page": min(per_page, 100)}
    if severity:
        params["severity"] = severity
    
    result = _github_api(f"repos/{owner}/{repo}/code-scanning/alerts", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    alerts = []
    for alert in result if isinstance(result, list) else []:
        alerts.append({
            "number": alert.get("number"),
            "state": alert.get("state"),
            "rule_id": alert.get("rule", {}).get("id"),
            "severity": alert.get("rule", {}).get("security_severity_level"),
            "description": alert.get("rule", {}).get("description"),
            "tool": alert.get("tool", {}).get("name"),
            "created_at": alert.get("created_at"),
            "url": alert.get("html_url"),
            "location": alert.get("most_recent_instance", {}).get("location", {}).get("path")
        })
    
    return {"success": True, "alerts": alerts, "count": len(alerts)}


def secret_scanning_alerts(
    owner: str,
    repo: str,
    state: str = "open",
    per_page: int = 30
) -> Dict[str, Any]:
    """Get secret scanning alerts for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        state: Alert state - "open", "resolved"
        per_page: Number of results
    """
    params = {"state": state, "per_page": min(per_page, 100)}
    
    result = _github_api(f"repos/{owner}/{repo}/secret-scanning/alerts", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    alerts = []
    for alert in result if isinstance(result, list) else []:
        alerts.append({
            "number": alert.get("number"),
            "state": alert.get("state"),
            "secret_type": alert.get("secret_type"),
            "secret_type_display_name": alert.get("secret_type_display_name"),
            "created_at": alert.get("created_at"),
            "url": alert.get("html_url"),
            "resolution": alert.get("resolution")
        })
    
    return {"success": True, "alerts": alerts, "count": len(alerts)}


# ============================================================================
# WORKFLOWS / ACTIONS
# ============================================================================

def list_workflows(owner: str, repo: str, per_page: int = 30) -> Dict[str, Any]:
    """List workflows for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        per_page: Number of results
    """
    result = _github_api(f"repos/{owner}/{repo}/actions/workflows", params={"per_page": per_page})
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    workflows = []
    for wf in result.get("workflows", []):
        workflows.append({
            "id": wf.get("id"),
            "name": wf.get("name"),
            "path": wf.get("path"),
            "state": wf.get("state"),
            "created_at": wf.get("created_at"),
            "updated_at": wf.get("updated_at")
        })
    
    return {"success": True, "workflows": workflows, "count": len(workflows)}


def list_workflow_runs(
    owner: str,
    repo: str,
    workflow_id: Optional[int] = None,
    branch: Optional[str] = None,
    actor: Optional[str] = None,
    status: Optional[str] = None,
    per_page: int = 30
) -> Dict[str, Any]:
    """List workflow runs for a repository.
    
    Args:
        owner: Repository owner
        repo: Repository name
        workflow_id: Filter by workflow ID
        branch: Filter by branch
        actor: Filter by user who triggered
        status: Filter by status - "queued", "in_progress", "completed", "success", "failure", etc.
        per_page: Number of results
    """
    if workflow_id:
        endpoint = f"repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
    else:
        endpoint = f"repos/{owner}/{repo}/actions/runs"
    
    params = {
        "branch": branch,
        "actor": actor,
        "status": status,
        "per_page": min(per_page, 100)
    }
    
    result = _github_api(endpoint, params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    runs = []
    for run in result.get("workflow_runs", []):
        runs.append({
            "id": run.get("id"),
            "name": run.get("name"),
            "display_title": run.get("display_title"),
            "status": run.get("status"),
            "conclusion": run.get("conclusion"),
            "workflow_id": run.get("workflow_id"),
            "head_branch": run.get("head_branch"),
            "head_sha": run.get("head_sha")[:7] if run.get("head_sha") else None,
            "event": run.get("event"),
            "actor": run.get("actor", {}).get("login"),
            "created_at": run.get("created_at"),
            "updated_at": run.get("updated_at"),
            "url": run.get("html_url")
        })
    
    return {"success": True, "workflow_runs": runs, "count": len(runs)}


def get_workflow_run(owner: str, repo: str, run_id: int) -> Dict[str, Any]:
    """Get details of a workflow run.
    
    Args:
        owner: Repository owner
        repo: Repository name
        run_id: Workflow run ID
    """
    result = _github_api(f"repos/{owner}/{repo}/actions/runs/{run_id}")
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    # Also get jobs
    jobs_result = _github_api(f"repos/{owner}/{repo}/actions/runs/{run_id}/jobs")
    jobs = []
    if isinstance(jobs_result, dict) and "jobs" in jobs_result:
        for job in jobs_result["jobs"]:
            jobs.append({
                "id": job.get("id"),
                "name": job.get("name"),
                "status": job.get("status"),
                "conclusion": job.get("conclusion"),
                "started_at": job.get("started_at"),
                "completed_at": job.get("completed_at")
            })
    
    return {
        "success": True,
        "workflow_run": {
            "id": result.get("id"),
            "name": result.get("name"),
            "display_title": result.get("display_title"),
            "status": result.get("status"),
            "conclusion": result.get("conclusion"),
            "workflow_id": result.get("workflow_id"),
            "head_branch": result.get("head_branch"),
            "head_sha": result.get("head_sha"),
            "event": result.get("event"),
            "actor": result.get("actor", {}).get("login"),
            "run_attempt": result.get("run_attempt"),
            "created_at": result.get("created_at"),
            "updated_at": result.get("updated_at"),
            "url": result.get("html_url"),
            "jobs": jobs
        }
    }


def rerun_workflow(owner: str, repo: str, run_id: int) -> Dict[str, Any]:
    """Re-run a workflow.
    
    Args:
        owner: Repository owner
        repo: Repository name
        run_id: Workflow run ID
    """
    result = _github_api(f"repos/{owner}/{repo}/actions/runs/{run_id}/rerun", method="POST")
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {"success": True, "message": f"Workflow run {run_id} re-triggered"}


# ============================================================================
# USER & NOTIFICATIONS
# ============================================================================

def get_user(username: str) -> Dict[str, Any]:
    """Get user profile information.
    
    Args:
        username: GitHub username
    """
    result = _github_api(f"users/{username}")
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "user": {
            "login": result.get("login"),
            "name": result.get("name"),
            "email": result.get("email"),
            "bio": result.get("bio"),
            "company": result.get("company"),
            "location": result.get("location"),
            "public_repos": result.get("public_repos"),
            "followers": result.get("followers"),
            "following": result.get("following"),
            "created_at": result.get("created_at"),
            "url": result.get("html_url")
        }
    }


def get_authenticated_user() -> Dict[str, Any]:
    """Get the authenticated user's profile."""
    result = _github_api("user")
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    return {
        "success": True,
        "user": {
            "login": result.get("login"),
            "name": result.get("name"),
            "email": result.get("email"),
            "bio": result.get("bio"),
            "company": result.get("company"),
            "location": result.get("location"),
            "public_repos": result.get("public_repos"),
            "private_repos": result.get("total_private_repos"),
            "followers": result.get("followers"),
            "following": result.get("following"),
            "created_at": result.get("created_at"),
            "url": result.get("html_url")
        }
    }


def list_orgs() -> Dict[str, Any]:
    """List organizations for the authenticated user."""
    result = _github_api("user/orgs")
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    orgs = []
    for org in result if isinstance(result, list) else []:
        orgs.append({
            "login": org.get("login"),
            "description": org.get("description"),
            "url": f"https://github.com/{org.get('login')}"
        })
    
    return {"success": True, "organizations": orgs, "count": len(orgs)}


def list_notifications(
    all: bool = False,
    participating: bool = False,
    per_page: int = 30
) -> Dict[str, Any]:
    """List notifications for the authenticated user.
    
    Args:
        all: Show all notifications (including read)
        participating: Only show participating notifications
        per_page: Number of results
    """
    params = {
        "all": str(all).lower(),
        "participating": str(participating).lower(),
        "per_page": min(per_page, 100)
    }
    
    result = _github_api("notifications", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    notifications = []
    for notif in result if isinstance(result, list) else []:
        notifications.append({
            "id": notif.get("id"),
            "reason": notif.get("reason"),
            "unread": notif.get("unread"),
            "subject": {
                "title": notif.get("subject", {}).get("title"),
                "type": notif.get("subject", {}).get("type"),
                "url": notif.get("subject", {}).get("url")
            },
            "repository": notif.get("repository", {}).get("full_name"),
            "updated_at": notif.get("updated_at")
        })
    
    return {"success": True, "notifications": notifications, "count": len(notifications)}


# ============================================================================
# SEARCH
# ============================================================================

def search_code(
    query: str,
    per_page: int = 30
) -> Dict[str, Any]:
    """Search code across GitHub.
    
    Args:
        query: Search query. Examples:
            - "function_name repo:owner/repo"
            - "import requests language:python org:orgname"
            - "TODO extension:py org:orgname"
        per_page: Number of results
    """
    params = {"q": query, "per_page": min(per_page, 100)}
    
    result = _github_api("search/code", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    items = []
    for item in result.get("items", []):
        items.append({
            "name": item.get("name"),
            "path": item.get("path"),
            "repository": item.get("repository", {}).get("full_name"),
            "url": item.get("html_url"),
            "sha": item.get("sha")[:7] if item.get("sha") else None
        })
    
    return {
        "success": True,
        "results": items,
        "total_count": result.get("total_count", 0),
        "count": len(items)
    }


def search_repos(
    query: str,
    sort: str = "updated",
    order: str = "desc",
    per_page: int = 30
) -> Dict[str, Any]:
    """Search repositories.
    
    Args:
        query: Search query. Examples:
            - "language:python org:orgname"
            - "topic:security stars:>100"
        sort: Sort by - "stars", "forks", "help-wanted-issues", "updated"
        order: Sort order - "asc", "desc"
        per_page: Number of results
    """
    params = {"q": query, "sort": sort, "order": order, "per_page": min(per_page, 100)}
    
    result = _github_api("search/repositories", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    repos = []
    for repo in result.get("items", []):
        repos.append({
            "full_name": repo.get("full_name"),
            "description": repo.get("description"),
            "language": repo.get("language"),
            "stargazers_count": repo.get("stargazers_count"),
            "forks_count": repo.get("forks_count"),
            "updated_at": repo.get("updated_at"),
            "url": repo.get("html_url"),
            "topics": repo.get("topics", [])
        })
    
    return {
        "success": True,
        "repositories": repos,
        "total_count": result.get("total_count", 0),
        "count": len(repos)
    }


def search_users(
    query: str,
    per_page: int = 30
) -> Dict[str, Any]:
    """Search users.
    
    Args:
        query: Search query. Examples:
            - "location:SF language:python"
            - "fullname:John type:user"
        per_page: Number of results
    """
    params = {"q": query, "per_page": min(per_page, 100)}
    
    result = _github_api("search/users", params=params)
    
    if isinstance(result, dict) and "error" in result:
        return {"success": False, "error": result.get("error")}
    
    users = []
    for user in result.get("items", []):
        users.append({
            "login": user.get("login"),
            "type": user.get("type"),
            "url": user.get("html_url")
        })
    
    return {
        "success": True,
        "users": users,
        "total_count": result.get("total_count", 0),
        "count": len(users)
    }


# ============================================================================
# MCP PROTOCOL IMPLEMENTATION
# ============================================================================

TOOLS = [
    # PRs
    {"name": "list_prs", "description": "List pull requests for a repository.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "state": {"type": "string", "default": "open"}, "sort": {"type": "string", "default": "updated"}, "direction": {"type": "string", "default": "desc"}, "per_page": {"type": "integer", "default": 30}}, "required": ["owner", "repo"]}},
    {"name": "get_pr", "description": "Get detailed information about a pull request.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "pr_number": {"type": "integer"}}, "required": ["owner", "repo", "pr_number"]}},
    {"name": "search_prs", "description": "Search PRs. Query examples: 'is:open author:user org:orgname', 'review-requested:user', 'is:merged merged:>2024-01-01'", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "sort": {"type": "string", "default": "updated"}, "order": {"type": "string", "default": "desc"}, "per_page": {"type": "integer", "default": 30}}, "required": ["query"]}},
    {"name": "create_pr", "description": "Create a pull request.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "title": {"type": "string"}, "head": {"type": "string"}, "base": {"type": "string"}, "body": {"type": "string"}, "draft": {"type": "boolean", "default": False}}, "required": ["owner", "repo", "title", "head", "base"]}},
    {"name": "merge_pr", "description": "Merge a pull request.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "pr_number": {"type": "integer"}, "merge_method": {"type": "string", "default": "squash"}, "commit_title": {"type": "string"}, "commit_message": {"type": "string"}}, "required": ["owner", "repo", "pr_number"]}},
    {"name": "pr_reviews", "description": "Get reviews for a pull request.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "pr_number": {"type": "integer"}}, "required": ["owner", "repo", "pr_number"]}},
    {"name": "request_reviewers", "description": "Request reviewers for a PR.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "pr_number": {"type": "integer"}, "reviewers": {"type": "array", "items": {"type": "string"}}}, "required": ["owner", "repo", "pr_number", "reviewers"]}},
    
    # Issues
    {"name": "list_issues", "description": "List issues for a repository.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "state": {"type": "string", "default": "open"}, "assignee": {"type": "string"}, "labels": {"type": "string"}, "sort": {"type": "string", "default": "updated"}, "per_page": {"type": "integer", "default": 30}}, "required": ["owner", "repo"]}},
    {"name": "get_issue", "description": "Get issue details.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "issue_number": {"type": "integer"}}, "required": ["owner", "repo", "issue_number"]}},
    {"name": "search_issues", "description": "Search issues. Query examples: 'is:open assignee:user org:orgname', 'label:bug', 'mentions:user'", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "sort": {"type": "string", "default": "updated"}, "order": {"type": "string", "default": "desc"}, "per_page": {"type": "integer", "default": 30}}, "required": ["query"]}},
    {"name": "create_issue", "description": "Create an issue.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "title": {"type": "string"}, "body": {"type": "string"}, "assignees": {"type": "array", "items": {"type": "string"}}, "labels": {"type": "array", "items": {"type": "string"}}}, "required": ["owner", "repo", "title"]}},
    {"name": "update_issue", "description": "Update an issue.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "issue_number": {"type": "integer"}, "title": {"type": "string"}, "body": {"type": "string"}, "state": {"type": "string"}, "assignees": {"type": "array", "items": {"type": "string"}}, "labels": {"type": "array", "items": {"type": "string"}}}, "required": ["owner", "repo", "issue_number"]}},
    {"name": "add_comment", "description": "Add comment to issue or PR.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "issue_number": {"type": "integer"}, "body": {"type": "string"}}, "required": ["owner", "repo", "issue_number", "body"]}},
    
    # Repos
    {"name": "list_repos", "description": "List repositories for user or org.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "org": {"type": "string"}, "type": {"type": "string", "default": "all"}, "sort": {"type": "string", "default": "updated"}, "per_page": {"type": "integer", "default": 30}}}},
    {"name": "get_repo", "description": "Get repository details.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}}, "required": ["owner", "repo"]}},
    {"name": "list_commits", "description": "List commits.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "sha": {"type": "string"}, "author": {"type": "string"}, "since": {"type": "string"}, "until": {"type": "string"}, "per_page": {"type": "integer", "default": 30}}, "required": ["owner", "repo"]}},
    {"name": "list_releases", "description": "List releases.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "per_page": {"type": "integer", "default": 10}}, "required": ["owner", "repo"]}},
    {"name": "get_file", "description": "Get file content.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "path": {"type": "string"}, "ref": {"type": "string"}}, "required": ["owner", "repo", "path"]}},
    {"name": "list_branches", "description": "List branches.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "per_page": {"type": "integer", "default": 30}}, "required": ["owner", "repo"]}},
    
    # Security
    {"name": "dependabot_alerts", "description": "Get Dependabot security alerts.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "state": {"type": "string", "default": "open"}, "severity": {"type": "string"}, "per_page": {"type": "integer", "default": 30}}, "required": ["owner", "repo"]}},
    {"name": "code_scanning_alerts", "description": "Get code scanning alerts.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "state": {"type": "string", "default": "open"}, "severity": {"type": "string"}, "per_page": {"type": "integer", "default": 30}}, "required": ["owner", "repo"]}},
    {"name": "secret_scanning_alerts", "description": "Get secret scanning alerts.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "state": {"type": "string", "default": "open"}, "per_page": {"type": "integer", "default": 30}}, "required": ["owner", "repo"]}},
    
    # Workflows
    {"name": "list_workflows", "description": "List workflows.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "per_page": {"type": "integer", "default": 30}}, "required": ["owner", "repo"]}},
    {"name": "list_workflow_runs", "description": "List workflow runs.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "workflow_id": {"type": "integer"}, "branch": {"type": "string"}, "actor": {"type": "string"}, "status": {"type": "string"}, "per_page": {"type": "integer", "default": 30}}, "required": ["owner", "repo"]}},
    {"name": "get_workflow_run", "description": "Get workflow run details.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "run_id": {"type": "integer"}}, "required": ["owner", "repo", "run_id"]}},
    {"name": "rerun_workflow", "description": "Re-run a workflow.", "inputSchema": {"type": "object", "properties": {"owner": {"type": "string"}, "repo": {"type": "string"}, "run_id": {"type": "integer"}}, "required": ["owner", "repo", "run_id"]}},
    
    # User
    {"name": "get_user", "description": "Get user profile.", "inputSchema": {"type": "object", "properties": {"username": {"type": "string"}}, "required": ["username"]}},
    {"name": "get_authenticated_user", "description": "Get authenticated user profile.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "list_orgs", "description": "List organizations.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "list_notifications", "description": "List notifications.", "inputSchema": {"type": "object", "properties": {"all": {"type": "boolean", "default": False}, "participating": {"type": "boolean", "default": False}, "per_page": {"type": "integer", "default": 30}}}},
    
    # Search
    {"name": "search_code", "description": "Search code. Query: 'function repo:owner/repo', 'import lang:python org:org'", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "per_page": {"type": "integer", "default": 30}}, "required": ["query"]}},
    {"name": "search_repos", "description": "Search repositories.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "sort": {"type": "string", "default": "updated"}, "order": {"type": "string", "default": "desc"}, "per_page": {"type": "integer", "default": 30}}, "required": ["query"]}},
    {"name": "search_users", "description": "Search users.", "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "per_page": {"type": "integer", "default": 30}}, "required": ["query"]}}
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
                "serverInfo": {"name": "github", "version": "1.0.0"}
            }
        }

    elif method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        tool_functions = {
            "list_prs": list_prs, "get_pr": get_pr, "search_prs": search_prs,
            "create_pr": create_pr, "merge_pr": merge_pr, "pr_reviews": pr_reviews,
            "request_reviewers": request_reviewers,
            "list_issues": list_issues, "get_issue": get_issue, "search_issues": search_issues,
            "create_issue": create_issue, "update_issue": update_issue, "add_comment": add_comment,
            "list_repos": list_repos, "get_repo": get_repo, "list_commits": list_commits,
            "list_releases": list_releases, "get_file": get_file, "list_branches": list_branches,
            "dependabot_alerts": dependabot_alerts, "code_scanning_alerts": code_scanning_alerts,
            "secret_scanning_alerts": secret_scanning_alerts,
            "list_workflows": list_workflows, "list_workflow_runs": list_workflow_runs,
            "get_workflow_run": get_workflow_run, "rerun_workflow": rerun_workflow,
            "get_user": get_user, "get_authenticated_user": get_authenticated_user,
            "list_orgs": list_orgs, "list_notifications": list_notifications,
            "search_code": search_code, "search_repos": search_repos, "search_users": search_users
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
            "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]}
        }

    elif method == "notifications/initialized":
        return None

    else:
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


def main():
    """Main MCP server loop."""
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
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": str(e)}}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()

