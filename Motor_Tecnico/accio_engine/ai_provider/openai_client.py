"""Cliente OpenAI (fallback opcional — API compatible /v1)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

OPENAI_DEFAULT_BASE = "https://api.openai.com/v1"


def resolve_openai_api_key() -> str:
    return (
        os.getenv("OPENAI_API_KEY", "").strip()
        or os.getenv("ACCIO_AI_API_KEY", "").strip()
    )


def openai_configured() -> bool:
    return bool(resolve_openai_api_key())


def chat_completions(
    *,
    api_key: str,
    body: dict[str, Any],
    base_url: str | None = None,
    timeout_sec: int = 90,
) -> dict[str, Any]:
    root = (base_url or os.getenv("ACCIO_AI_BASE_URL", "").strip() or OPENAI_DEFAULT_BASE).rstrip("/")
    url = f"{root}/chat/completions"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"OpenAI HTTP {exc.code}: {err_body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI unreachable: {exc.reason}") from exc
