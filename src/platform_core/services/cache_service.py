from datetime import datetime, timedelta
from hashlib import sha256
from json import dumps
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from platform_core.models.api_cache import ApiCacheEntry


class ApiCacheService:
    def __init__(self, db: Session) -> None:
        self.db = db

    @staticmethod
    def build_key(provider: str, url: str, params: Dict[str, Any]) -> str:
        payload = dumps({"provider": provider, "url": url, "params": params}, sort_keys=True, default=str)
        return sha256(payload.encode("utf-8")).hexdigest()

    def get(self, provider: str, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cache_key = self.build_key(provider, url, params)
        entry = self.db.scalar(
            select(ApiCacheEntry).where(
                ApiCacheEntry.cache_key == cache_key,
                ApiCacheEntry.expires_at > datetime.utcnow(),
            )
        )
        return entry.response_json if entry else None

    def set(
        self,
        provider: str,
        url: str,
        params: Dict[str, Any],
        response_json: Dict[str, Any],
        ttl_seconds: int,
    ) -> None:
        cache_key = self.build_key(provider, url, params)
        entry = self.db.scalar(select(ApiCacheEntry).where(ApiCacheEntry.cache_key == cache_key))
        expires_at = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        if entry is None:
            entry = ApiCacheEntry(
                cache_key=cache_key,
                provider=provider,
                request_url=url,
                request_params=params,
                response_json=response_json,
                expires_at=expires_at,
            )
            self.db.add(entry)
        else:
            entry.request_params = params
            entry.response_json = response_json
            entry.expires_at = expires_at
        self.db.commit()

