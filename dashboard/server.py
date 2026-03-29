"""
DuberyMNL Command Center -- FastAPI Backend
Wraps existing CLI tools as HTTP endpoints for the dashboard UI.
"""
import json
import os
import sys
import time
import asyncio
import requests
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
TMP = PROJECT_DIR / ".tmp"
PIPELINE_FILE = TMP / "pipeline.json"
DASHBOARD_DATA = Path(__file__).resolve().parent / "dubery-dashboard-data.json"
IMAGES_DIR = TMP / "images"

load_dotenv(PROJECT_DIR / ".env")

app = FastAPI(title="DuberyMNL Command Center", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve dashboard static files
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent)), name="static")


# === Models ===

class GenerateRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "1:1"
    resolution: str = "1K"
    caption_id: str | None = None
    image_input: list[str] | None = None


class ApproveRequest(BaseModel):
    rating: int | None = 5


class RejectRequest(BaseModel):
    reason: str | None = ""


# === Helpers ===

def load_pipeline():
    if PIPELINE_FILE.exists():
        return json.loads(PIPELINE_FILE.read_text())
    return []


def save_pipeline(data):
    PIPELINE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def find_item(pipeline, caption_id):
    for item in pipeline:
        if str(item.get("id")) == str(caption_id):
            return item
    return None


def rebuild_dashboard_data():
    """Run the build script to regenerate dashboard data."""
    import subprocess
    result = subprocess.run(
        [sys.executable, str(PROJECT_DIR / "tools" / "build_dubery_dashboard.py")],
        capture_output=True, text=True, timeout=30
    )
    return result.returncode == 0


# === Routes ===

@app.get("/")
async def root():
    return FileResponse(str(Path(__file__).resolve().parent / "index.html"))


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "pipeline_items": len(load_pipeline()),
        "kie_key": bool(os.getenv("KIE_AI_API_KEY")),
        "meta_token": bool(os.getenv("META_ADS_ACCESS_TOKEN")),
    }


@app.get("/api/pipeline")
async def get_pipeline():
    pipeline = load_pipeline()
    from collections import Counter
    statuses = Counter(item.get("status", "unknown") for item in pipeline)
    return {
        "total": len(pipeline),
        "by_status": dict(statuses),
        "items": pipeline,
    }


@app.get("/api/pipeline/{caption_id}")
async def get_pipeline_item(caption_id: str):
    pipeline = load_pipeline()
    item = find_item(pipeline, caption_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Caption {caption_id} not found")
    return item


@app.get("/api/dashboard-data")
async def get_dashboard_data():
    if DASHBOARD_DATA.exists():
        return json.loads(DASHBOARD_DATA.read_text())
    raise HTTPException(status_code=404, detail="Dashboard data not found. Run build script.")


@app.post("/api/dashboard-data/rebuild")
async def rebuild_data():
    success = rebuild_dashboard_data()
    if success:
        return {"status": "ok", "message": "Dashboard data rebuilt"}
    raise HTTPException(status_code=500, detail="Build script failed")


@app.post("/api/generate")
async def generate_image(req: GenerateRequest):
    """Submit an image generation job to kie.ai. Returns task ID for polling."""
    api_key = os.getenv("KIE_AI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="KIE_AI_API_KEY not configured")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": "nano-banana-2",
        "input": {
            "prompt": req.prompt,
            "aspect_ratio": req.aspect_ratio,
            "resolution": req.resolution,
            "output_format": "jpg",
        },
    }

    # Upload reference images if provided
    if req.image_input:
        sys.path.insert(0, str(PROJECT_DIR / "tools" / "image_gen"))
        from generate_kie import upload_images_to_kie
        uploaded = upload_images_to_kie(req.image_input, api_key, headers)
        if uploaded:
            payload["input"]["image_input"] = uploaded

    try:
        resp = requests.post(
            "https://api.kie.ai/api/v1/jobs/createTask",
            headers=headers, json=payload, timeout=30
        )
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"kie.ai API error: {e}")

    task_id = result.get("data", {}).get("taskId")
    if not task_id:
        raise HTTPException(status_code=502, detail=f"No taskId returned: {result}")

    return {
        "status": "submitted",
        "task_id": task_id,
        "caption_id": req.caption_id,
        "message": "Image generation started. Poll /api/generate/status/{task_id} for progress.",
    }


@app.get("/api/generate/status/{task_id}")
async def check_generation(task_id: str):
    """Poll kie.ai for generation status."""
    api_key = os.getenv("KIE_AI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="KIE_AI_API_KEY not configured")

    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        resp = requests.get(
            "https://api.kie.ai/api/v1/jobs/recordInfo",
            headers=headers, params={"taskId": task_id}, timeout=15
        )
        resp.raise_for_status()
        data = resp.json().get("data", {})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Poll error: {e}")

    state = data.get("state", "unknown")

    if state in ("success", "completed"):
        result_json = json.loads(data.get("resultJson", "{}"))
        result_urls = result_json.get("resultUrls", [])
        image_url = result_urls[0] if result_urls else None
        return {"status": "completed", "image_url": image_url, "task_id": task_id}

    if state in ("failed", "error"):
        return {"status": "failed", "error": data.get("errorMsg", "Unknown error"), "task_id": task_id}

    return {"status": "processing", "state": state, "task_id": task_id}


@app.post("/api/approve/{caption_id}")
async def approve_image(caption_id: str, req: ApproveRequest):
    pipeline = load_pipeline()
    item = find_item(pipeline, caption_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Caption {caption_id} not found")

    item["status"] = "IMAGE_APPROVED"
    if req.rating:
        item["rating"] = req.rating
    save_pipeline(pipeline)
    rebuild_dashboard_data()

    return {"status": "ok", "caption_id": caption_id, "new_status": "IMAGE_APPROVED"}


@app.post("/api/reject/{caption_id}")
async def reject_image(caption_id: str, req: RejectRequest):
    pipeline = load_pipeline()
    item = find_item(pipeline, caption_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Caption {caption_id} not found")

    item["status"] = "REJECTED"
    item["reject_reason"] = req.reason
    save_pipeline(pipeline)
    rebuild_dashboard_data()

    return {"status": "ok", "caption_id": caption_id, "new_status": "REJECTED"}


@app.get("/api/queue")
async def get_queue():
    """Get items ready for image generation (PENDING with prompts)."""
    pipeline = load_pipeline()
    queue = [
        item for item in pipeline
        if item.get("status") in ("PENDING", "PROMPT_READY")
    ]
    return {"count": len(queue), "items": queue}


@app.get("/api/approved")
async def get_approved():
    """Get approved images ready for ad staging."""
    pipeline = load_pipeline()
    approved = [
        item for item in pipeline
        if item.get("status") == "IMAGE_APPROVED"
    ]
    return {"count": len(approved), "items": approved}


@app.get("/api/images/{filename}")
async def serve_image(filename: str):
    """Serve generated images from .tmp/images/"""
    path = IMAGES_DIR / filename
    if not path.exists():
        # Try output/images
        path = PROJECT_DIR / "output" / "images" / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(str(path))


if __name__ == "__main__":
    import uvicorn
    print(f"Starting DuberyMNL Command Center on http://localhost:8000")
    print(f"Project: {PROJECT_DIR}")
    print(f"Pipeline: {PIPELINE_FILE} ({len(load_pipeline())} items)")
    uvicorn.run(app, host="0.0.0.0", port=8000)
