"""Capability status API router."""

from fastapi import APIRouter

from llm_studio.api.deps import get_api_state
from llm_studio.capabilities import get_capabilities_for_config

router = APIRouter()


@router.get("/v1/capabilities")
async def capabilities_status():
    config = get_api_state().config
    return {"capabilities": [capability.to_dict() for capability in get_capabilities_for_config(config)]}
