"""Unit tests for the dependency-free ruleset: checksums and regex detection."""

from __future__ import annotations

import pytest

from phi_mcp import entities
from phi_mcp.checksums import dea_is_valid, luhn_is_valid, npi_is_valid
from phi_mcp.regex_engine import RegexEngine


# --- Check-digit validators -------------------------------------------------
@pytest.mark.parametrize("npi", ["1234567893", "1245319599", "1679576722", "1003000126"])
def test_valid_npis(npi: str) -> None:
    assert npi_is_valid(npi)


@pytest.mark.parametrize("npi", ["1710975306", "1234567890", "0000000000", "12345"])
def test_invalid_npis(npi: str) -> None:
    assert not npi_is_valid(npi)


def test_dea_checksum() -> None:
    assert dea_is_valid("AB1234563")
    assert not dea_is_valid("AB1234560")
    assert not dea_is_valid("ZZ1234563")  # bad registrant-type letter


def test_luhn() -> None:
    assert luhn_is_valid("4111111111111111")
    assert luhn_is_valid("4111 1111 1111 1111")
    assert not luhn_is_valid("4111111111111112")


# --- RegexEngine detection --------------------------------------------------
def _types(engine: RegexEngine, text: str) -> set[str]:
    return {e.entity_type for e in engine.detect(text)}


def test_detects_email_without_context() -> None:
    assert entities.EMAIL_ADDRESS in _types(RegexEngine(), "reach me at a.b@c.io")


def test_npi_requires_valid_checksum() -> None:
    engine = RegexEngine()
    assert entities.NPI in _types(engine, "NPI 1234567893")
    # A 10-digit number that fails the checksum is not an NPI.
    assert entities.NPI not in _types(engine, "order 1234567890")


def test_mrn_requires_context() -> None:
    engine = RegexEngine()
    assert entities.MEDICAL_RECORD_NUMBER not in _types(engine, "the code 1234567 shipped")
    assert entities.MEDICAL_RECORD_NUMBER in _types(engine, "Patient MRN: 1234567")


def test_bare_ssn_requires_context_but_dashed_does_not() -> None:
    engine = RegexEngine()
    assert entities.US_SSN not in _types(engine, "reference 078051120 here")
    assert entities.US_SSN in _types(engine, "SSN 078051120")
    assert entities.US_SSN in _types(engine, "078-05-1120")


def test_detection_is_deterministic() -> None:
    engine = RegexEngine()
    text = "MRN: 1234567 email a@b.co NPI 1234567893"
    first = engine.detect(text)
    second = engine.detect(text)
    assert [(e.entity_type, e.start, e.end, e.score) for e in first] == [
        (e.entity_type, e.start, e.end, e.score) for e in second
    ]
