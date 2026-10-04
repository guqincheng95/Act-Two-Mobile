"""Runway API service.

Stage 1 keeps this module intentionally small.
The real Act-Two request shape will be implemented only after verifying
Runway's current official API contract.
"""

import os

RUNWAY_API_BASE = os.getenv("RUNWAY_API_BASE", "https://api.dev.runwayml.com")


def get_runway_api_key() -> str:
    key = os.getenv("RUNWAYML_API_SECRET")
    if not key:
        raise RuntimeError("RUNWAYML_API_SECRET is not configured")
    return key
