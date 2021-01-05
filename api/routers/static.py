import os

from fastapi import APIRouter, status
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException

static_router = APIRouter()


@static_router.get("/gstreamer/{camera_id}/{file_name}", include_in_schema=False)
async def get_video(camera_id: str, file_name: str):
    file_path = f"/repo/data/processor/static/gstreamer/{camera_id}/{file_name}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found.")
    return FileResponse(file_path)
