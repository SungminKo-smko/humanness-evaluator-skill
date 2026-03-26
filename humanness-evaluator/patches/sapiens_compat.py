"""
sapiens_compat.py — Auto-applied Sapiens model loading compatibility patch

Addresses three issues encountered with sapiens >= 1.1.0 + old transformers:

  1. HuggingFace URL resolution failures (transformers 4.19.x cannot handle
     the /api/resolve-cache/ redirect → MissingSchema / FileNotFoundError).
  2. Model file format mismatch: HuggingFace distributes model.safetensors
     but old transformers looks for pytorch_model.bin.
  3. Tokenizer default-value binding: DEFAULT_TOKENIZER_PATH is resolved at
     function-definition time so runtime overrides of the module-level variable
     are silently ignored.

Fix: monkey-patch sapiens.predict_scores to:
  - Auto-detect the local HuggingFace snapshot directory for each model.
  - Convert model.safetensors → pytorch_model.bin when necessary.
  - Inject checkpoint_path and tokenizer_path as explicit keyword arguments
    so they are not subject to default-binding.

This module is imported automatically by agent_api.py before any sapiens call.
"""

import os
import glob as _glob


def _find_hf_snapshot(repo_name_fragment: str) -> str | None:
    """Return the newest snapshot directory matching *repo_name_fragment*, or None."""
    cache_base = os.path.expanduser("~/.cache/huggingface/hub")
    pattern = os.path.join(cache_base, f"models--*{repo_name_fragment}*", "snapshots", "*")
    snapshots = sorted(_glob.glob(pattern))
    return snapshots[-1] if snapshots else None


def _ensure_pytorch_model_bin(snapshot_dir: str) -> None:
    """Convert model.safetensors → pytorch_model.bin inside *snapshot_dir* if needed."""
    bin_path = os.path.join(snapshot_dir, "pytorch_model.bin")
    st_path = os.path.join(snapshot_dir, "model.safetensors")
    if not os.path.exists(bin_path) and os.path.exists(st_path):
        try:
            from safetensors.torch import load_file
            import torch
            state_dict = load_file(st_path)
            torch.save(state_dict, bin_path)
        except Exception:
            pass  # Conversion failed — sapiens may still load via safetensors natively


def _patch_sapiens():
    try:
        import sapiens as _sapiens
    except ImportError:
        return  # sapiens not installed — nothing to patch

    _original = _sapiens.predict_scores

    def _patched_predict_scores(seq, chain_type, checkpoint_path=None, tokenizer_path=None, **kw):
        # Determine which model variant to look for (VH vs VL)
        chain_str = str(chain_type).upper()
        model_suffix = "vh" if chain_str in ("H", "VH", "HEAVY") else "vl"

        # Auto-inject checkpoint_path from local HF cache when not provided
        if checkpoint_path is None:
            snapshot = _find_hf_snapshot(f"biophi-sapiens1-{model_suffix}")
            if snapshot:
                _ensure_pytorch_model_bin(snapshot)
                checkpoint_path = snapshot

        # Always inject tokenizer_path explicitly to bypass default-value binding
        if tokenizer_path is None:
            tok_snapshot = _find_hf_snapshot("biophi-sapiens1-tokenizer")
            if tok_snapshot:
                tokenizer_path = tok_snapshot

        # Only pass the args the original accepts
        if checkpoint_path is not None:
            kw["checkpoint_path"] = checkpoint_path
        if tokenizer_path is not None:
            kw["tokenizer_path"] = tokenizer_path

        return _original(seq=seq, chain_type=chain_type, **kw)

    # Patch module-level reference (used by external callers)
    _sapiens.predict_scores = _patched_predict_scores

    # Also patch the inner module where the function is defined, if accessible
    try:
        import sapiens.predict as _sp
        if hasattr(_sp, "predict_scores"):
            _sp.predict_scores = _patched_predict_scores
    except Exception:
        pass


# Apply immediately on import
_patch_sapiens()
