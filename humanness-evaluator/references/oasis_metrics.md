# OASis Humanness Metrics Reference

## Overview

OASis (Oxford Antibody Structure Informatics Suite) is a computational tool for predicting antibody humanness by comparing sequences against a database of real human antibodies.

## Key Metrics Explained

### 1. OASis Identity (%) - PRIMARY METRIC

**Definition**: Percentage of 9-amino acid peptide windows found in the human antibody database

**Calculation**:
```
OASis Identity (%) = (# peptides found in humans / total # peptides) × 100
```

**Ranges**:
- **>75%**: Excellent humanization → Ready for clinic
- **70-75%**: Good humanization → Acceptable
- **60-70%**: Fair humanization → Consider optimization
- **50-60%**: Poor humanization → Recommend redesign
- **<50%**: Very poor → Needs major changes

**What It Means**:
- Higher = more similar to naturally occurring human antibodies
- Higher = lower immunogenicity risk
- Published FDA-approved mAbs: 70-85%

**Example**:
- VH sequence breaks into 113 overlapping 9-mers
- 80 peptides match human database at ≥10% threshold
- OASis Identity = (80/113) × 100 = 70.8%

---

### 2. OASis Percentile

**Definition**: Percentile ranking vs. the entire human antibody database

**Range**: 0.0 (least human) to 1.0 (most human)

**Interpretation**:
- Percentile 0.5 = This sequence is more human than 50% of all human antibodies
- Percentile 0.9 = Excellent—more human than 90% of the database
- Percentile 0.1 = Poor—less human than 90% of the database

---

### 3. Germline Content (%)

**Definition**: Percentage of sequence matching known IGHV (heavy chain germline) genes

**Calculation**: Alignment against IMGT germline database

**Why It Matters**:
- Higher germline content = more naturally human
- Germlines are the evolutionary "starting templates" for all human antibodies
- V, D, J gene matching is key for avoiding T-cell rejection

**Typical Values**:
- Natural human antibodies: 85-95%
- Well-humanized antibodies: 75-85%
- Poorly humanized: <70%

**Breakdown**:
- VH germline: Heavy chain V gene
- DH germline: Diversity segment
- JH germline: J segment

---

### 4. Humanizing Mutations Count

**Definition**: Number of amino acid changes that improve humanness

**Why It Matters**:
- Each mutation trades "non-human" for "human" residues
- Too many mutations = loses binding (mutation load)
- 10-20 mutations typical for good humanization
- Depends on CDR content and framework residues

**Typical Pattern**:
- Framework regions: 5-15 mutations (safe)
- CDRs: 0-3 mutations (risky—affects binding)

---

## Database Details

### Human Antibody Database (~200 billion sequences)

**Source**: OAS (Observed Antibody Space)
- B-cell repertoires from healthy donors
- Published antibody sequences
- High-throughput antibody libraries

**Coverage**:
- Heavy chains (VH): Most human germlines well-represented
- Light chains (VL): Kappa and lambda chains
- All immunoglobulin classes (IgG, IgM, IgA, etc.)

**Peptide Threshold (default 10%)**:
- A 9-mer is considered "human" if it appears in ≥10% of OAS subjects
- Threshold balances:
  - High threshold (e.g., 30%) = stricter humanness
  - Low threshold (e.g., 5%) = more permissive

---

## Clinical Relevance

### Why Humanness Matters

Research shows strong correlation:

| Metric | Clinical Outcome |
|--------|-----------------|
| OASis Identity | ↑ → ↓ Immunogenicity |
| Germline Content | ↑ → ↓ T-cell rejection |
| CDR Humanization | Limited → Preserves binding |

### Published Examples

**Excellent Humanization (>75% OASis)**:
- Adalimumab (anti-TNF, clinical standard)
- Pembrolizumab (anti-PD-1, Merck)
- Atezolizumab (anti-PD-L1, Roche)

**Poor Humanization (<60% OASis)**:
- Mouse antibodies (0-20%)
- Chimeric antibodies (30-50%)
- Early humanized designs (50-65%)

---

## Interpreting Results

### Scenario 1: Design Screening

You have 100 designed VH sequences.

```
Humanness Score Distribution:
  >75%: 25 designs → ✓ High priority for synthesis
  70-75%: 35 designs → ~ Consider if binding is OK
  60-70%: 30 designs → ⚠ May need optimization
  <60%: 10 designs → ❌ Skip or re-design
```

**Decision**: Synthesize top 25-40, do binding assays, select best.

---

### Scenario 2: Humanization Validation

You've applied IMGT-based humanization.

**Before**: 55% OASis Identity
**After**: 72% OASis Identity
**Improvement**: +17%

**Interpretation**: Successful humanization. Expect lower immunogenicity in preclinical models.

---

### Scenario 3: CDR Grafting Assessment

You're comparing different CDR donor sources:

```
Donor A: 68% OASis, binding = 1000 nM
Donor B: 65% OASis, binding = 50 nM
Donor C: 62% OASis, binding = 10 nM
```

**Trade-off**: Binding affinity vs humanness. Choose based on therapeutic target (affinity-critical vs humanness-critical).

---

## Limitations & Caveats

### What OASis DOES NOT Measure

❌ **Binding affinity** (that's experimental)
❌ **Actual immunogenicity** (needs animal studies)
❌ **T-cell epitopes** (HLA-specific)
❌ **Protein stability** (biophysics)
❌ **Pharmacokinetics** (in vivo)

**OASis is a PREDICTION**, not ground truth. Always validate experimentally.

### When OASis Scores Are Misleading

1. **Rare legitimate sequence**: Humanness appears low but is naturally human
2. **Novel CDR combinations**: May have low score but excellent binding
3. **Non-IgG isotypes**: Database may be IgG-biased
4. **Light chains**: LS human databases less comprehensive than VH

---

## Peptide Fragmentation Deep Dive

### 9-mer Windows (Default)

**Example VH sequence:**
```
Position: 1234567890123456789...
Sequence: EVQLVESGG GLVQPGGSLR...
Peptides: [EVQLVESGG] [VQLVESGG] [QLVESGG] ...
```

**Why 9 amino acids?**
- Long enough to be specific
- Short enough to be common in nature
- Optimal for OASis algorithm

**Total peptides in ~120 AA VH:**
- Window size = 9
- Total peptides = 120 - 9 + 1 = **112 peptides**

---

## Output File Interpretation

### Excel Columns

```
ID                    | input_spec_29
Rank                  | 1
Sequence_Length       | 121
Humanness_Score       | 71.43%  ← PRIMARY METRIC
OASis_Percentile      | 0.73
Germline_Content_%    | 82.5%
VH_Germline_Before    | IGHV1-69*01
VH_Germline_After     | IGHV1-2*02
Humanizing_Mutations  | 14
```

---

## Decision Framework

### Choosing Candidates for Synthesis

**Cutoff by Application**:

| Application | Min OASis | Rationale |
|-------------|-----------|-----------|
| Preclinical | 55% | Basic humanization, mice immune |
| IND-enabling | 65% | GLP toxicology studies |
| Phase 1 | 70% | First humans, low immunogenicity |
| Phase 2+ | >72% | Commercial standard |

---

## See Also

- **BioPhiSkill documentation**: Core implementation
- **IMGT Numbering**: Required for CDR definition
- **OASis paper**: https://doi.org/10.1038/s41598-021-95505-6
