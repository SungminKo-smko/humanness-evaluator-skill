# Installation

## Prerequisites

- Python 3.9+
- conda (recommended)
- BioPhiSkill

## Step 1: Install BioPhiSkill

```bash
git clone https://github.com/Shaperon-AIDEN/BioPhiSkill.git
cd BioPhiSkill
bash install.sh
conda activate biophi
```

## Step 2: Install Python dependencies

```bash
pip install -r requirements.txt
```

## Step 3: (Optional) Install as package

```bash
pip install -e .
```

## Verify installation

```python
from humanness_evaluator import HumannessEvaluator
print("Installation OK")
```
