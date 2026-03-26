# Humanness Evaluator - Examples & FAQ

## Quick Examples

### Example 1: Evaluate Your Design CSV

```python
from humanness_evaluator import evaluate_csv

# Simplest usage
results = evaluate_csv("my_designs.csv", "results.xlsx")

# With custom column name
results = evaluate_csv(
    csv_path="designs.csv",
    output_excel="humanness_scores.xlsx",
    vh_column="VH_sequence"  # if your column has different name
)
```

**Expected Output**: Excel file with all humanness metrics

---

### Example 2: Evaluate Single Sequence

```python
from humanness_evaluator import evaluate_single

# Quick evaluation
result = evaluate_single("EVQLVESGGGLVQPGG...")

if result['success']:
    score = result['humanness_score']
    percentile = result['oasis_percentile']
    print(f"Humanness: {score:.1f}% (Percentile: {percentile:.2f})")
else:
    print(f"Error: {result['error']}")
```

---

### Example 3: Batch Process with Custom IDs

```python
from humanness_evaluator import evaluate_batch

sequences = [
    {'sequence_id': 'design_A', 'vh_sequence': 'EVQL...'},
    {'sequence_id': 'design_B', 'vh_sequence': 'DVQL...'},
    {'sequence_id': 'design_C', 'vh_sequence': 'QVQL...'},
]

results = evaluate_batch(
    sequences=sequences,
    output_excel="batch_results.xlsx"
)

# Access results
print(results[['sequence_id', 'humanness_score']])
```

---

### Example 4: Filter High-Quality Designs

```python
from humanness_evaluator import evaluate_csv

results = evaluate_csv("designs.csv", "full_results.xlsx")

# Get only good humanization
good = results[results['Humanness_Score'] > 70]
print(f"✓ {len(good)}/{len(results)} pass humanness threshold")

# Save filtered set
good.to_excel("high_quality_designs.xlsx")

# Get stats
print(f"Mean humanness: {good['Humanness_Score'].mean():.1f}%")
```

---

### Example 5: Compare Before/After Humanization

```python
from humanness_evaluator import evaluate_single

# Original sequence (poorly humanized)
original = evaluate_single(
    vh_sequence="DVQLVESGGGLVQPGG...",
    sequence_id="original"
)

# After optimization
optimized = evaluate_single(
    vh_sequence="EVQLVESGGGLVQPGG...",  # Framework changes
    sequence_id="optimized"
)

improvement = optimized['humanness_score'] - original['humanness_score']
print(f"Improvement: {original['humanness_score']:.1f}% → "
      f"{optimized['humanness_score']:.1f}% (+{improvement:.1f}%)")
```

---

### Example 6: Rank Designs by Humanness

```python
from humanness_evaluator import evaluate_csv

results = evaluate_csv("designs.csv", "ranked_results.xlsx")

# Sort by humanness descending
ranked = results.sort_values('Humanness_Score', ascending=False)

# Show top 10
print("Top 10 most human designs:")
print(ranked[['ID', 'Rank', 'Humanness_Score']].head(10).to_string())

# Save ranking
ranked.to_excel("designs_ranked_by_humanness.xlsx")
```

---

## FAQ

### Q1: What does "Humanness Score" actually measure?

**A**: It's the **OASis Identity** percentage—how many 9-amino acid peptide windows from your sequence appear in real human antibodies. 

- 70% means 70 out of 100 peptide windows were found in humans
- Higher = more similar to naturally occurring human antibodies
- Higher = lower predicted immunogenicity

See `references/oasis_metrics.md` for details.

---

### Q2: What's a "good" humanness score?

**A**: Depends on your application:

| Target | Score | Use Case |
|--------|-------|----------|
| **Research** | >55% | Proof-of-concept, preclinical |
| **IND-enabling** | >65% | Toxicology studies |
| **Clinical (Phase 1)** | >70% | First-in-human trials |
| **Commercial** | >72% | FDA approval-track |

FDA-approved mAbs typically score **70-85%**.

---

### Q3: How long does evaluation take?

**A**: Roughly:
- **1 sequence**: 5-10 seconds
- **100 sequences**: 8-15 minutes
- **1000 sequences**: 1-2 hours

Mostly bottleneck is Azure OASis API response time. Network latency matters.

---

### Q4: Can I evaluate light chains (VL)?

**A**: Yes! Pass `vl_sequence` parameter:

```python
result = evaluate_single(
    vh_sequence="EVQLVESGG...",
    vl_sequence="DIQMTQSPS..."  # Light chain
)
```

Result includes both VH and VL metrics.

---

### Q5: The score seems low. What should I do?

**A**: Try these strategies:

1. **Check sequence quality**: Is it valid? No 'X' characters?
2. **Germline grafting**: Replace framework with human IGHV genes
3. **CDR optimization**: Modify CDRs to use more human-like residues
4. **Run again**: API variance can give ±2-3%

