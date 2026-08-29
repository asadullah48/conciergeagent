"""Identifier generation must be stable across processes and interpreters."""
from __future__ import annotations

import os
import subprocess
import sys

import pytest

from conciergeagent.core.identifiers import session_id, stable_digest, ticket_id


def test_stable_digest_is_deterministic():
    assert stable_digest("a", "b") == stable_digest("a", "b")


def test_stable_digest_is_uppercase_hex():
    digest = stable_digest("customer", "query")
    assert digest.isupper()
    assert all(char in "0123456789ABCDEF" for char in digest)


@pytest.mark.parametrize("length", [1, 4, 8, 10])
def test_stable_digest_honours_length(length):
    assert len(stable_digest("x", length=length)) == length


@pytest.mark.parametrize("length", [0, -1, 11, 64])
def test_stable_digest_rejects_out_of_range_length(length):
    with pytest.raises(ValueError, match="length must be between"):
        stable_digest("x", length=length)


def test_digest_separator_prevents_field_collision():
    """('ab','c') and ('a','bc') must not collapse to the same digest."""
    assert stable_digest("ab", "c") != stable_digest("a", "bc")


def test_session_and_ticket_namespaces_differ():
    assert session_id("q", "c").removeprefix("SES-") != ticket_id("q", "c").removeprefix("TCK-")


def test_session_id_has_expected_prefix():
    assert session_id("query", "CUST-1").startswith("SES-")


def test_ticket_id_has_expected_prefix():
    assert ticket_id("query", "CUST-1").startswith("TCK-")


def test_session_id_varies_with_intent():
    assert session_id("q", "c", "ADVISORY") != session_id("q", "c", "SUPPORT")


def test_session_id_varies_with_customer():
    assert session_id("q", "CUST-1") != session_id("q", "CUST-2")


def test_session_id_varies_with_query():
    assert session_id("q1", "CUST-1") != session_id("q2", "CUST-1")


def test_ids_survive_hash_randomisation_across_processes():
    """Regression guard: builtin hash() was seeded per process, these are not."""
    script = (
        "from conciergeagent.core.identifiers import ticket_id;"
        "print(ticket_id('disputed charge', 'CUST-9082'))"
    )
    runs = {
        subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            check=True,
            env={**os.environ, "PYTHONHASHSEED": "random"},
        ).stdout.strip()
        for _ in range(3)
    }
    assert len(runs) == 1
