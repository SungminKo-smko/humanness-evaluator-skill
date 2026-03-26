"""
Sample usage of the humanness-evaluator skill.
Run from repo root with: conda activate biophi && python examples/sample_usage.py
"""

from humanness_evaluator import evaluate_csv, evaluate_single

# --- Single sequence ---
result = evaluate_single(
    vh_sequence="EVQLVESGGGLVQPGGSLRLSCAASGFNIKDTYIHWVRQAPGKGLEWVARIYPTNGYTRYADSVKGRFTISADTSKNTAYLQMNSLRAEDTAVYYCSRWGGDGFYAMDYWGQGTLVTVSS",
    sequence_id="trastuzumab_vh"
)
print(f"Humanness: {result['humanness_score']:.1f}%")

# --- Batch CSV ---
results = evaluate_csv(
    csv_path="examples/sample_input.csv",
    output_excel="examples/sample_output.xlsx"
)
print(results[["sequence_id", "humanness_score"]])
