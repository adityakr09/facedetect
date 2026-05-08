from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health", summary="Liveness probe")
async def health():
    return JSONResponse({"status": "ok"})
