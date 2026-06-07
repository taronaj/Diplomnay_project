import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from configs.config import settings
from core.admin_panel import register_admin_panel
from core.exceptions import register_exception_handlers
from core.frontend import mount_frontend
from core.logging import request_logging_middleware
from core.rate_limit import InMemoryRateLimiter
from core.router_registry import include_api_routers
from core.startup import run_startup_tasks


def create_app() -> FastAPI:
    run_startup_tasks()

    app = FastAPI(title="Учебная платформа", version="3.0.0")

    app.middleware("http")(
        InMemoryRateLimiter(
            max_requests=settings.rate_limit_requests,
            window_seconds=settings.rate_limit_window_seconds,
        )
    )
    app.middleware("http")(request_logging_middleware)
    register_exception_handlers(app)

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.auth.secret_key,
        session_cookie="admin_session",
    )

    mount_frontend(app)
    register_admin_panel(app)
    include_api_routers(app)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, port=settings.port, host=settings.host)
