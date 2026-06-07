from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from routers.frontend_api import LoginRequest, frontend_sign_in

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def mount_frontend(app: FastAPI) -> None:
    static_path = PROJECT_ROOT / "project" / "templates" / "static"
    if static_path.exists():
        app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

    @app.get("/", include_in_schema=False)
    async def frontend_index():
        html_path = PROJECT_ROOT / "project" / "frontend" / "index.html"
        return HTMLResponse(
            html_path.read_text(encoding="utf-8"),
            headers={"Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"},
        )

    @app.post("/sign-in", include_in_schema=False)
    async def frontend_compat_sign_in(payload: LoginRequest):
        return await frontend_sign_in(payload)
