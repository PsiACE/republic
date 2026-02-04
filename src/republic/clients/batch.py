"""Batch operations for Republic."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
from typing import Any, TypeVar

from any_llm.types.batch import Batch

from republic.core.execution import LLMCore

T = TypeVar("T")


class BatchClient:
    """Group batch operations for clarity."""

    def __init__(self, core: LLMCore) -> None:
        self._core = core

    def _provider_name(self, provider: str | None) -> str:
        return provider or self._core.provider

    def _call(self, provider_name: str, name: str, fn: Callable[[], T], **attributes: Any) -> T:
        try:
            with self._core.span(name, provider=provider_name, model="-", **attributes):
                return fn()
        except Exception as exc:
            self._core.raise_wrapped(exc, provider_name, "-")
            raise AssertionError("unreachable") from exc

    async def _acall(self, provider_name: str, name: str, fn: Callable[[], Awaitable[T]], **attributes: Any) -> T:
        try:
            with self._core.span(name, provider=provider_name, model="-", **attributes):
                return await fn()
        except Exception as exc:
            self._core.raise_wrapped(exc, provider_name, "-")
            raise AssertionError("unreachable") from exc

    def create(
        self,
        input_file_path: str,
        endpoint: str,
        *,
        provider: str | None = None,
        completion_window: str = "24h",
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Batch:
        provider_name = self._provider_name(provider)
        client = self._core.get_client(provider_name)
        return self._call(
            provider_name,
            "republic.batch.create",
            lambda: client.create_batch(
                input_file_path=input_file_path,
                endpoint=endpoint,
                completion_window=completion_window,
                metadata=metadata,
                **kwargs,
            ),
            endpoint=endpoint,
        )

    async def acreate(
        self,
        input_file_path: str,
        endpoint: str,
        *,
        provider: str | None = None,
        completion_window: str = "24h",
        metadata: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> Batch:
        provider_name = self._provider_name(provider)
        client = self._core.get_client(provider_name)
        return await self._acall(
            provider_name,
            "republic.batch.create",
            lambda: client.acreate_batch(
                input_file_path=input_file_path,
                endpoint=endpoint,
                completion_window=completion_window,
                metadata=metadata,
                **kwargs,
            ),
            endpoint=endpoint,
        )

    def retrieve(self, batch_id: str, *, provider: str | None = None, **kwargs: Any) -> Batch:
        provider_name = self._provider_name(provider)
        client = self._core.get_client(provider_name)
        return self._call(
            provider_name,
            "republic.batch.retrieve",
            lambda: client.retrieve_batch(batch_id=batch_id, **kwargs),
            batch_id=batch_id,
        )

    async def aretrieve(self, batch_id: str, *, provider: str | None = None, **kwargs: Any) -> Batch:
        provider_name = self._provider_name(provider)
        client = self._core.get_client(provider_name)
        return await self._acall(
            provider_name,
            "republic.batch.retrieve",
            lambda: client.aretrieve_batch(batch_id=batch_id, **kwargs),
            batch_id=batch_id,
        )

    def cancel(self, batch_id: str, *, provider: str | None = None, **kwargs: Any) -> Batch:
        provider_name = self._provider_name(provider)
        client = self._core.get_client(provider_name)
        return self._call(
            provider_name,
            "republic.batch.cancel",
            lambda: client.cancel_batch(batch_id=batch_id, **kwargs),
            batch_id=batch_id,
        )

    async def acancel(self, batch_id: str, *, provider: str | None = None, **kwargs: Any) -> Batch:
        provider_name = self._provider_name(provider)
        client = self._core.get_client(provider_name)
        return await self._acall(
            provider_name,
            "republic.batch.cancel",
            lambda: client.acancel_batch(batch_id=batch_id, **kwargs),
            batch_id=batch_id,
        )

    def list(
        self,
        *,
        provider: str | None = None,
        after: str | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> Sequence[Batch]:
        provider_name = self._provider_name(provider)
        client = self._core.get_client(provider_name)
        return self._call(
            provider_name,
            "republic.batch.list",
            lambda: client.list_batches(after=after, limit=limit, **kwargs),
            after=after,
            limit=limit,
        )

    async def alist(
        self,
        *,
        provider: str | None = None,
        after: str | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> Sequence[Batch]:
        provider_name = self._provider_name(provider)
        client = self._core.get_client(provider_name)
        return await self._acall(
            provider_name,
            "republic.batch.list",
            lambda: client.alist_batches(after=after, limit=limit, **kwargs),
            after=after,
            limit=limit,
        )
