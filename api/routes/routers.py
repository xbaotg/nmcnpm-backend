from core.config import config
from fastapi import APIRouter

from . import auth, users

router = APIRouter()

router.include_router(auth.router, prefix=config.API_PREFIX_AUTH, tags=["auth"])
router.include_router(users.route, prefix=config.API_PREFIX_USERS, tags=["users"])
