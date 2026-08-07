import sys
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI, Request

sys.path.insert(0, str(Path(__file__).parent.parent))

from security import RequestBodyLimitMiddleware  # noqa: E402


def build_client(limit=10):
    app = FastAPI()
    app.add_middleware(
        RequestBodyLimitMiddleware,
        route_limits={("POST", "/upload"): limit},
        default_limit=limit,
    )

    @app.post("/upload")
    async def upload(request: Request):
        body = await request.body()
        return {"size": len(body)}

    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    )


@pytest.mark.asyncio
async def test_rejects_oversized_content_length_before_route():
    async with build_client() as client:
        response = await client.post("/upload", content=b"x" * 11)
    assert response.status_code == 413
    assert response.json()["success"] is False


@pytest.mark.asyncio
async def test_accepts_body_at_limit():
    async with build_client() as client:
        response = await client.post("/upload", content=b"x" * 10)
    assert response.status_code == 200
    assert response.json() == {"size": 10}


@pytest.mark.asyncio
async def test_counts_streamed_body_without_content_length():
    async def stream():
        yield b"x" * 6
        yield b"y" * 5

    async with build_client() as client:
        response = await client.post("/upload", content=stream())
    assert response.status_code == 413
