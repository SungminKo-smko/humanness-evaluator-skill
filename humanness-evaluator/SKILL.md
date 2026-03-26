---
name: humanness-evaluator
description: Evaluate humanness scores for antibody sequences using OASis (Oxford Antibody Structure Informatics Suite). Automatically process batch CSV files with designed VH sequences and generate comprehensive humanness metrics. Use this skill whenever the user has antibody sequences and needs to assess immunogenicity risk through OASis identity scores, germline content, or humanizing mutations. Triggers on phrases like "humanness score", "OASis evaluation", "antibody humanization metrics", or when handling designed antibody CSV files.
---

# Humanness Evaluator Skill

Batch evaluation of antibody humanness using **BioPhiSkill** and **OASis** (Oxford Antibody Structure Informatics Suite).

## Quick Start

### 1. Installation (One-time setup)

```bash
# Clone BioPhiSkill
git clone https://github.com/Shaperon-AIDEN/BioPhiSkill.git
cd BioPhiSkill
bash install.sh
conda activate biophi
```

### 2. Basic Usage

**Option A: Evaluate a CSV with multiple sequences**

```python
from humanness_evaluator import evaluate_csv

# Reads 'designed_chain_sequence' column from your CSV
results = evaluate_csv(
    csv_path="designs.csv",
    output_excel="results.xlsx"
)
```

**Option B: Evaluate a single sequence**

```python
from humanness_evaluator import evaluate_single

result = evaluate_single(
    vh_sequence="EVQLVESGGGLVQPGG...",
    sequence_id="design_001"
)
print(f"Humanness: {result['humanness_score']}%")
```

### 3. Output

Returns Excel workbook with columns:
- **Humanness_Score** (OASis Identity %) — main metric
- OASis_Percentile (0-1 ranking)
- Germline_Content (% matching germline)
- Germlines (before/after analysis)
- Humanizing_Mutations_Count

---

## What is OASis Humanness?

**OASis** measures "humanness" by:

1. **Peptide Fragmentation**: Breaks VH sequence into overlapping 9-mer windows
2. **Database Query**: Checks each peptide against ~200 billion human antibody sequences
3. **Human Match Scoring**: Counts peptides found in real human antibodies
4. **Identity Calculation**: `OASis Identity = (human peptides / total peptides) × 100`

**Interpretation:**
- **>70%**: Good humanization, lower immunogenicity risk
- **50-70%**: Moderate, consider additional humanization
- **<50%**: Poor, high immunogenicity risk

---

## Core Functions

### `evaluate_csv(csv_path, output_excel, vh_column="designed_chain_sequence")`

Process batch of sequences from CSV.

**Parameters:**
- `csv_path` (str): Input CSV with sequence column
- `output_excel` (str): Output filename (e.g., "results.xlsx")
- `vh_column` (str): Column name containing VH sequences (default: "designed_chain_sequence")

**Returns:** DataFrame with results

**Example:**
```python
from humanness_evaluator import evaluate_csv

df = evaluate_csv(
    csv_path="final_designs_metrics_100.csv",
    output_excel="humanness_results.xlsx"
)

# Summary statistics
print(f"Mean Humanness: {df['Humanness_Score'].mean():.2f}%")
print(f"Range: {df['Humanness_Score'].min():.2f}% - {df['Humanness_Score'].max():.2f}%")
```

---

### `evaluate_single(vh_sequence, vl_sequence=None, sequence_id="")`

Evaluate a single VH (and optional VL) sequence.

**Parameters:**
- `vh_sequence` (str): Heavy chain amino acid sequence
- `vl_sequence` (str, optional): Light chain sequence for full antibody
- `sequence_id` (str, optional): Sequence identifier for reporting

**Returns:** dict with keys:
- `humanness_score`: OASis Identity (%)
- `oasis_percentile`: Percentile ranking (0-1)
- `germline_content`: % matching germline
- `mutations_count`: Number of humanizing mutations
- `germlines`: {vh_before, vh_after, vl_before, vl_after}

**Example:**
```python
from humanness_evaluator import evaluate_single

result = evaluate_single(
    vh_sequence="EVQLVESGGGLVQPGGSLRLSCAA...",
    sequence_id="my_design_001"
)

if result['humanness_score'] > 70:
    print("✓ Good humanization!")
else:
    print("⚠ Consider further optimization")
```

---

## Expected Workflow

### Scenario 1: Batch Evaluation (Most Common)

You have 50+ designed antibody sequences in a CSV:

```bash
# 1. Activate environment
conda activate biophi

# 2. Run evaluation
python -c "
from humanness_evaluator import evaluate_csv
evaluate_csv('my_designs.csv', 'humanness_results.xlsx')
"

# 3. Check results in Excel
# humanness_results.xlsx now contains all metrics
```

