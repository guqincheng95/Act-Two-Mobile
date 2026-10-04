from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.services.runway import create_act_two_task, retrieve_task

load_dotenv()

app = FastAPI(
    title="Act-Two-Mobile API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

ALLOWED_RATIOS = {
    "1280:720",
    "720:1280",
    "960:960",
    "1104:832",
    "832:1104",
    "1584:672",
}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/tasks")
async def create_task(
    character_image: Annotated[UploadFile, File(...)],
    reference_video: Annotated[UploadFile, File(...)],
    expression_intensity: Annotated[int, Form()] = 3,
    ratio: Annotated[str, Form()] = "720:1280",
    seed: Annotated[str | None, Form()] = None,
    body_control: Annotated[bool, Form()] = True,
) -> dict[str, str]:
    if not 1 <= expression_intensity <= 5:
        raise HTTPException(status_code=400, detail="expression_intensity must be between 1 and 5")

    if ratio not in ALLOWED_RATIOS:
        raise HTTPException(status_code=400, detail="Unsupported output ratio")

    parsed_seed: int | None = None
    if seed not in (None, ""):
        try:
            parsed_seed = int(seed)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="seed must be an integer") from exc

    image_suffix = Path(character_image.filename or "character.jpg").suffix or ".jpg"
    video_suffix = Path(reference_video.filename or "reference.mp4").suffix or ".mp4"

    with tempfile.TemporaryDirectory(prefix="act-two-mobile-") as temp_dir:
        character_path = Path(temp_dir) / f"character{image_suffix}"
        reference_path = Path(temp_dir) / f"reference{video_suffix}"

        with character_path.open("wb") as dst:
            shutil.copyfileobj(character_image.file, dst)

        with reference_path.open("wb") as dst:
            shutil.copyfileobj(reference_video.file, dst)

        if character_path.stat().st_size > 200 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Character file exceeds 200MB")
        if reference_path.stat().st_size > 200 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="Reference video exceeds 200MB")

        try:
            task_id = await create_act_two_task(
                character_path=character_path,
                reference_path=reference_path,
                expression_intensity=expression_intensity,
                ratio=ratio,
                seed=parsed_seed,
                body_control=body_control,
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Runway submission failed: {exc}") from exc

    return {"id": task_id, "status": "SUBMITTED"}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    try:
        return await retrieve_task(task_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Runway task query failed: {exc}") from exc
