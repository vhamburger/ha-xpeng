"""XPENG Open Platform API client for Home Assistant."""
from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

API_PRODUCTION_URL = "https://open.xpeng.com/open/oauth2/queryData"
API_UAT_URL = "https://open-eu.uat.xpeng.com/open/oauth2/queryData"


class XpengApiClient:
    """Client to communicate with the XPENG Open Platform API."""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        open_id: str,
        access_token: str,
        session: aiohttp.ClientSession,
        use_uat: bool = False,
    ) -> None:
        """Initialize the API client."""
        self._app_id = app_id
        self._app_secret = app_secret
        self._open_id = open_id
        self._access_token = access_token
        self._session = session
        self._url = API_UAT_URL if use_uat else API_PRODUCTION_URL

    def _generate_signature(self, nonce: str) -> str:
        """Calculate the request signature for queryData API.

        Format: HMAC-SHA256 of 'appId={appId}&nonce={nonce}' with appSecret as key.
        """
        message = f"appId={self._app_id}&nonce={nonce}"
        sign = hmac.new(
            self._app_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return sign

    async def submit_query_task(self, record_no: str | None = None) -> dict[str, Any]:
        """Submit a queryData export task or check task status.

        - First call (record_no=None): initiates export task, returns 'DataFileExporting' and recordNo.
        - Subsequent calls (with record_no): queries status and returns download URL when ready.
        """
        nonce = str(int(time.time() * 1000))
        sign = self._generate_signature(nonce)

        params = {
            "appId": self._app_id,
            "nonce": nonce,
            "sign": sign,
        }

        payload: dict[str, Any] = {
            "openId": self._open_id,
            "accessToken": self._access_token,
        }
        if record_no:
            payload["recordNo"] = record_no

        _LOGGER.debug("Sending queryData request to %s (recordNo=%s)", self._url, record_no)

        async with self._session.post(
            self._url,
            params=params,
            json=payload,
            timeout=aiohttp.ClientTimeout(total=60),
        ) as response:
            if response.status != 200:
                text = await response.text()
                _LOGGER.error("XPENG API error (HTTP %s): %s", response.status, text)
                raise XpengApiError(f"HTTP {response.status}: {text}")

            result = await response.json()
            _LOGGER.debug("XPENG API response: %s", result)
            return result

    async def download_file(self, download_url: str, destination_path: str) -> str:
        """Download exported file archive from the returned URL."""
        _LOGGER.debug("Downloading export file from %s to %s", download_url, destination_path)
        async with self._session.get(
            download_url,
            timeout=aiohttp.ClientTimeout(total=300),
        ) as response:
            if response.status != 200:
                raise XpengApiError(f"Download failed with HTTP {response.status}")

            with open(destination_path, "wb") as f:
                while True:
                    chunk = await response.content.read(1024 * 1024)
                    if not chunk:
                        break
                    f.write(chunk)

        return destination_path


class XpengApiError(Exception):
    """Exception raised for XPENG API communication errors."""
