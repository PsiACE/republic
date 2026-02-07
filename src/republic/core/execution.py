"""Core execution utilities for Republic."""

from __future__ import annotations

import inspect
import json
import logging
from collections.abc import Callable
from typing import Any, NoReturn

from any_llm import AnyLLM
from any_llm.exceptions import (
    AnyLLMError,
    AuthenticationError,
    ContentFilterError,
    ContextLengthExceededError,
    InvalidRequestError,
    MissingApiKeyError,
    ModelNotFoundError,
    ProviderError,
    RateLimitError,
    UnsupportedProviderError,
)

from republic.core.errors import ErrorKind, RepublicError

logger = logging.getLogger(__name__)


class LLMCore:
    """Shared LLM execution utilities (provider resolution, retries, client cache)."""

    RETRY = object()

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        fallback_models: list[str],
        max_retries: int,
        api_key: str | dict[str, str] | None,
        api_base: str | dict[str, str] | None,
        client_args: dict[str, Any],
        verbose: int,
        error_classifier: Callable[[Exception], ErrorKind | None] | None = None,
    ) -> None:
        self._provider = provider
        self._model = model
        self._fallback_models = fallback_models
        self._max_retries = max_retries
        self._api_key = api_key
        self._api_base = api_base
        self._client_args = client_args
        self._verbose = verbose
        self._error_classifier = error_classifier
        self._client_cache: dict[str, AnyLLM] = {}

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    @property
    def fallback_models(self) -> list[str]:
        return self._fallback_models

    @property
    def max_retries(self) -> int:
        return self._max_retries

    def max_attempts(self) -> int:
        return max(1, self._max_retries)

    @staticmethod
    def resolve_model_provider(model: str, provider: str | None) -> tuple[str, str]:
        if provider:
            if ":" in model:
                raise RepublicError(
                    ErrorKind.INVALID_INPUT,
                    "When provider is specified, model must not include a provider prefix.",
                )
            return provider, model

        if ":" not in model:
            raise RepublicError(ErrorKind.INVALID_INPUT, "Model must be in 'provider:model' format.")

        provider_name, model_id = model.split(":", 1)
        if not provider_name or not model_id:
            raise RepublicError(ErrorKind.INVALID_INPUT, "Model must be in 'provider:model' format.")
        return provider_name, model_id

    def resolve_fallback(self, model: str) -> tuple[str, str]:
        if ":" in model:
            provider_name, model_id = model.split(":", 1)
            if not provider_name or not model_id:
                raise RepublicError(ErrorKind.INVALID_INPUT, "Fallback models must be in 'provider:model' format.")
            return provider_name, model_id
        if self._provider:
            return self._provider, model
        raise RepublicError(
            ErrorKind.INVALID_INPUT,
            "Fallback models must include provider or LLM must be initialized with a provider.",
        )

    def model_candidates(self, override_model: str | None, override_provider: str | None) -> list[tuple[str, str]]:
        if override_model:
            provider, model = self.resolve_model_provider(override_model, override_provider)
            return [(provider, model)]

        candidates = [(self._provider, self._model)]
        for model in self._fallback_models:
            candidates.append(self.resolve_fallback(model))
        return candidates

    def iter_clients(self, override_model: str | None, override_provider: str | None):
        for provider_name, model_id in self.model_candidates(override_model, override_provider):
            yield provider_name, model_id, self.get_client(provider_name)

    def _resolve_api_key(self, provider: str) -> str | None:
        if isinstance(self._api_key, dict):
            return self._api_key.get(provider)
        return self._api_key

    def _resolve_api_base(self, provider: str) -> str | None:
        if isinstance(self._api_base, dict):
            return self._api_base.get(provider)
        return self._api_base

    def _freeze_cache_key(self, provider: str, api_key: str | None, api_base: str | None) -> str:
        def _freeze(value: Any) -> Any:
            if isinstance(value, (str, int, float, bool)) or value is None:
                return value
            if isinstance(value, (tuple, list)):
                return [_freeze(item) for item in value]
            if isinstance(value, dict):
                return {str(k): _freeze(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
            return repr(value)

        payload = {
            "provider": provider,
            "api_key": api_key,
            "api_base": api_base,
            "client_args": _freeze(self._client_args),
        }
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    def get_client(self, provider: str) -> AnyLLM:
        api_key = self._resolve_api_key(provider)
        api_base = self._resolve_api_base(provider)
        cache_key = self._freeze_cache_key(provider, api_key, api_base)
        if cache_key not in self._client_cache:
            self._client_cache[cache_key] = AnyLLM.create(
                provider,
                api_key=api_key,
                api_base=api_base,
                **self._client_args,
            )
        return self._client_cache[cache_key]

    def log_error(self, error: RepublicError, provider: str, model: str, attempt: int) -> None:
        if self._verbose == 0:
            return

        prefix = f"[{provider}:{model}] attempt {attempt + 1}/{self.max_attempts()}"
        if error.cause:
            logger.warning("%s failed: %s (cause=%r)", prefix, error, error.cause)
        else:
            logger.warning("%s failed: %s", prefix, error)

    def classify_exception(self, exc: Exception) -> ErrorKind:
        if isinstance(exc, RepublicError):
            return exc.kind
        if self._error_classifier is not None:
            try:
                kind = self._error_classifier(exc)
            except Exception as classifier_exc:
                logger.warning("error_classifier failed: %r", classifier_exc)
            else:
                if isinstance(kind, ErrorKind):
                    return kind
        try:
            from pydantic import ValidationError as PydanticValidationError

            validation_error_type: type[Exception] | None = PydanticValidationError
        except ImportError:
            validation_error_type = None
        if validation_error_type is not None and isinstance(exc, validation_error_type):
            return ErrorKind.INVALID_INPUT
        error_map = [
            ((MissingApiKeyError, AuthenticationError), ErrorKind.CONFIG),
            (
                (UnsupportedProviderError, InvalidRequestError, ModelNotFoundError, ContextLengthExceededError),
                ErrorKind.INVALID_INPUT,
            ),
            ((RateLimitError, ContentFilterError), ErrorKind.TEMPORARY),
            ((ProviderError, AnyLLMError), ErrorKind.PROVIDER),
        ]
        for types, kind in error_map:
            if isinstance(exc, types):
                return kind
        return ErrorKind.UNKNOWN

    def should_retry(self, kind: ErrorKind) -> bool:
        return kind in {ErrorKind.TEMPORARY, ErrorKind.PROVIDER}

    def wrap_error(self, exc: Exception, kind: ErrorKind, provider: str, model: str) -> RepublicError:
        message = f"{provider}:{model}: {exc}"
        return RepublicError(kind, message, cause=exc)

    def raise_wrapped(self, exc: Exception, provider: str, model: str) -> NoReturn:
        kind = self.classify_exception(exc)
        raise self.wrap_error(exc, kind, provider, model) from exc

    def _handle_attempt_error(self, exc: Exception, provider_name: str, model_id: str, attempt: int) -> None:
        kind = self.classify_exception(exc)
        wrapped = self.wrap_error(exc, kind, provider_name, model_id)
        if not self.should_retry(kind):
            raise wrapped
        self.log_error(wrapped, provider_name, model_id, attempt)

    def run_chat_sync(
        self,
        *,
        messages_payload: list[dict[str, Any]],
        tools_payload: list[dict[str, Any]] | None,
        model: str | None,
        provider: str | None,
        max_tokens: int | None,
        stream: bool,
        reasoning_effort: Any | None,
        tool_count: int,
        kwargs: dict[str, Any],
        on_response: Callable[[Any, str, str, int], Any],
    ) -> Any:
        last_provider: str | None = None
        last_model: str | None = None
        for provider_name, model_id, client in self.iter_clients(model, provider):
            last_provider, last_model = provider_name, model_id
            for attempt in range(self.max_attempts()):
                try:
                    response = client.completion(
                        model=model_id,
                        messages=messages_payload,
                        tools=tools_payload,
                        max_tokens=max_tokens,
                        stream=stream,
                        reasoning_effort=reasoning_effort,
                        **kwargs,
                    )
                except Exception as exc:
                    self._handle_attempt_error(exc, provider_name, model_id, attempt)
                else:
                    result = on_response(response, provider_name, model_id, attempt)
                    if result is self.RETRY:
                        continue
                    return result

        if last_provider and last_model:
            raise RepublicError(
                ErrorKind.TEMPORARY,
                f"{last_provider}:{last_model}: LLM call failed after retries",
            )
        raise RepublicError(ErrorKind.TEMPORARY, "LLM call failed after retries")

    async def run_chat_async(
        self,
        *,
        messages_payload: list[dict[str, Any]],
        tools_payload: list[dict[str, Any]] | None,
        model: str | None,
        provider: str | None,
        max_tokens: int | None,
        stream: bool,
        reasoning_effort: Any | None,
        tool_count: int,
        kwargs: dict[str, Any],
        on_response: Callable[[Any, str, str, int], Any],
    ) -> Any:
        last_provider: str | None = None
        last_model: str | None = None
        for provider_name, model_id, client in self.iter_clients(model, provider):
            last_provider, last_model = provider_name, model_id
            for attempt in range(self.max_attempts()):
                try:
                    response = await client.acompletion(
                        model=model_id,
                        messages=messages_payload,
                        tools=tools_payload,
                        max_tokens=max_tokens,
                        stream=stream,
                        reasoning_effort=reasoning_effort,
                        **kwargs,
                    )
                except Exception as exc:
                    self._handle_attempt_error(exc, provider_name, model_id, attempt)
                else:
                    result = on_response(response, provider_name, model_id, attempt)
                    if inspect.isawaitable(result):
                        result = await result
                    if result is self.RETRY:
                        continue
                    return result

        if last_provider and last_model:
            raise RepublicError(
                ErrorKind.TEMPORARY,
                f"{last_provider}:{last_model}: LLM call failed after retries",
            )
        raise RepublicError(ErrorKind.TEMPORARY, "LLM call failed after retries")
