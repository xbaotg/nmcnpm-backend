from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.routers import router
import argparse
import uvicorn


def get_application() -> FastAPI:
    app = FastAPI()

    # TODO: fix origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # register routers
    app.include_router(router)

    return app


app = get_application()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=3000)
    parser.add_argument("--reload", type=bool, default=False)
    args = parser.parse_args()

    uvicorn.run("main:app", host=args.host, port=args.port, reload=args.reload)
