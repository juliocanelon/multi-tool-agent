"""Shared type definitions for the MVP agents."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class Finding:
    """Represents a security finding imported from Checkmarx."""

    project: str
    file: str
    line: int
    severity: str
    query: str
    description: str
    remediation: str


@dataclass
class CommandingConfig:
    """Configuration for the commanding agent backend."""

    provider: str
    stub_diff_path: Optional[Path] = None


@dataclass
class RepoConfig:
    """Configuration describing repository interactions."""

    path: Path
    base_branch: str
    branch_prefix: str
    push: bool = False
    create_pr: bool = False


@dataclass
class VerificationConfig:
    """Instructions for post-fix verification commands."""

    enabled: bool
    command: str
    working_directory: Path


@dataclass
class MVPConfig:
    """Top-level configuration for the MVP orchestrator."""

    checkmarx_csv: Path
    instruction_path: Path
    commanding: CommandingConfig
    repo: RepoConfig
    verification: VerificationConfig


@dataclass
class Plan:
    """A remediation plan generated from security findings."""

    findings: List[Finding] = field(default_factory=list)
    plan_path: Optional[Path] = None


@dataclass
class CommandingResponse:
    """A response payload from the commanding agent."""

    diff: Optional[str]
    provider: str


@dataclass
class VerificationResult:
    """Represents the outcome of a verification command."""

    succeeded: bool
    output: str
    command: str

