"""
Models for GitHub repository operations.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl


class RepositoryStatus(str, Enum):
    """Enum for repository analysis status."""
    PENDING = "pending"
    CLONING = "cloning"
    ANALYZING = "analyzing"
    DETECTING = "detecting"
    EXTRACTING = "extracting"
    COMPLETED = "completed"
    FAILED = "failed"


class RepositoryCreate(BaseModel):
    """Model for creating a repository analysis."""
    url: HttpUrl = Field(..., description="GitHub repository URL")
    branch: Optional[str] = Field(None, description="Branch to analyze (defaults to default branch)")
    include_paths: Optional[List[str]] = Field(None, description="Paths to include in analysis")
    exclude_paths: Optional[List[str]] = Field(None, description="Paths to exclude from analysis")
    detect_formats: Optional[List[str]] = Field(None, description="Formats to detect (if empty, all formats are detected)")
    description: Optional[str] = Field(None, description="Optional description for this analysis")
    options: Optional[Dict[str, str]] = Field(None, description="Additional options for the analysis")


class RepositoryDB(BaseModel):
    """Database model for a repository analysis."""
    id: str = Field(..., description="Unique identifier")
    url: HttpUrl = Field(..., description="GitHub repository URL")
    owner: str = Field(..., description="Repository owner")
    name: str = Field(..., description="Repository name")
    branch: str = Field(..., description="Branch being analyzed")
    status: RepositoryStatus = Field(RepositoryStatus.PENDING, description="Current status of the analysis")
    include_paths: List[str] = Field(default_factory=list, description="Paths included in analysis")
    exclude_paths: List[str] = Field(default_factory=list, description="Paths excluded from analysis")
    detect_formats: List[str] = Field(default_factory=list, description="Formats to detect")
    description: Optional[str] = Field(None, description="Description for this analysis")
    options: Dict[str, str] = Field(default_factory=dict, description="Additional options")
    file_count: int = Field(0, description="Number of files scanned")
    format_counts: Dict[str, int] = Field(default_factory=dict, description="Count of detected formats")
    schema_counts: Dict[str, int] = Field(default_factory=dict, description="Count of extracted schemas")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True


class RepositoryResponse(RepositoryDB):
    """Response model for a repository analysis."""
    pass


class RepositoryUpdate(BaseModel):
    """Model for updating a repository analysis."""
    description: Optional[str] = Field(None, description="Description for this analysis")
    options: Optional[Dict[str, str]] = Field(None, description="Additional options")
    include_paths: Optional[List[str]] = Field(None, description="Paths to include in analysis")
    exclude_paths: Optional[List[str]] = Field(None, description="Paths to exclude from analysis")
    detect_formats: Optional[List[str]] = Field(None, description="Formats to detect")


class FileInfo(BaseModel):
    """Model for file information."""
    path: str = Field(..., description="File path within repository")
    size: int = Field(..., description="File size in bytes")
    format_id: Optional[str] = Field(None, description="Detected format ID")
    confidence: Optional[float] = Field(None, description="Format detection confidence")
    schema_id: Optional[str] = Field(None, description="Extracted schema ID")
    error: Optional[str] = Field(None, description="Error message if processing failed")
