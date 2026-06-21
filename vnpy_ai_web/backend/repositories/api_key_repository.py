"""Repository for ApiKey CRUD operations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from vnpy_ai_web.backend.database.models import ApiKey


class ApiKeyRepository:
    """Repository for ApiKey model."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, provider: str, key_prefix: str, encrypted_key: str) -> ApiKey:
        """Create a new API key."""
        api_key = ApiKey(provider=provider, key_prefix=key_prefix, encrypted_key=encrypted_key)
        self._session.add(api_key)
        self._session.commit()
        self._session.refresh(api_key)
        return api_key

    def get_by_id(self, api_key_id: int) -> ApiKey | None:
        """Get an API key by ID."""
        return self._session.query(ApiKey).filter(ApiKey.id == api_key_id).first()

    def get_by_provider(self, provider: str) -> ApiKey | None:
        """Get an API key by provider name."""
        return self._session.query(ApiKey).filter(ApiKey.provider == provider).first()

    def list_all(self) -> list[ApiKey]:
        """List all API keys."""
        return self._session.query(ApiKey).all()

    def update(self, api_key_id: int, **kwargs: object) -> ApiKey | None:
        """Update an API key."""
        api_key = self.get_by_id(api_key_id)
        if api_key is None:
            return None
        for key, value in kwargs.items():
            if hasattr(api_key, key):
                setattr(api_key, key, value)
        self._session.commit()
        self._session.refresh(api_key)
        return api_key

    def delete(self, api_key_id: int) -> bool:
        """Delete an API key."""
        api_key = self.get_by_id(api_key_id)
        if api_key is None:
            return False
        self._session.delete(api_key)
        self._session.commit()
        return True
