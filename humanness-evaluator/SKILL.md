---
name: humanness-evaluator
description: Evaluate humanness scores for antibody sequences using OASis (Oxford Antibody Structure Informatics Suite). Automatically process batch CSV files with designed VH sequences and generate comprehensive humanness metrics. Use this skill whenever the user has antibody sequences and needs to assess immunogenicity risk through OASis identity scores, germline content, or humanizing mutations. Triggers on phrases like "humanness score", "OASis evaluation", "antibody humanization metrics", or when handling designed antibody CSV files. Also supports full Sapiens humanization (before/after comparison) via the bundled BioPhiSkill engine.
---

# Humanness Evaluator Skill

Batch evaluation of antibody humanness using **OASis** (Oxford Antibody Structure Informatics Suite) and optional **Sapiens** humanization — fully bundled, no separate BioPhiSkill installation required.

## Installation (One-time setup)

```bash
# From the skill directory:
bash install.sh
conda activate biophi
```

> Requires [Miniconda](https://docs.conda.io/en/latest/miniconda.html). The installer creates a `biophi` conda environment with Python 3.9, HMMER, abnumber, and all pip dependencies.

## Quick Test

```bash
conda activate biophi
python -c "from agent_api import evaluate_humanness; print('Ready!')"
```

---

## Usage

### Option A: Evaluate a CSV with multiple sequences

```python
from humanness_evaluator import evaluate_csv

results = evaluate_csv(
    csv_path="designs.csv",       # must have 'designed_chain_sequence' column
    output_excel="results.xlsx"
)
print(f"Mean Humanness: {results['Humanness_Score'].mean():.1f}%")
```

### Option B: Evaluate a single sequence

```python
from humanness_evaluator import evaluate_single

result = evaluate_single(
    vh_sequence="EVQLVESGG...",
    sequence_id="design_001"
)
print(f"Humanness: {result['humanness_score']:.1f}%")
```

### Option C: Full humanization (Sapiens before/after)

```python
import sys
sys.path.insert(0, "/path/to/humanness-evaluator")  # skill root

from agent_api import humanize_antibody_sequence

result = humanize_antibody_sequence(
    vh_seq="EVQLQQSGAELVRPGAL...",
    output_dir="./output"
)
print(result["summary"])
```

---

## Output

Returns Excel workbook with columns:

| Column | Range | Interpretation |
|--------|-------|----------------|
| **Humanness_Score** | 0–100 | OASis Identity % — **main metric** |
| OASis_Percentile | 0.0–1.0 | Ranking vs human antibody database |
| Germline_Content_% | 0–100 | % similar to known germlines |
| VH_Germline_Before/After | — | IGHV / IGHJ gene assignment |
| Humanizing_Mutations_Count | 0+ | Mutations improving humanness |

**Decision framework:**
```
>75%    ✓✓  Excellent — ready for clinic
70–75%  ✓   Good — acceptable
60–70%  ~   Fair — consider optimization
50–60%  ⚠   Poor — recommend redesign
<50%    ❌  Very Poor — needs major changes
```

---

## Core Functions

### `evaluate_csv(csv_path, output_excel, vh_column="designed_chain_sequence")`

Process a batch of VH sequences from a CSV file.

```python
from humanness_evaluator import evaluate_csv

df = evaluate_csv("final_designs.csv", "humanness_results.xlsx")
good = df[df['Humanness_Score'] > 70]
print(f"{len(good)}/{len(df)} pass threshold")
```

### `evaluate_single(vh_sequence, vl_sequence=None, sequence_id="")`

Evaluate one VH (and optional VL) sequence.

```python
from humanness_evaluator import evaluate_single

result = evaluate_single("EVQL...", sequence_id="variant_A")
if result['humanness_score'] < 65:
    print("Needs optimization")
```

### `humanize_antibody_sequence(vh_seq, ...)` — from `agent_api`

Full Sapiens humanization with before/after OASis comparison.

```python
from agent_api import humanize_antibody_sequence

result = humanize_antibody_sequence(vh_seq="EVQL...", output_dir="./output")
# result keys: summary, vh_mutations, before, after, germlines, plot_image, excel_report
```

---

## Architecture

```
humanness-evaluator/          ← skill root (importable as Python package)
├── SKILL.md                  ← this file
├── install.sh                ← one-shot installer
├── environment.yml           ← conda env spec
├── setup.py                  ← biophi package installer
├── agent_api.py              ← bundled BioPhiSkill entry point
├── biophi/                   ← bundled BioPhiSkill core library
│   ├── humanization/
│   │   └── methods/
│   │       ├── humanization.py   (Sapiens)
│   │       ├── humanness.py      (OASis Azure API)
│   │       └── stats.py          (OASis percentile data)
│   └── common/
├── patches/                  ← ANARCI / Sapiens compatibility patches
├── scripts/
│   └── humanness_evaluator.py    ← batch CSV evaluator
└── references/
    ├── oasis_metrics.md
    └── examples_and_faq.md
```

**OASis API endpoint** (no local DB needed):
`https://biophioasisapi.azurewebsites.net/api/peptides/`

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'agent_api'"
Run `bash install.sh` and activate `conda activate biophi`.

### "Azure API timeout"
Retry in a few minutes. Requires internet access (HTTPS to Azure).

### "Column 'designed_chain_sequence' not found"
```python
evaluate_csv("file.csv", vh_column="your_column_name")
```

---

## Performance

| Scale | Expected time |
|-------|--------------|
| 1 sequence | ~5–10 sec |
| 100 sequences | ~8–15 min |
| 1000 sequences | ~1–2 hours |

---

## References

- OASis: [doi:10.1038/s41598-021-95505-6](https://doi.org/10.1038/s41598-021-95505-6)
- BioPhiSkill: [github.com/SungminKo-smko/BioPhiSkill](https://github.com/SungminKo-smko/BioPhiSkill)
- IMGT: [imgt.org](http://www.imgt.org)
