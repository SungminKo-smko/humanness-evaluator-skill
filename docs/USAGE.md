# Usage

## Batch CSV Evaluation

```python
from humanness_evaluator import evaluate_csv

results = evaluate_csv(
    csv_path="designs.csv",
    output_excel="results.xlsx",
    vh_column="designed_chain_sequence"  # default
)
print(f"Mean Humanness: {results['humanness_score'].mean():.2f}%")
```

## Single Sequence

```python
from humanness_evaluator import evaluate_single

result = evaluate_single(
    vh_sequence="EVQLVESGGGLVQPGG...",
    sequence_id="design_001"
)
print(f"Humanness: {result['humanness_score']:.1f}%")
```

## CLI

```bash
conda activate biophi
python -m humanness_evaluator.scripts.humanness_evaluator designs.csv -o results.xlsx
```

## Output Columns

| Column | Range | Description |
|--------|-------|-------------|
| Humanness_Score | 0-100 | OASis Identity % |
| OASis_Percentile | 0-1 | Percentile ranking |
| Germline_Content | 0-100 | % matching germline |
| Humanizing_Mutations_Count | 0+ | Mutations improving humanness |
