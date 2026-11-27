from __future__ import annotations

import os
from typing import Any

import aiohttp


class Nat20Error(RuntimeError):
    """Raised when the Nat20 bridge returns an error or cannot be reached."""


class Nat20Client:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (
            base_url or os.getenv("NAT20_BASE_URL") or "http://127.0.0.1:8020"
        ).rstrip("/")
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=15)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        session = await self._get_session()
        url = f"{self.base_url}{path}"

        try:
            async with session.request(method, url, json=payload) as response:
                try:
                    data = await response.json()
                except (aiohttp.ContentTypeError, ValueError):
                    data = await response.text()

                if response.status >= 400:
                    raise Nat20Error(
                        f"Nat20 API {response.status}: {data}"
                    )
                return data

        except aiohttp.ClientError as exc:
            raise Nat20Error(
                f"Nat20 nicht erreichbar unter {self.base_url}: {exc}"
            ) from exc

    async def health(self) -> dict[str, Any]:
        return await self._request("GET", "/v1/health")

    async def validate_party(self, party: list[dict[str, Any]]) -> Any:
        return await self._request(
            "POST", "/v1/party/validate", {"party": party}
        )

    async def start_combat(
        self,
        party: list[dict[str, Any]],
        monsters: list[str],
        seed: int | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "party": party,
            "monsters": monsters,
        }
        if seed is not None:
            payload["seed"] = seed
        return await self._request("POST", "/v1/combat", payload)

    async def get_combat(self, combat_id: str) -> Any:
        return await self._request("GET", f"/v1/combat/{combat_id}")

    async def submit_intent(
        self, combat_id: str, intent: dict[str, Any]
    ) -> Any:
        return await self._request(
            "POST", f"/v1/combat/{combat_id}/intent", intent
        )

    async def advance_monster(
        self, combat_id: str, target_id: str | None = None
    ) -> Any:
        payload = {"target_id": target_id} if target_id else {}
        return await self._request(
            "POST", f"/v1/combat/{combat_id}/advance-monster", payload
        )

    async def end_combat(self, combat_id: str) -> Any:
        return await self._request("POST", f"/v1/combat/{combat_id}/end", {})

    async def roll(self, dice: str, seed: int | None = None) -> Any:
        payload: dict[str, Any] = {"dice": dice}
        if seed is not None:
            payload["seed"] = seed
        return await self._request("POST", "/v1/roll", payload)

    async def check(self, payload: dict[str, Any]) -> Any:
        return await self._request("POST", "/v1/check", payload)

    async def short_rest(self, payload: dict[str, Any]) -> Any:
        return await self._request("POST", "/v1/rest/short", payload)

    async def long_rest(self, payload: dict[str, Any]) -> Any:
        return await self._request("POST", "/v1/rest/long", payload)

    async def browse_srd(self, category: str, query: str | None = None) -> Any:
        path = f"/v1/srd/{category}"
        if query:
            from urllib.parse import quote
            path += f"?q={quote(query)}"
        return await self._request("GET", path)

    async def get_srd_entry(self, category: str, slug: str) -> Any:
        return await self._request("GET", f"/v1/srd/{category}/{slug}")

    async def close(self) -> None:
        if self._session is not None and not self._session.closed:
            await self._session.close()