### Scenario 2: Single Sequence Testing

Quick evaluation of one design:

```python
from humanness_evaluator import evaluate_single

# After rational design or AI generation
result = evaluate_single(
    vh_sequence="EVQL...",  # Your designed sequence
    sequence_id="variant_A"
)

# Decide if humanization is needed
if result['humanness_score'] < 65:
    print(f"Humanness: {result['humanness_score']}% → Needs optimization")
```

---

## Output Columns Reference

| Column | Range | Interpretation |
|--------|-------|-----------------|
| **Humanness_Score** | 0-100 | % OASis Identity → **main metric** |
| OASis_Percentile | 0.0-1.0 | Ranking vs database |
| Germline_Content_% | 0-100 | % similar to known germlines |
| VH_Germline_Before | - | Original IGHV gene |
| VH_Germline_After | - | Best-matching gene after analysis |
| Humanizing_Mutations_Count | 0+ | Mutations improving humanness |

**Decision Framework:**
```
Humanness Score (OASis Identity)
├─ >75% ✓✓ Excellent (ready for clinic)
├─ 70-75% ✓ Good (acceptable)
├─ 60-70% ~ Fair (consider optimization)
├─ 50-60% ⚠ Poor (recommend redesign)
└─ <50% ❌ Very Poor (needs major changes)
```

---

## Common Use Cases

### Case 1: De Novo Design Screening

You've designed 100 VH sequences computationally:

```python
from humanness_evaluator import evaluate_csv

# Get metrics on all designs
results = evaluate_csv(
    csv_path="designs.csv",
    vh_column="vh_sequence"
)

# Filter for good candidates
good_designs = results[results['Humanness_Score'] > 70]
print(f"✓ {len(good_designs)}/{len(results)} pass humanness threshold")
```

### Case 2: Humanization Validation

You've applied humanization (e.g., germline grafting):

```python
from humanness_evaluator import evaluate_single

# Before humanization
before = evaluate_single(vh_sequence=original_vh, sequence_id="original")
# After humanization
after = evaluate_single(vh_sequence=humanized_vh, sequence_id="humanized")

improvement = after['humanness_score'] - before['humanness_score']
print(f"Humanization improvement: +{improvement:.1f}%")
```

### Case 3: CDR Grafting Assessment

You've grafted CDRs from a donor onto a human framework:

```python
# Compare original vs CDR-grafted
results = evaluate_csv(
    csv_path="cdr_grafting_results.csv",
    output_excel="humanness_comparison.xlsx"
)

# Identify best CDR donors by humanness
best = results.nlargest(5, 'Humanness_Score')
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'agent_api'"

❌ **Problem**: BioPhiSkill not installed

**Solution**:
```bash
git clone https://github.com/Shaperon-AIDEN/BioPhiSkill.git
cd BioPhiSkill
bash install.sh
conda activate biophi
```

### "Azure API timeout"

❌ **Problem**: Network issue or API temporarily unavailable

**Solution**: 
- Retry in a few minutes
- Check internet connection
- Verify firewall allows HTTPS to Azure

### "Sequence too short"

❌ **Problem**: VH sequence < 9 amino acids

**Solution**: Check input CSV for malformed sequences

### "Column 'designed_chain_sequence' not found"

❌ **Problem**: CSV has different column name

**Solution**: Specify correct column:
```python
evaluate_csv(
    csv_path="file.csv",
    vh_column="custom_vh_column_name"  # ← change this
)
```

---

## Performance Notes

**Expected Runtime:**
- Single sequence: ~5-10 seconds
- 100 sequences: ~8-15 minutes (depends on API latency)
- 1000 sequences: ~1-2 hours

**Factors:**
- Azure OASis API response time (usually <5s per sequence)
- Network stability
- Sequence length (longer = more peptides = slightly longer)

---

## Why Humanness Matters

Research shows humanness correlation with clinical outcomes:

| Metric | Outcome |
|--------|---------|
| **OASis Identity** | ↑ Identity → ↓ Immunogenicity |
| **Germline Content** | ↑ Content → ↓ T-cell rejection risk |
| **CDR Grafting** | Preserves binding while improving humanness |

**Published targets:**
- FDA-approved mAbs: typically **70-85% OASis Identity**
- Lead clinical candidates: **>65% OASis Identity**

---

## Related Skills & Tools

- **BioPhiSkill**: Source library (humanization + OASis)
- **IMGT Numbering**: Needed for proper CDR definition
- **Germline Databases**: Imported from IMGT

---

## References

- OASis Paper: [Oxford-based humanness prediction](https://doi.org/10.1038/s41598-021-95505-6)
- IMGT: [Official antibody numbering](http://www.imgt.org)
- BioPhiSkill: [GitHub repo](https://github.com/Shaperon-AIDEN/BioPhiSkill)
