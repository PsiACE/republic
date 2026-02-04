from __future__ import annotations

import pytest

from republic.core import ErrorKind, RepublicError, instrument_republic, span


class TestTelemetry:
    def test_span_noop_when_logfire_missing(self, monkeypatch):
        monkeypatch.setattr("republic.core.telemetry.logfire", None)
        instrumented = span("republic.test")
        assert instrumented is not None

    def test_instrument_republic_requires_logfire(self, monkeypatch):
        monkeypatch.setattr("republic.core.telemetry.logfire", None)

        with pytest.raises(RepublicError) as exc_info:
            instrument_republic()
        assert exc_info.value.kind == ErrorKind.CONFIG
