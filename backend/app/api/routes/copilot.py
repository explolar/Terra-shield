"""GeoCopilot endpoints — natural-language climate-risk querying."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ...schemas.modules import CopilotRequest
from ...services import copilot, llm
from ..deps import rate_limit

router = APIRouter(prefix="/copilot", tags=["GeoCopilot"], dependencies=[Depends(rate_limit)])


@router.get("/tools")
def tools() -> dict:
    return {"tools": copilot.tools_manifest(), "llm": llm.status()}


@router.post("/ask")
async def ask(req: CopilotRequest) -> dict:
    aoi = req.aoi.to_engine() if req.aoi else None
    return await copilot.ask(req.question, aoi)
