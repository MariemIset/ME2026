"""HTTP clients for the BO1 (churn) and BO2 (loyalty) backends.

Each client wraps `requests.Session` with:
* shared timeout from settings,
* automatic retries with exponential backoff (`tenacity`),
* structured logging,
* typed return values (DataFrame or dict).

The clients never raise on application errors silently — they raise
``ApiError`` so the Streamlit views can render a friendly message.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import pandas as pd
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from streamlit_ui.config import get_settings
from streamlit_ui.logging_config import get_logger

logger = get_logger(__name__)


class ApiError(RuntimeError):
    """Raised when an API call fails after all retries."""


@dataclass
class HealthStatus:
    ok: bool
    detail: dict[str, Any]


def _retry():
    s = get_settings()
    return retry(
        retry=retry_if_exception_type(
            (requests.ConnectionError, requests.Timeout)
        ),
        stop=stop_after_attempt(s.api_retry_attempts),
        wait=wait_exponential(multiplier=s.api_retry_backoff, min=1, max=30),
        reraise=True,
    )


class _BaseClient:
    def __init__(self, base_url: str):
        s = get_settings()
        self.base_url = base_url.rstrip("/")
        self.timeout = s.api_timeout_seconds
        self.session = requests.Session()

    def _url(self, path: str) -> str:
        return f"{self.base_url}{path}"

    @_retry()
    def _get(self, path: str) -> Any:
        try:
            r = self.session.get(self._url(path), timeout=self.timeout)
        except requests.RequestException as e:
            logger.error("api_get_failed", path=path, error=str(e))
            raise
        if r.status_code >= 400:
            raise ApiError(f"GET {path} → {r.status_code}: {r.text[:200]}")
        return r.json()

    @_retry()
    def _post(self, path: str, payload: dict[str, Any]) -> Any:
        try:
            r = self.session.post(
                self._url(path), json=payload, timeout=self.timeout,
            )
        except requests.RequestException as e:
            logger.error("api_post_failed", path=path, error=str(e))
            raise
        if r.status_code >= 400:
            raise ApiError(f"POST {path} → {r.status_code}: {r.text[:200]}")
        return r.json()

    def health(self) -> HealthStatus:
        try:
            data = self._get("/health")
            ok = bool(data.get("status") == "ok")
            return HealthStatus(ok=ok, detail=data)
        except Exception as e:  # noqa: BLE001
            return HealthStatus(ok=False, detail={"error": str(e)})


class ChurnClient(_BaseClient):
    """Client for the BO1 churn FastAPI service."""

    def __init__(self):
        super().__init__(get_settings().churn_api_url)

    def model_info(self) -> dict[str, Any]:
        return self._get("/model/info")

    def predict_by_ids(
        self,
        loyalty_numbers: list[int],
        as_of_date: date | None = None,
    ) -> pd.DataFrame:
        if not loyalty_numbers:
            raise ApiError("loyalty_numbers must not be empty.")
        payload: dict[str, Any] = {"loyalty_numbers": loyalty_numbers}
        if as_of_date is not None:
            payload["as_of_date"] = as_of_date.isoformat()

        logger.info("churn_predict_call", n=len(loyalty_numbers))
        data = self._post("/predict/by-loyalty-id", payload)
        df = pd.DataFrame(data)
        if df.empty:
            return df
        df["churn_probability"] = df["churn_probability"].astype(float)
        logger.info("churn_predict_done", rows=len(df))
        return df


class LoyaltyClient(_BaseClient):
    """Client for the BO2 loyalty FastAPI service."""

    def __init__(self):
        super().__init__(get_settings().loyalty_api_url)

    def models_info(self) -> dict[str, Any]:
        return self._get("/models/info")

    def recommend(
        self,
        loyalty_numbers: list[int],
        as_of_date: date | None = None,
        top_k: int = 3,
    ) -> pd.DataFrame:
        if not loyalty_numbers:
            raise ApiError("loyalty_numbers must not be empty.")
        payload: dict[str, Any] = {
            "loyalty_numbers": loyalty_numbers,
            "top_k": int(top_k),
        }
        if as_of_date is not None:
            payload["as_of_date"] = as_of_date.isoformat()

        logger.info("loyalty_recommend_call", n=len(loyalty_numbers), top_k=top_k)
        data = self._post("/recommend/by-loyalty-id", payload)
        df = pd.DataFrame(data)
        if df.empty:
            return df
        for c in ("redemption_proba", "uplift_score", "expected_value"):
            if c in df.columns:
                df[c] = df[c].astype(float)
        logger.info("loyalty_recommend_done", rows=len(df))
        return df
