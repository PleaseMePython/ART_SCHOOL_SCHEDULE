"""Агрегатор API."""

from fastapi import APIRouter

from src.api.schedule import router as schedule_router

api_router = APIRouter()
api_router.include_router(schedule_router, tags=['schedule'])
