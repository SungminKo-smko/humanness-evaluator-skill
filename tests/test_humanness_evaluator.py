"""
Tests for humanness_evaluator.
Requires BioPhiSkill installed (conda activate biophi).
"""

import json
import pytest
from pathlib import Path

# Load reference test cases
TEST_CASES_PATH = Path(__file__).parent.parent / "humanness-evaluator" / "test_cases.json"


def load_test_cases():
    with open(TEST_CASES_PATH) as f:
        return json.load(f)["test_cases"]


def test_biophi_importable():
    """BioPhiSkill must be importable for the evaluator to work."""
    try:
        from agent_api import evaluate_humanness  # noqa: F401
    except ImportError:
        pytest.skip("BioPhiSkill not installed — run: conda activate biophi")


def test_evaluate_single_returns_required_keys():
    try:
        from humanness_evaluator import evaluate_single
    except ImportError:
        pytest.skip("BioPhiSkill not installed")

    cases = load_test_cases()
    result = evaluate_single(
        vh_sequence=cases[0]["vh_sequence"],
        sequence_id=cases[0]["id"]
    )

    assert "humanness_score" in result
    assert "oasis_percentile" in result
    assert result["success"] is True


def test_humanized_mab_above_threshold():
    try:
        from humanness_evaluator import evaluate_single
    except ImportError:
        pytest.skip("BioPhiSkill not installed")

    cases = {c["id"]: c for c in load_test_cases()}
    tc = cases["trastuzumab_vh"]
    result = evaluate_single(vh_sequence=tc["vh_sequence"], sequence_id=tc["id"])

    assert result["humanness_score"] >= tc["expected_humanness_min"], (
        f"Expected ≥{tc['expected_humanness_min']}%, got {result['humanness_score']}%"
    )
