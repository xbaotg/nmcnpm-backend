from core.config import config
from fastapi import APIRouter

from .routes import auth, users, players, referees, clubs, params, matches, events

router = APIRouter()

router.include_router(auth.router, prefix=config.API_PREFIX_AUTH, tags=["auth"])
router.include_router(matches.route, prefix=config.API_PREFIX_MATCHES, tags=["matches"])
router.include_router(params.route, prefix=config.API_PREFIX_PARAMS, tags=["params"])
router.include_router(users.route, prefix=config.API_PREFIX_USERS, tags=["users"])
router.include_router(players.route, prefix=config.API_PREFIX_PLAYERS, tags=["players"])
router.include_router(clubs.route, prefix=config.API_PREFIX_CLUBS, tags=["clubs"])
router.include_router(referees.route, prefix=config.API_PREFIX_REFEREES, tags=["referees"])
