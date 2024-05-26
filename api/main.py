from core.config import config
from fastapi import APIRouter

from .routes import auth, users, clubs

router = APIRouter()

router.include_router(auth.router, prefix=config.API_PREFIX_AUTH, tags=["auth"])
router.include_router(users.route, prefix=config.API_PREFIX_USERS, tags=["users"])
router.include_router(clubs.route, prefix=config.API_PREFIX_CLUBS, tags=["clubs"])
