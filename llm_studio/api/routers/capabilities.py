"""Capability status API router."""

from fastapi import APIRouter

from llm_studio.capabilities import get_capabilities

router = APIRouter()


@router.get("/v1/capabilities")
async def capabilities_status():
    return {"capabilities": [capability.to_dict() for capability in get_capabilities()]}
