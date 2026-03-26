# Troubleshooting

## ModuleNotFoundError: No module named 'agent_api'

BioPhiSkill not installed or conda env not active.

```bash
conda activate biophi
```

## Column not found error

Specify the correct column name:

```python
evaluate_csv("file.csv", vh_column="your_column_name")
```

## Azure API timeout

- Retry in a few minutes
- Check internet / firewall allows HTTPS to Azure

## Sequence too short

VH sequence must be ≥9 amino acids. Check input CSV for malformed entries.
