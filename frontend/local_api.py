"""In-process adapter from Streamlit to PayAhead's application logic."""
from __future__ import annotations

import io
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import streamlit as st


def _load_deployment_secrets() -> None:
    """Expose Streamlit-managed secrets to the existing server-side services."""
    keys = (
        "DATABASE_URL", "SECRET_KEY", "JWT_SECRET_KEY", "AI_PROVIDER", "AI_API_KEY",
        "AI_MODEL", "AI_BASE_URL", "OPENAI_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY",
        "PAYPAL_CLIENT_ID", "PAYPAL_CLIENT_SECRET", "PAYPAL_BASE_URL", "PAYPAL_WEBHOOK_ID",
        "PAYPAL_CURRENCY", "PAYPAL_RETURN_URL", "PAYPAL_CANCEL_URL", "ENABLE_SCHEDULER",
        "EXPENSE_MODEL",
    )
    try:
        secrets = st.secrets
        for key in keys:
            if key in secrets and str(secrets[key]):
                os.environ[key] = str(secrets[key])
    except (FileNotFoundError, RuntimeError):
        # Local `.env` configuration remains available through backend/app.py.
        pass


_load_deployment_secrets()
BACKEND_DIR = str(Path(__file__).resolve().parents[1] / "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app as backend_app  # noqa: E402


@dataclass
class LocalResponse:
    status_code: int
    payload: dict[str, Any]

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> dict[str, Any]:
        return self.payload


def request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    files: dict[str, tuple[str, bytes, str]] | None = None,
    headers: dict[str, str] | None = None,
) -> LocalResponse:
    """Dispatch an API request through Flask in-process without opening a port."""
    route = urlsplit(path).path
    if not route.startswith("/api/"):
        route = "/api" + (route if route.startswith("/") else "/" + route)
    form_data: dict[str, Any] | None = None
    if files:
        form_data = {
            name: (filename, io.BytesIO(content), content_type)
            for name, (filename, content, content_type) in files.items()
        }
    try:
        with backend_app.test_client() as client:
            response = client.open(
                route,
                method=method.upper(),
                query_string=params,
                json=json,
                data=form_data,
                headers=headers or {},
            )
        payload = response.get_json(silent=True)
        if not isinstance(payload, dict):
            payload = {"error": "The request could not be completed."}
        return LocalResponse(response.status_code, payload)
    except Exception:
        backend_app.logger.exception("In-process request failed: %s %s", method, route)
        return LocalResponse(500, {"error": "The request could not be completed."})
