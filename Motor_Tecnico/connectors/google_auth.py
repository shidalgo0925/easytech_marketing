#!/usr/bin/env python3
"""Token de acceso Google desde refresh token en .env."""

from __future__ import annotations

import os

import requests
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


def google_access_token() -> str:
    refresh = os.getenv("GOOGLE_OAUTH_REFRESH_TOKEN", "").strip()
    if not refresh:
        raise RuntimeError("Falta GOOGLE_OAUTH_REFRESH_TOKEN — conectar en /google/")
    client_id = os.getenv("GOOGLE_CLIENT_ID", "").strip()
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise RuntimeError("Faltan GOOGLE_CLIENT_ID o GOOGLE_CLIENT_SECRET")
    resp = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    if not resp.ok:
        raise RuntimeError(f"Google token error {resp.status_code}: {resp.text[:200]}")
    return resp.json()["access_token"]
