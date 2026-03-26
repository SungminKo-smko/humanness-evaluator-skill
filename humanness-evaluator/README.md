# Humanness Evaluator Skill

Batch evaluation of antibody humanness using **BioPhiSkill** and **OASis** (Oxford Antibody Structure Informatics Suite).

## What It Does

- **Evaluates humanness** of designed antibody sequences
- **Calculates OASis Identity** (% similarity to natural human antibodies)
- **Predicts immunogenicity risk** (higher humanness = lower risk)
- **Processes CSV files** with multiple sequences
- **Generates Excel reports** with all metrics

## Quick Start

### Install

```bash
git clone https://github.com/Shaperon-AIDEN/BioPhiSkill.git
cd BioPhiSkill
bash install.sh
conda activate biophi
```

### Use

```python
from humanness_evaluator import evaluate_csv, evaluate_single

# Batch evaluation
results = evaluate_csv("designs.csv", "results.xlsx")

# Single sequence
result = evaluate_single("EVQLVESGG...")
print(f"Humanness: {result['humanness_score']:.1f}%")
```

## Skill Structure

```
humanness-evaluator/
├── SKILL.md                          # Main skill definition
├── __init__.py                       # Package init
├── test_cases.json                   # Test cases for evaluation
├── scripts/
│   └── humanness_evaluator.py        # Main implementation
└── references/
    ├── oasis_metrics.md              # Detailed OASis explanation
    └── examples_and_faq.md           # Examples and FAQ
```

## Key Files

- **SKILL.md**: Skill definition, API reference, use cases
- **humanness_evaluator.py**: Core implementation (batch + single evaluation)
- **oasis_metrics.md**: Deep dive into OASis humanness metrics
- **examples_and_faq.md**: Code examples and frequently asked questions

## When to Use

Use this skill when the user:
- Has antibody sequences and needs humanness scores
- Wants to evaluate OASis identity
- Needs to predict immunogenicity risk
- Has a CSV with multiple designed sequences
- Wants to filter/rank designs by humanness
- Needs germline content and humanizing mutation counts

Trigger phrases:
- "humanness score"
- "OASis evaluation"
- "antibody humanization metrics"
- "immunogenicity risk"
- Mention of CSV with antibody sequences

## Features

✅ **Batch Processing**: Evaluate 100+ sequences automatically
✅ **Excel Output**: Comprehensive reports with all metrics
✅ **Progress Tracking**: Real-time feedback during evaluation
✅ **Error Handling**: Graceful handling of invalid sequences
✅ **Summary Statistics**: Mean, median, min/max humanness
✅ **Quality Distribution**: Break down into excellent/good/fair/poor

## Output Metrics

| Column | Description |
|--------|-------------|
| **Humanness_Score** | OASis Identity (%) — main metric |
| OASis_Percentile | Percentile ranking (0-1) |
| Germline_Content_% | % matching known germline genes |
| Humanizing_Mutations_Count | # of mutations improving humanness |
| Germlines | VH germline genes before/after |

## Interpretation Guide

- **>75%**: Excellent humanization (ready for clinic)
- **70-75%**: Good humanization (acceptable)
- **60-70%**: Fair humanization (consider optimization)
- **<60%**: Poor humanization (recommend redesign)

## Dependencies

- Python 3.9+
- BioPhiSkill
- pandas
- openpyxl

## Notes

- Requires BioPhiSkill installation (uses Sapiens + Azure OASis API)
- Processing time: ~5-10 sec per sequence
- OASis API must be accessible (Azure endpoint)

## License

Inherits from BioPhiSkill and OASis
