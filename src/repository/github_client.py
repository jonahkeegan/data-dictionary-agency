"""
GitHub client for repository operations.
"""
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import git
from github import Github, GithubException
from github.Repository import Repository

from src.core.config import settings


logger = logging.getLogger(__name__)


class GitHubClient:
    """Client for GitHub operations."""

    def __init__(self, token: Optional[str] = None):
        """Initialize the GitHub client.
        
        Args:
            token: GitHub API token. If None, uses the token from settings.
        """
        self.token = token or settings.GITHUB_TOKEN
        if not self.token:
            logger.warning("No GitHub token provided, API rate limits may be restrictive")
        
        self.github = Github(self.token, base_url=settings.GITHUB_API_URL)
        logger.debug("Initialized GitHub client with API URL: %s", settings.GITHUB_API_URL)

    def get_repository(self, owner: str, name: str) -> Repository:
        """Get a GitHub repository.
        
        Args:
            owner: Repository owner (user or organization).
            name: Repository name.
            
        Returns:
            Repository: GitHub repository object.
            
        Raises:
            GithubException: If repository not found or API error.
        """
        return self.github.get_repo(f"{owner}/{name}")

    def get_repository_from_url(self, url: str) -> Repository:
        """Get a GitHub repository from URL.
        
        Args:
            url: GitHub repository URL.
            
        Returns:
            Repository: GitHub repository object.
            
        Raises:
            ValueError: If URL is not a valid GitHub repository URL.
            GithubException: If repository not found or API error.
        """
        # Parse URL to extract owner and name
        parsed_url = urlparse(url)
        
        # Check if URL is a GitHub URL
        if not parsed_url.netloc.endswith("github.com"):
            raise ValueError(f"Not a GitHub URL: {url}")
        
        # Extract owner and name from path
        path_parts = parsed_url.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub repository URL: {url}")
        
        owner = path_parts[0]
        name = path_parts[1]
        
        return self.get_repository(owner, name)

    def clone_repository(
        self, 
        repository: Repository, 
        branch: Optional[str] = None,
        depth: Optional[int] = None,
        local_path: Optional[str] = None,
    ) -> str:
        """Clone a GitHub repository to local filesystem.
        
        Args:
            repository: GitHub repository object.
            branch: Branch to clone (default: repository's default branch).
            depth: Clone depth (default: full clone).
            local_path: Local path to clone to (default: temporary directory).
            
        Returns:
            str: Path to cloned repository.
            
        Raises:
            git.GitError: If cloning fails.
        """
        # Determine branch to clone
        branch = branch or repository.default_branch
        
        # Create temporary directory if local_path not provided
        if local_path is None:
            local_path = tempfile.mkdtemp(prefix=f"dda-{repository.name}-")
        
        logger.info(
            "Cloning repository %s/%s (branch: %s) to %s",
            repository.owner.login,
            repository.name,
            branch,
            local_path,
        )
        
        # Prepare clone URL with authentication if token is provided
        clone_url = repository.clone_url
        if self.token:
            clone_url = clone_url.replace(
                "https://", f"https://{self.token}@"
            )
        
        # Clone options
        clone_options = ["--branch", branch]
        if depth:
            clone_options.extend(["--depth", str(depth)])
        
        # Clone repository
        git.Repo.clone_from(clone_url, local_path, multi_options=clone_options)
        
        return local_path

    def list_repository_files(
        self,
        repository: Repository,
        path: str = "",
        ref: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List files in a GitHub repository.
        
        Args:
            repository: GitHub repository object.
            path: Path within repository to list files from.
            ref: Git reference (branch, tag, commit) to list files from.
            
        Returns:
            List[Dict[str, Any]]: List of file information dictionaries.
            
        Raises:
            GithubException: If path not found or API error.
        """
        try:
            contents = repository.get_contents(path, ref=ref)
            files = []
            
            while contents:
                content = contents.pop(0)
                if content.type == "dir":
                    # Add subdirectory contents to the queue
                    contents.extend(repository.get_contents(content.path, ref=ref))
                else:
                    # Add file information to the result
                    files.append({
                        "name": content.name,
                        "path": content.path,
                        "sha": content.sha,
                        "size": content.size,
                        "type": content.type,
                        "download_url": content.download_url,
                    })
            
            return files
        
        except GithubException as e:
            logger.error(
                "Failed to list files in repository %s/%s (path: %s, ref: %s): %s",
                repository.owner.login,
                repository.name,
                path,
                ref,
                e,
            )
            raise

    def get_file_content(
        self,
        repository: Repository,
        path: str,
        ref: Optional[str] = None,
    ) -> bytes:
        """Get content of a file in a GitHub repository.
        
        Args:
            repository: GitHub repository object.
            path: Path to file within repository.
            ref: Git reference (branch, tag, commit).
            
        Returns:
            bytes: File content.
            
        Raises:
            GithubException: If file not found or API error.
        """
        try:
            content = repository.get_contents(path, ref=ref)
            return content.decoded_content
        
        except GithubException as e:
            logger.error(
                "Failed to get file content from repository %s/%s (path: %s, ref: %s): %s",
                repository.owner.login,
                repository.name,
                path,
                ref,
                e,
            )
            raise
