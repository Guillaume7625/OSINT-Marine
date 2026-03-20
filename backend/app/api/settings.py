from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.domain.models import AppSetting, PromptProfile
from app.domain.schemas import DevSettingsRead, DevSettingsUpdate, PromptProfileRead

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/dev", response_model=DevSettingsRead)
def get_dev_settings(db: Session = Depends(get_db), settings: Settings = Depends(get_settings)):
    profile = _get_or_create_active_profile(db=db, settings=settings)
    routing_defaults = _get_or_create_routing_defaults(db=db, settings=settings)
    db.commit()
    return DevSettingsRead(
        prompt_profile=PromptProfileRead.model_validate(profile),
        routing_defaults=routing_defaults,
    )


@router.put("/dev", response_model=DevSettingsRead)
def update_dev_settings(
    payload: DevSettingsUpdate,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    if settings.app_env != "dev":
        raise HTTPException(status_code=403, detail="Settings update endpoint is only enabled in dev")

    profile = _get_or_create_active_profile(db=db, settings=settings)
    if payload.prompt:
        if payload.prompt.global_prompt is not None:
            profile.global_prompt = payload.prompt.global_prompt
        if payload.prompt.workspace_prompt is not None:
            profile.workspace_prompt = payload.prompt.workspace_prompt

    routing_defaults = _get_or_create_routing_defaults(db=db, settings=settings)
    if payload.routing_defaults:
        routing_defaults.update(payload.routing_defaults)
        record = db.query(AppSetting).filter(AppSetting.key == "routing_defaults").one()
        record.value = routing_defaults

    db.commit()

    return DevSettingsRead(
        prompt_profile=PromptProfileRead.model_validate(profile),
        routing_defaults=routing_defaults,
    )


def _get_or_create_active_profile(*, db: Session, settings: Settings) -> PromptProfile:
    profile = db.query(PromptProfile).filter(PromptProfile.is_active.is_(True)).first()
    if profile:
        return profile

    profile = PromptProfile(
        name="default",
        global_prompt=settings.bootstrap_global_prompt,
        workspace_prompt=settings.bootstrap_workspace_prompt,
        is_active=True,
    )
    db.add(profile)
    db.flush()
    return profile


def _get_or_create_routing_defaults(*, db: Session, settings: Settings) -> dict:
    record = db.query(AppSetting).filter(AppSetting.key == "routing_defaults").one_or_none()
    if record:
        return record.value

    defaults = {
        "mode": settings.default_routing_mode,
        "model_fast": settings.anthropic_model_fast,
        "model_default": settings.anthropic_model_default,
        "model_complex": settings.anthropic_model_complex,
    }
    db.add(AppSetting(key="routing_defaults", value=defaults))
    db.flush()
    return defaults
