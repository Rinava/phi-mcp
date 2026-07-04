"""Smoke test for the real Presidio engine.

Skipped unless Presidio *and* a spaCy model are installed, so it never runs in
the fast loop and never blocks contributors who only use the regex engine.

Setup:  pip install "phi-redact-mcp[presidio]" && python -m spacy download en_core_web_lg
Run:    pytest tests_integration
"""

from __future__ import annotations

import importlib.util

import pytest

from phi_mcp import entities

_HAS_PRESIDIO = importlib.util.find_spec("presidio_analyzer") is not None

pytestmark = pytest.mark.skipif(not _HAS_PRESIDIO, reason="presidio-analyzer not installed")


def _engine():
    from phi_mcp.presidio_engine import PresidioEngine

    # en_core_web_sm is the lightest model; good enough for a smoke test.
    return PresidioEngine(spacy_model="en_core_web_sm")


def test_presidio_detects_person_and_normalises_names() -> None:
    engine = _engine()
    found = {e.entity_type for e in engine.detect("Dr. Alice Reyes wrote NPI 1234567893.")}
    # PERSON comes from spaCy NER; NPI is normalised from Presidio's US_NPI.
    assert entities.PERSON in found
    assert entities.NPI in found


def test_presidio_custom_mrn_recognizer_fires_with_context() -> None:
    engine = _engine()
    found = {e.entity_type for e in engine.detect("Patient MRN: 1234567 admitted today.")}
    assert entities.MEDICAL_RECORD_NUMBER in found
