"""
CivicPulse — Model Registry

Manages model versions, loading, and A/B rollout.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)

ML_MODEL_PATH = os.environ.get("ML_MODEL_PATH", "/models/fusion/latest/")


class ModelRegistry:
    """Tracks trained model versions and manages rollout."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or ML_MODEL_PATH
        self.active_version: Optional[str] = None
        self.registry: list[dict] = []

    def register(self, version: str, metrics: dict, model_path: str) -> None:
        """Register a new model version with its metrics."""
        entry = {
            "version": version,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "model_path": model_path,
            "metrics": metrics,
            "status": "registered",
        }
        self.registry.append(entry)
        logger.info("Registered model version: %s", version)

    def promote(self, version: str) -> None:
        """Promote a model version to active."""
        for entry in self.registry:
            if entry["version"] == version:
                entry["status"] = "active"
                self.active_version = version
                logger.info("Promoted model version to active: %s", version)
                return
            elif entry["status"] == "active":
                entry["status"] = "retired"

        raise ValueError(f"Version {version} not found in registry")

    def get_active_version(self) -> Optional[dict]:
        """Get the currently active model version."""
        for entry in self.registry:
            if entry["status"] == "active":
                return entry
        return None

    def list_versions(self) -> list[dict]:
        """List all registered model versions."""
        return self.registry

    def save_registry(self, path: Optional[str] = None) -> None:
        """Save registry to disk."""
        save_path = path or os.path.join(self.base_path, "registry.json")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(self.registry, f, indent=2, default=str)

    def load_registry(self, path: Optional[str] = None) -> None:
        """Load registry from disk."""
        load_path = path or os.path.join(self.base_path, "registry.json")
        if os.path.exists(load_path):
            with open(load_path) as f:
                self.registry = json.load(f)
            # Find active version
            for entry in self.registry:
                if entry.get("status") == "active":
                    self.active_version = entry["version"]
