from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from runwayml import AsyncRunwayML


def get_client() -> AsyncRunwayML:
    api_key = os.getenv("RUNWAYML_API_SECRET")
    if not api_key:
        raise RuntimeError("RUNWAYML_API_SECRET is not configured")
    return AsyncRunwayML(api_key=api_key)


async def upload_ephemeral(path: Path) -> str:
    client = get_client()
    response = await client.uploads.create_ephemeral(file=path)
    return response.uri


async def create_act_two_task(
    *,
    character_path: Path,
    reference_path: Path,
    expression_intensity: int = 3,
    ratio: str = "720:1280",
    seed: int | None = None,
    body_control: bool = True,
) -> str:
    client = get_client()

    character_uri = await upload_ephemeral(character_path)
    reference_uri = await upload_ephemeral(reference_path)

    params: dict[str, Any] = {
        "model": "act_two",
        "character": {"type": "image", "uri": character_uri},
        "reference": {"type": "video", "uri": reference_uri},
        "expression_intensity": expression_intensity,
        "ratio": ratio,
        "body_control": body_control,
    }
    if seed is not None:
        params["seed"] = seed

    task = await client.character_performance.create(**params)
    return task.id


async def retrieve_task(task_id: str) -> dict[str, Any]:
    client = get_client()
    task = await client.tasks.retrieve(task_id)

    if hasattr(task, "model_dump"):
        return task.model_dump(mode="json", by_alias=True, exclude_none=True)

    return {
        "id": getattr(task, "id", task_id),
        "status": getattr(task, "status", "UNKNOWN"),
        "output": getattr(task, "output", None),
        "failure": getattr(task, "failure", None),
        "failureCode": getattr(task, "failure_code", None),
    }
