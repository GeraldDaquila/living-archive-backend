"""FSD route registration for the existing USE application."""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

def register_fsd_routes(app, use_core):
    if any(getattr(route, "path", "") == "/api/fsd/analyze" for route in app.routes):
        return
    @app.post("/api/fsd/analyze")
    async def fsd_analyze(request: Request):
        return JSONResponse(status_code=503, content={"ok": False, "error": "fsd_not_configured"})