Then re-evaluate and compare before/after scores.

---

### Q6: My CSV has thousands of sequences. Will it work?

**A**: Yes, but plan for time:
- 10,000 sequences = ~15-20 hours (depends on network)
- Recommendation: Break into batches of 500-1000
- Run overnight

```python
# Option: Run in chunks
for i in range(0, len(df), 500):
    chunk = df.iloc[i:i+500]
    chunk.to_csv(f"batch_{i}.csv")
    evaluate_csv(f"batch_{i}.csv", f"results_{i}.xlsx")
```

---

### Q7: What if Azure API is down?

**A**: 
- Check your internet connection
- Wait a few minutes and retry
- Check Azure status: https://status.azure.com
- Error message will tell you the issue

---

### Q8: Can I evaluate antibodies with non-standard regions?

**A**: OASis works best on standard VH sequences. Edge cases:

- **Scfv fragments**: Evaluate VH only, ignore linker+VL
- **Nanobodies (VHH)**: Different database, may need different tool
- **CDR-Only grafts**: Evaluate full chain, not just CDR
- **Humanized chimera**: Evaluate humanized variable domains

---

### Q9: How do I interpret germline genes?

**A**: Example output:

```
VH_Germline_Before: IGHV1-69*01
VH_Germline_After:  IGHV1-2*02
```

This means:
- Original sequence best matches `IGHV1-69` allele
- After analysis, looks more like `IGHV1-2` allele
- Germanline genes from IMGT database

Higher match = more "human-like"

---

### Q10: Is humanness score the only thing that matters?

**A**: No! Important trade-offs:

| Factor | Impact | Trade-off |
|--------|--------|-----------|
| **Humanness** | ↓ Immunogenicity | vs Binding affinity |
| **Germline match** | ↓ T-cell response | vs CDR grafting |
| **Mutation count** | Stability | vs Binding |

**You should also measure**:
- Binding affinity (ELISA, SPR, FortéBio)
- Expression levels (mammalian cells)
- Stability (thermal shift, aggregation)
- Actual immunogenicity (animal models)

Humanness is **predictive**, not definitive.

---

### Q11: Can I use this for other protein targets?

**A**: OASis is **antibody-specific**. It won't work for:
- Protein scaffolds (fibronectin, etc.)
- Non-antibody biologics
- TCRs (T-cell receptors)
- Nanobodies (different germline database)

For these, you'd need other humanness tools.

---

### Q12: Why do similar sequences have different scores?

**A**: Reasons:

1. **API variance**: ±2-3% normal variation
2. **Peptide overlap**: One amino acid change affects multiple 9-mers
3. **Database updates**: OASis database occasionally refreshed
4. **Sequence length**: Shorter = higher variance in score

Try:
- Re-run to confirm
- Focus on relative ranking, not absolute numbers

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'agent_api'"

**Cause**: BioPhiSkill not installed

**Fix**:
```bash
git clone https://github.com/Shaperon-AIDEN/BioPhiSkill.git
cd BioPhiSkill
bash install.sh
conda activate biophi
```

---

### Error: "Column 'designed_chain_sequence' not found"

**Cause**: CSV has different column name

**Fix**: Specify the correct column:
```python
evaluate_csv(
    csv_path="file.csv",
    vh_column="my_vh_column"  # Use your column name
)
```

---

### Error: "Azure API timeout"

**Cause**: Network issue or API latency

**Fix**: 
- Check internet connection
- Retry in a few minutes
- Try smaller batch

---

### Scores look suspiciously high/low

**Cause**: Possible API variance or sequence issues

**Fix**:
- Verify sequence quality (no invalid amino acids)
- Re-run to confirm
- Check if VH or VL was evaluated

---

## Integration with Your Workflow

### Step 1: Design Sequences

```
Computational design (RoseTTAFold, ProteinMPNN, etc.)
         ↓
Generates ~100 candidate sequences
```

### Step 2: Evaluate Humanness

```python
from humanness_evaluator import evaluate_csv

results = evaluate_csv("candidates.csv")
```

### Step 3: Filter & Prioritize

```python
good = results[results['Humanness_Score'] > 70]
best = good.sort_values('Humanness_Score', ascending=False)
```

### Step 4: Synthesis & Testing

```
Order top 10 for synthesis
         ↓
ELISA binding assay
         ↓
SPR kinetics (if good)
         ↓
Select best for preclinical
```

### Step 5: Optional Re-optimization

```
If humanness was limiting:
  - Apply germline grafting
  - Modify framework residues
  - Re-evaluate
```

---

## References

- **OASis Paper**: https://doi.org/10.1038/s41598-021-95505-6
- **BioPhiSkill**: https://github.com/Shaperon-AIDEN/BioPhiSkill
- **IMGT**: http://www.imgt.org
- **OAS Database**: https://opig.stats.ox.ac.uk/webapps/oas/
