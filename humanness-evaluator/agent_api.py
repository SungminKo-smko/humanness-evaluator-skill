"""
BioPhiSkill Agent API
=====================
A single-function entry point for AI agents to perform antibody humanization
and evaluate humanness using the Sapiens model and the Azure OASis API.

Functions
---------
- humanize_antibody_sequence: Full Sapiens humanization + before/after OASis evaluation + visualization
- evaluate_humanness: OASis-only evaluation (no humanization)

Usage (after installing from GitHub)
-------------------------------------
    git clone https://github.com/Shaperon-AIDEN/BioPhiSkill.git
    cd BioPhiSkill && bash install.sh
    conda activate biophi

    from agent_api import humanize_antibody_sequence
    result = humanize_antibody_sequence(vh_seq="EVQLQQSGAELVRPGAL...", output_dir="./output")
    print(result["summary"])
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

# Auto-apply ANARCI compatibility patch for Python 3.12+
# This must happen BEFORE any abnumber/anarci imports
try:
    _skill_dir = os.path.dirname(os.path.abspath(__file__))
    if _skill_dir not in sys.path:
        sys.path.insert(0, _skill_dir)
    from patches import anarci_compat  # noqa: F401
    from patches import sapiens_compat  # noqa: F401
except Exception:
    pass  # If patch fails, proceed anyway — may work on Python <=3.11

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from abnumber import Chain
from biophi.humanization.methods.humanization import (
    SapiensHumanizationParams,
    humanize_chain,
)
from biophi.humanization.methods.humanness import (
    get_chain_humanness,
    get_antibody_humanness,
    OASisParams,
)

OASIS_API_URL = "https://biophioasisapi.azurewebsites.net/api/peptides/"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def humanize_antibody_sequence(
    vh_seq: str,
    vl_seq: str = None,
    scheme: str = "imgt",
    cdr_definition: str = "imgt",
    sapiens_iterations: int = 1,
    humanize_cdrs: bool = False,
    oasis_api_url: str = OASIS_API_URL,
    min_fraction_subjects: float = 0.1,
    output_dir: str = "output",
) -> dict:
    """
    Perform Sapiens antibody humanization and evaluate humanness before/after.

    Parameters
    ----------
    vh_seq : str
        Heavy chain amino acid sequence (required).
    vl_seq : str, optional
        Light chain amino acid sequence.
    scheme : str
        Numbering scheme ('imgt', 'kabat', 'chothia'). Default 'imgt'.
    cdr_definition : str
        CDR definition ('imgt', 'kabat', 'chothia'). Default 'imgt'.
    sapiens_iterations : int
        Number of Sapiens humanization iterations. Default 1.
    humanize_cdrs : bool
        Whether to humanize CDR regions. Default False (parental CDRs retained).
    oasis_api_url : str
        Azure OASis REST API endpoint URL.
    min_fraction_subjects : float
        OASis subject frequency threshold (default 0.1 = 10%).
    output_dir : str
        Directory to save plot and Excel report.

    Returns
    -------
    dict with keys:
        - summary (str)       : Human-readable summary of results
        - vh_mutations (list) : [{position, from, to}, ...] for VH
        - vl_mutations (list) : [{position, from, to}, ...] for VL
        - before (dict)       : OASis identity, percentile, germline content (before)
        - after  (dict)       : OASis identity, percentile, germline content (after)
        - germlines (dict)    : VH/VL germline gene names before and after
        - plot_image (str)    : Path to saved PNG plot
        - excel_report (str)  : Path to saved Excel report
    """
    os.makedirs(output_dir, exist_ok=True)

    oasis_params = OASisParams(
        oasis_db_path=oasis_api_url,
        min_fraction_subjects=min_fraction_subjects,
    )
    humanization_params = SapiensHumanizationParams(
        scheme=scheme,
        cdr_definition=cdr_definition,
        iterations=sapiens_iterations,
        humanize_cdrs=humanize_cdrs,
    )

    print(f"[1/4] Parsing sequences with scheme={scheme}...")
    parental_vh = Chain(vh_seq, scheme=scheme, cdr_definition=cdr_definition) if vh_seq else None
    parental_vl = Chain(vl_seq, scheme=scheme, cdr_definition=cdr_definition) if vl_seq else None

    print("[2/4] Running Sapiens humanization...")
    vh_humanization = humanize_chain(parental_vh, humanization_params) if parental_vh else None
    vl_humanization = humanize_chain(parental_vl, humanization_params) if parental_vl else None

    humanized_vh = vh_humanization.humanized_chain if vh_humanization else None
    humanized_vl = vl_humanization.humanized_chain if vl_humanization else None

    print("[3/4] Evaluating OASis humanness (before & after)...")
    before_vh = get_chain_humanness(parental_vh, params=oasis_params) if parental_vh else None
    before_vl = get_chain_humanness(parental_vl, params=oasis_params) if parental_vl else None
    after_vh  = get_chain_humanness(humanized_vh, params=oasis_params) if humanized_vh else None
    after_vl  = get_chain_humanness(humanized_vl, params=oasis_params) if humanized_vl else None

    # ---- Mutations ----
    vh_mutations = _extract_mutations(vh_humanization) if vh_humanization else []
    vl_mutations = _extract_mutations(vl_humanization) if vl_humanization else []

    # ---- OASis metrics ----
    t = min_fraction_subjects
    before = _metrics(before_vh, before_vl, t)
    after  = _metrics(after_vh,  after_vl,  t)

    # ---- Germlines ----
    germlines = {
        "vh_before": _germline(before_vh),
        "vh_after":  _germline(after_vh),
        "vl_before": _germline(before_vl),
        "vl_after":  _germline(after_vl),
    }

    print("[4/4] Generating plots and Excel report...")
    plot_path  = _save_plots(before_vh, after_vh, before_vl, after_vl, t, output_dir)
    excel_path = _save_excel(
        vh_humanization, vl_humanization,
        before_vh, after_vh, before_vl, after_vl,
        output_dir
    )

    summary = _build_summary(vh_mutations, vl_mutations, before, after, germlines, t, plot_path)
    print(summary)

    return {
        "summary": summary,
        "vh_mutations": vh_mutations,
        "vl_mutations": vl_mutations,
        "before": before,
        "after": after,
        "germlines": germlines,
        "plot_image": plot_path,
        "excel_report": excel_path,
    }


def evaluate_humanness(
    vh_seq: str,
    vl_seq: str = None,
    scheme: str = "imgt",
    cdr_definition: str = "imgt",
    oasis_api_url: str = OASIS_API_URL,
    min_fraction_subjects: float = 0.1,
    output_dir: str = "output",
) -> dict:
    """
    Evaluate OASis humanness of an antibody sequence WITHOUT humanization.

    Returns
    -------
    dict with keys: summary, oasis_identity, oasis_percentile, germline_content,
                    germlines, plot_image, excel_report
    """
    os.makedirs(output_dir, exist_ok=True)
    oasis_params = OASisParams(oasis_db_path=oasis_api_url, min_fraction_subjects=min_fraction_subjects)

    chain_vh = Chain(vh_seq, scheme=scheme, cdr_definition=cdr_definition) if vh_seq else None
    chain_vl = Chain(vl_seq, scheme=scheme, cdr_definition=cdr_definition) if vl_seq else None

    print("[1/2] Evaluating OASis humanness...")
    humanness_vh = get_chain_humanness(chain_vh, params=oasis_params) if chain_vh else None
    humanness_vl = get_chain_humanness(chain_vl, params=oasis_params) if chain_vl else None

    t = min_fraction_subjects
    metrics = _metrics(humanness_vh, humanness_vl, t)

    print("[2/2] Saving plot and Excel report...")
    plot_path  = _save_plots(humanness_vh, None, humanness_vl, None, t, output_dir, compare=False)
    excel_path = _save_excel(None, None, humanness_vh, None, humanness_vl, None, output_dir)

    summary_lines = [
        "=== OASis Humanness Evaluation ===",
        f"OASis Identity ({int(t*100)}%): {metrics['oasis_identity']:.1f}%",
        f"OASis Percentile: {metrics['oasis_percentile']:.2f}%",
        f"Germline Content: {metrics['germline_content']:.1f}%",
    ]
    if humanness_vh:
        summary_lines.append(f"VH Germline: {_germline(humanness_vh)}")
    if humanness_vl:
        summary_lines.append(f"VL Germline: {_germline(humanness_vl)}")
    summary_lines += [f"Plot: {plot_path}", f"Excel: {excel_path}"]
    summary = "\n".join(summary_lines)
    print(summary)

    return {
        **metrics,
        "germlines": {"vh": _germline(humanness_vh), "vl": _germline(humanness_vl)},
        "summary": summary,
        "plot_image": plot_path,
        "excel_report": excel_path,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_mutations(chain_humanization):
    if chain_humanization is None:
        return []
    mutations = []
    aln = chain_humanization.alignment
    for pos in aln.positions:
        from_aa, to_aa = aln[pos]
        if from_aa not in (None, '-', '') and to_aa not in (None, '-', '') and from_aa != to_aa:
            mutations.append({"position": str(pos), "from": from_aa, "to": to_aa})
    return mutations


def _metrics(vh_h, vl_h, t):
    def oasis_id(h):
        return h.get_oasis_identity(t) * 100 if h else None
    def oasis_pct(h):
        return h.get_oasis_percentile(t) * 100 if h else None
    def gc(h):
        return h.num_germline_residues / len(h.chain) * 100 if h else None

    num_human = sum(h.get_num_human_peptides(t) for h in [vh_h, vl_h] if h)
    num_total = sum(h.get_num_peptides() for h in [vh_h, vl_h] if h)
    combined_id = (num_human / num_total * 100) if num_total else None

    return {
        "oasis_identity": combined_id,
        "oasis_identity_vh": oasis_id(vh_h),
        "oasis_identity_vl": oasis_id(vl_h),
        "oasis_percentile": oasis_pct(vh_h),
        "germline_content": gc(vh_h),
        "germline_content_vl": gc(vl_h),
    }


def _germline(chain_h):
    if chain_h is None:
        return "N/A"
    v = chain_h.v_germline_names[0] if chain_h.v_germline_names else "?"
    j = chain_h.j_germline_names[0] if chain_h.j_germline_names else "?"
    return f"{v} / {j}"


def _save_plots(before_vh, after_vh, before_vl, after_vl, t, output_dir, compare=True):
    sns.set_theme(style="whitegrid", font_scale=0.9)
    chains = []
    if before_vh: chains.append(("VH", before_vh, after_vh))
    if before_vl: chains.append(("VL", before_vl, after_vl))

    n_chains = len(chains)
    n_cols = 2 if compare else 1
    fig, axes = plt.subplots(n_chains, n_cols, figsize=(14 * n_cols // 2, 5 * n_chains), squeeze=False)
    threshold_pct = t * 100

    for row, (chain_label, before_h, after_h) in enumerate(chains):
        for col, (label, humanness) in enumerate(
            (["Before", before_h], ["After", after_h]) if compare else [["", before_h]]
        ):
            if humanness is None:
                axes[row][col].set_visible(False)
                continue
            ax = axes[row][col]
            fracs = [p.fraction_oas_subjects for p in humanness.peptides.values()]
            fracs_pct = [f * 100 if f is not None else 0 for f in fracs]
            positions = list(range(len(fracs_pct)))

            colors = ["#e74c3c" if f < threshold_pct else "#2ecc71" for f in fracs_pct]
            ax.bar(positions, fracs_pct, color=colors, width=0.8)
            ax.axhline(threshold_pct, color="orange", linestyle="--", linewidth=1.5,
                       label=f"Threshold ({int(threshold_pct)}%)")

            title = f"{chain_label} {label} – OASis Identity: {humanness.get_oasis_identity(t)*100:.1f}%"
            ax.set_title(title, fontsize=11, fontweight="bold")
            ax.set_ylabel("OASis Subject %")
            ax.set_xlabel("Peptide Start Position")
            ax.set_ylim(0, 105)
            ax.legend(fontsize=8)

            pos_keys = list(humanness.peptides.keys())
            tick_every = max(1, len(pos_keys) // 15)
            ax.set_xticks(positions[::tick_every])
            ax.set_xticklabels([str(pos_keys[i]) for i in positions[::tick_every]], rotation=45, ha="right")

    plt.tight_layout()
    path = os.path.join(output_dir, "humanness_plot.png")
    plt.savefig(path, dpi=200, bbox_inches="tight")
    plt.close()
    return path


def _save_excel(vh_hzn, vl_hzn, before_vh, after_vh, before_vl, after_vl, output_dir):
    writer = pd.ExcelWriter(os.path.join(output_dir, "humanization_report.xlsx"), engine="openpyxl")
    rows = []
    for chain_label, before_h, after_h in [("VH", before_vh, after_vh), ("VL", before_vl, after_vl)]:
        if before_h:
            t = 0.1
            rows.append({
                "Chain": chain_label,
                "OASis Identity Before (%)": round(before_h.get_oasis_identity(t) * 100, 2),
                "OASis Identity After (%)": round(after_h.get_oasis_identity(t) * 100, 2) if after_h else "N/A",
                "OASis Percentile Before (%)": round(before_h.get_oasis_percentile(t) * 100, 2),
                "OASis Percentile After (%)": round(after_h.get_oasis_percentile(t) * 100, 2) if after_h else "N/A",
                "Germline Content Before (%)": round(before_h.num_germline_residues / len(before_h.chain) * 100, 2),
                "Germline Content After (%)": round(after_h.num_germline_residues / len(after_h.chain) * 100, 2) if after_h else "N/A",
                "V Germline Before": before_h.v_germline_names[0] if before_h.v_germline_names else "",
                "V Germline After": after_h.v_germline_names[0] if (after_h and after_h.v_germline_names) else "N/A",
                "J Germline Before": before_h.j_germline_names[0] if before_h.j_germline_names else "",
                "J Germline After": after_h.j_germline_names[0] if (after_h and after_h.j_germline_names) else "N/A",
            })
    pd.DataFrame(rows).to_excel(writer, sheet_name="Summary", index=False)

    mut_rows = []
    for chain_label, hzn in [("VH", vh_hzn), ("VL", vl_hzn)]:
        if hzn:
            for m in _extract_mutations(hzn):
                mut_rows.append({"Chain": chain_label, **m})
    if mut_rows:
        pd.DataFrame(mut_rows).to_excel(writer, sheet_name="Mutations", index=False)

    for chain_label, humanness in [("VH Before", before_vh), ("VH After", after_vh),
                                    ("VL Before", before_vl), ("VL After", after_vl)]:
        if humanness:
            try:
                humanness.to_peptide_dataframe().to_excel(writer, sheet_name=chain_label[:31], index=False)
            except Exception:
                pass

    writer.close()
    return os.path.join(output_dir, "humanization_report.xlsx")


def _build_summary(vh_mutations, vl_mutations, before, after, germlines, t, plot_path):
    def fmt(v):
        return f"{v:.2f}" if v is not None else "N/A"

    lines = [
        "=" * 48,
        "  BioPhiSkill – Humanization Summary",
        "=" * 48,
        "",
        "[Humanizing Mutations]",
        f"  VH: {len(vh_mutations)} mutations",
    ]
    if vl_mutations:
        lines.append(f"  VL: {len(vl_mutations)} mutations")
    if vh_mutations:
        lines.append("  VH changes: " + ", ".join(
            f"{m['from']}{m['position']}{m['to']}" for m in vh_mutations[:10]
        ) + ("…" if len(vh_mutations) > 10 else ""))
    lines += [
        "",
        f"[OASis Identity  (threshold={int(t*100)}%)]",
        f"  Combined Before: {fmt(before['oasis_identity'])}%",
        f"  Combined After : {fmt(after['oasis_identity'])}%",
        f"  VH Before: {fmt(before['oasis_identity_vh'])}%  →  After: {fmt(after['oasis_identity_vh'])}%",
    ]
    if before['oasis_identity_vl'] is not None:
        lines.append(f"  VL Before: {fmt(before['oasis_identity_vl'])}%  →  After: {fmt(after['oasis_identity_vl'])}%")
    lines += [
        "",
        "[OASis Percentile]",
        f"  VH Before: {fmt(before['oasis_percentile'])}%  →  After: {fmt(after['oasis_percentile'])}%",
        "",
        "[Germline Content]",
        f"  VH Before: {fmt(before['germline_content'])}%  →  After: {fmt(after['germline_content'])}%",
        "",
        "[Germlines]",
        f"  VH Before: {germlines['vh_before']}",
        f"  VH After : {germlines['vh_after']}",
    ]
    if germlines["vl_before"] != "N/A":
        lines += [f"  VL Before: {germlines['vl_before']}", f"  VL After : {germlines['vl_after']}"]
    lines += ["", "[Output]", f"  Plot  : {plot_path}", "=" * 48]
    return "\n".join(lines)
