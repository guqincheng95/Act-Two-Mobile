from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.services.runway import (
    create_act_two_task,
    create_act_two_task_from_uris,
    create_ephemeral_upload_slot,
    retrieve_task,
)

load_dotenv()

app = FastAPI(
    title="Act-Two-Mobile API",
    version="0.2.1",
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
    return {"status": "ok", "version": "0.2.1", "directUpload": "enabled", "characterVideo": "enabled"}


class UploadInitRequest(BaseModel):
    filename: str


class DirectTaskRequest(BaseModel):
    character_uri: str
    reference_uri: str
    character_type: str = "image"
    expression_intensity: int = 3
    ratio: str = "720:1280"
    seed: int | None = None
    body_control: bool = True


@app.post("/api/uploads/init")
async def init_upload(request: UploadInitRequest) -> dict:
    if not request.filename or len(request.filename) > 255:
        raise HTTPException(status_code=400, detail="Invalid filename")
    try:
        return await create_ephemeral_upload_slot(request.filename)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Runway upload init failed: {exc}") from exc


@app.post("/api/tasks/direct")
async def create_direct_task(request: DirectTaskRequest) -> dict:
    if not 1 <= request.expression_intensity <= 5:
        raise HTTPException(status_code=400, detail="expression_intensity must be between 1 and 5")
    if request.ratio not in ALLOWED_RATIOS:
        raise HTTPException(status_code=400, detail="Unsupported output ratio")
    if request.character_type not in {"image", "video"}:
        raise HTTPException(status_code=400, detail="character_type must be image or video")
    if not request.character_uri.startswith("runway://") or not request.reference_uri.startswith("runway://"):
        raise HTTPException(status_code=400, detail="Direct task requires runway:// asset URIs")

    try:
        task_id = await create_act_two_task_from_uris(
            character_uri=request.character_uri,
            reference_uri=request.reference_uri,
            character_type=request.character_type,
            expression_intensity=request.expression_intensity,
            ratio=request.ratio,
            seed=request.seed,
            body_control=(request.body_control if request.character_type == "image" else False),
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Runway submission failed: {exc}") from exc

    return {
        "id": task_id,
        "status": "SUBMITTED",
        "debug": {
            "model": "act_two",
            "character_type": request.character_type,
            "reference_type": "video",
            "expression_intensity": request.expression_intensity,
            "body_control": (request.body_control if request.character_type == "image" else False),
            "ratio": request.ratio,
            "seed": request.seed,
        },
    }


@app.post("/api/tasks")
async def create_task(
    character_file: Annotated[UploadFile, File(...)],
    reference_video: Annotated[UploadFile, File(...)],
    character_type: Annotated[str, Form()] = "image",
    expression_intensity: Annotated[int, Form()] = 3,
    ratio: Annotated[str, Form()] = "720:1280",
    seed: Annotated[str | None, Form()] = None,
    body_control: Annotated[bool, Form()] = True,
) -> dict:
    if character_type not in {"image", "video"}:
        raise HTTPException(status_code=400, detail="character_type must be image or video")

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

    image_suffix = Path(character_file.filename or "character.jpg").suffix or ".jpg"
    video_suffix = Path(reference_video.filename or "reference.mp4").suffix or ".mp4"

    with tempfile.TemporaryDirectory(prefix="act-two-mobile-") as temp_dir:
        character_path = Path(temp_dir) / f"character{image_suffix}"
        reference_path = Path(temp_dir) / f"reference{video_suffix}"

        with character_path.open("wb") as dst:
            shutil.copyfileobj(character_file.file, dst)

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
                character_type=character_type,
                expression_intensity=expression_intensity,
                ratio=ratio,
                seed=parsed_seed,
                body_control=(body_control if character_type == "image" else False),
            )
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Runway submission failed: {exc}") from exc

    return {
        "id": task_id,
        "status": "SUBMITTED",
        "debug": {
            "model": "act_two",
            "character_type": character_type,
            "reference_type": "video",
            "expression_intensity": expression_intensity,
            "body_control": (body_control if character_type == "image" else False),
            "ratio": ratio,
            "seed": parsed_seed,
        },
    }


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str) -> dict:
    try:
        return await retrieve_task(task_id)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Runway task query failed: {exc}") from exc
