"""Reuse the Chapter 2 checkpoint without copying its implementation."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ch02"))

from harness import Event, Final, RunResult, SnapshotTools, ToolCall, run
from demo import FILES
from anthropic_adapter import AnthropicModel
