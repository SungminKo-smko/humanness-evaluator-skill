# humanness-evaluator-skill

Batch evaluation of antibody humanness scores using **BioPhiSkill** and **OASis** (Oxford Antibody Structure Informatics Suite).

## Overview

This repo contains the `humanness-evaluator` Claude Code skill — callable by Claude to assess immunogenicity risk of designed antibody sequences via OASis Identity scores.

## Structure

```
humanness-evaluator-skill/
├── humanness-evaluator/        # Skill package
│   ├── SKILL.md                # Skill definition & API reference
│   ├── README.md               # Skill-level documentation
│   ├── __init__.py             # Package init
│   ├── test_cases.json         # Reference test cases
│   ├── scripts/
│   │   └── humanness_evaluator.py
│   └── references/
│       ├── oasis_metrics.md
│       └── examples_and_faq.md
├── docs/
│   ├── INSTALLATION.md
│   ├── USAGE.md
│   └── TROUBLESHOOTING.md
├── examples/
│   ├── sample_input.csv
│   └── sample_usage.py
├── tests/
│   └── test_humanness_evaluator.py
├── .gitignore
├── LICENSE
├── requirements.txt
└── setup.py
```

## Quick Start

### 1. Install dependencies

```bash
git clone https://github.com/Shaperon-AIDEN/BioPhiSkill.git
cd BioPhiSkill && bash install.sh
conda activate biophi
pip install -r requirements.txt
```

### 2. Run evaluation

```python
from humanness_evaluator import evaluate_csv, evaluate_single

# Batch CSV evaluation
results = evaluate_csv("designs.csv", "results.xlsx")

# Single sequence
result = evaluate_single("EVQLVESGG...")
print(f"Humanness: {result['humanness_score']:.1f}%")
```

## Humanness Score Interpretation

| Score | Grade | Action |
|-------|-------|--------|
| >75% | Excellent | Ready for clinic |
| 70-75% | Good | Acceptable |
| 60-70% | Fair | Consider optimization |
| <60% | Poor | Recommend redesign |

## License

See [LICENSE](LICENSE).
