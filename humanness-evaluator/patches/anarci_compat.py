"""
anarci_compat.py — Auto-applied ANARCI compatibility patch for Python 3.12+

ANARCI relies on Biopython's HSP objects where `query_start`, `query_end`, etc.
can be None in newer Biopython versions. This module monkey-patches the two
functions that fail in that case, so no manual edits to site-packages are needed.

This module is imported automatically by agent_api.py.
"""

import sys


def _patch_anarci():
    """Apply runtime monkey-patches to ANARCI for Python 3.12 + Biopython >= 1.80."""
    try:
        import anarci.anarci as _anarci_mod
    except ImportError:
        return  # anarci not installed — skip

    # ------------------------------------------------------------------ #
    # Patch 1: _domains_are_same                                          #
    # query_end can be None → guard so domains are NOT falsely split      #
    # ------------------------------------------------------------------ #
    def _domains_are_same(dom1, dom2):
        dom1, dom2 = sorted(
            [dom1, dom2],
            key=lambda x: x.query_start if x.query_start is not None else 0
        )
        end1 = dom1.query_end if dom1.query_end is not None else float('inf')
        if (dom2.query_start or 0) >= end1:
            return False
        return True

    # ------------------------------------------------------------------ #
    # Patch 2: _hmm_alignment_to_states                                   #
    # query_start / query_end can be None → use safe defaults             #
    # ------------------------------------------------------------------ #
    _original_hmm = _anarci_mod._hmm_alignment_to_states

    def _hmm_alignment_to_states_safe(hsp, n, seq_length):
        # Patch None coordinates before the original function sees them
        if hsp.query_start is None:
            hsp._query_start = 0
        if hsp.query_end is None:
            hsp._query_end = seq_length
        return _original_hmm(hsp, n, seq_length)

    _anarci_mod._domains_are_same = _domains_are_same

    # Only wrap if the original is not already a wrapper to stay idempotent
    if not getattr(_anarci_mod._hmm_alignment_to_states, '_patched', False):
        _hmm_alignment_to_states_safe._patched = True
        _anarci_mod._hmm_alignment_to_states = _hmm_alignment_to_states_safe


# Apply immediately on import
_patch_anarci()
