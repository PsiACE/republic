"""Core execution utilities for Republic."""

from __future__ import annotations

import json
import logging
from typing import Any, Callable, Dict, List, NoReturn, Optional, Tuple

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
        fallback_models: List[str],
        max_retries: int,
        api_key: Optional[str | Dict[str, str]],
        api_base: Optional[str | Dict[str, str]],
        client_args: Dict[str, Any],
        verbose: int,
        span: Callable[..., Any],
        error_classifier: Optional[Callable[[Exception], Optional[ErrorKind]]] = None,
    ) -> None:
        self._provider = provider
        self._model = model
        self._fallback_models = fallback_models
        self._max_retries = max_retries
        self._api_key = api_key
        self._api_base = api_base
        self._client_args = client_args
        self._verbose = verbose
        self._span = span
        self._error_classifier = error_classifier
        self._client_cache: Dict[str, AnyLLM] = {}

    @property
    def provider(self) -> str:
        return self._provider

    @property
    def model(self) -> str:
        return self._model

    @property
    def fallback_models(self) -> List[str]:
        return self._fallback_models

    @property
    def max_retries(self) -> int:
        return self._max_retries

    def max_attempts(self) -> int:
        return max(1, self._max_retries)

    def span(self, name: str, **attributes: Any):
        return self._span(name, **attributes)

    @staticmethod
    def resolve_model_provider(model: str, provider: Optional[str]) -> Tuple[str, str]:
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

    def resolve_fallback(self, model: str) -> Tuple[str, str]:
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

    def model_candidates(self, override_model: Optional[str], override_provider: Optional[str]) -> List[Tuple[str, str]]:
        if override_model:
            provider, model = self.resolve_model_provider(override_model, override_provider)
            return [(provider, model)]

        candidates = [(self._provider, self._model)]
        for model in self._fallback_models:
            candidates.append(self.resolve_fallback(model))
        return candidates

    def iter_clients(self, override_model: Optional[str], override_provider: Optional[str]):
        for provider_name, model_id in self.model_candidates(override_model, override_provider):
            yield provider_name, model_id, self.get_client(provider_name)

    def _resolve_api_key(self, provider: str) -> Optional[str]:
        if isinstance(self._api_key, dict):
            return self._api_key.get(provider)
        return self._api_key

    def _resolve_api_base(self, provider: str) -> Optional[str]:
        if isinstance(self._api_base, dict):
            return self._api_base.get(provider)
        return self._api_base

    def _freeze_cache_key(self, provider: str, api_key: Optional[str], api_base: Optional[str]) -> str:
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
            ((ContentFilterError,), ErrorKind.INVALID_INPUT),
            ((RateLimitError, ProviderError), ErrorKind.TEMPORARY),
            ((AnyLLMError,), ErrorKind.PROVIDER),
        ]
        for error_types, kind in error_map:
            if isinstance(exc, error_types):
                return kind
        return ErrorKind.UNKNOWN

    @staticmethod
    def should_retry(kind: ErrorKind) -> bool:
        return kind is ErrorKind.TEMPORARY

    @staticmethod
    def wrap_error(exc: Exception, kind: ErrorKind, provider: str, model: str) -> RepublicError:
        if isinstance(exc, RepublicError):
            return exc
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
        messages_payload: List[Dict[str, Any]],
        tools_payload: Optional[List[Dict[str, Any]]],
        model: Optional[str],
        provider: Optional[str],
        max_tokens: Optional[int],
        stream: bool,
        reasoning_effort: Optional[Any],
        tool_count: int,
        kwargs: Dict[str, Any],
        on_response: Callable[[Any, str, str, int], Any],
    ) -> Any:
        last_provider: Optional[str] = None
        last_model: Optional[str] = None
        for provider_name, model_id, client in self.iter_clients(model, provider):
            last_provider, last_model = provider_name, model_id
            for attempt in range(self.max_attempts()):
                try:
                    with self._span(
                        "republic.llm.chat",
                        provider=provider_name,
                        model=model_id,
                        stream=stream,
                        attempt=attempt + 1,
                        tool_count=tool_count,
                    ):
                        response = client.completion(
                            model=model_id,
                            messages=messages_payload,
                            tools=tools_payload,
                            max_tokens=max_tokens,
                            stream=stream,
                            reasoning_effort=reasoning_effort,
                            **kwargs,
                        )
                    result = on_response(response, provider_name, model_id, attempt)
                    if result is self.RETRY:
                        continue
                    return result
                except Exception as exc:
                    self._handle_attempt_error(exc, provider_name, model_id, attempt)

        if last_provider and last_model:
            raise RepublicError(
                ErrorKind.TEMPORARY,
                f"{last_provider}:{last_model}: LLM call failed after retries",
            )
        raise RepublicError(ErrorKind.TEMPORARY, "LLM call failed after retries")

    async def run_chat_async(
        self,
        *,
        messages_payload: List[Dict[str, Any]],
        tools_payload: Optional[List[Dict[str, Any]]],
        model: Optional[str],
        provider: Optional[str],
        max_tokens: Optional[int],
        stream: bool,
        reasoning_effort: Optional[Any],
        tool_count: int,
        kwargs: Dict[str, Any],
        on_response: Callable[[Any, str, str, int], Any],
    ) -> Any:
        last_provider: Optional[str] = None
        last_model: Optional[str] = None
        for provider_name, model_id, client in self.iter_clients(model, provider):
            last_provider, last_model = provider_name, model_id
            for attempt in range(self.max_attempts()):
                try:
                    with self._span(
                        "republic.llm.chat",
                        provider=provider_name,
                        model=model_id,
                        stream=stream,
                        attempt=attempt + 1,
                        tool_count=tool_count,
                    ):
                        response = await client.acompletion(
                            model=model_id,
                            messages=messages_payload,
                            tools=tools_payload,
                            max_tokens=max_tokens,
                            stream=stream,
                            reasoning_effort=reasoning_effort,
                            **kwargs,
                        )
                    result = on_response(response, provider_name, model_id, attempt)
                    if result is self.RETRY:
                        continue
                    return result
                except Exception as exc:
                    self._handle_attempt_error(exc, provider_name, model_id, attempt)

        if last_provider and last_model:
            raise RepublicError(
                ErrorKind.TEMPORARY,
                f"{last_provider}:{last_model}: LLM call failed after retries",
            )
        raise RepublicError(ErrorKind.TEMPORARY, "LLM call failed after retries")
