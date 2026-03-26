#!/usr/bin/env python3
"""
Humanness Evaluator - Main Implementation

Provides:
- evaluate_csv(): Batch evaluation of sequences from CSV
- evaluate_single(): Single sequence evaluation
- evaluate_batch(): Flexible batch processing with progress tracking
"""

import sys
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union
import traceback

# Try to import BioPhiSkill
try:
    from agent_api import evaluate_humanness, humanize_antibody_sequence
    BIOPHI_AVAILABLE = True
except ImportError:
    BIOPHI_AVAILABLE = False
    evaluate_humanness = None


class HumannessEvaluator:
    """Main class for humanness evaluation workflow"""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize evaluator
        
        Args:
            verbose: Print progress messages
        """
        self.verbose = verbose
        
        if not BIOPHI_AVAILABLE:
            raise ImportError(
                "BioPhiSkill not found. Install with:\n"
                "  git clone https://github.com/Shaperon-AIDEN/BioPhiSkill.git\n"
                "  cd BioPhiSkill && bash install.sh\n"
                "  conda activate biophi"
            )
    
    def _log(self, msg: str):
        """Print verbose message"""
        if self.verbose:
            print(msg, flush=True)
    
    def evaluate_single(
        self,
        vh_sequence: str,
        vl_sequence: Optional[str] = None,
        sequence_id: str = "",
        min_fraction_subjects: float = 0.1
    ) -> Dict:
        """
        Evaluate a single antibody sequence
        
        Args:
            vh_sequence: Heavy chain amino acid sequence
            vl_sequence: Light chain sequence (optional)
            sequence_id: Identifier for this sequence
            min_fraction_subjects: OASis threshold (default 0.1 = 10%)
        
        Returns:
            Dict with keys:
                - humanness_score: OASis Identity (%)
                - oasis_percentile: Percentile ranking
                - germline_content: % matching germline
                - mutations_count: # of humanizing mutations
                - germlines: {vh_before, vh_after, vl_before, vl_after}
                - summary: Human-readable summary
        """
        try:
            self._log(f"  Evaluating {sequence_id or 'sequence'}...")
            
            # Call BioPhiSkill
            result = evaluate_humanness(
                vh_seq=vh_sequence,
                vl_seq=vl_sequence,
                min_fraction_subjects=min_fraction_subjects,
                output_dir=None
            )
            
            # Extract key metrics
            return {
                "sequence_id": sequence_id,
                "humanness_score": result.get('oasis_identity', 0),
                "oasis_percentile": result.get('oasis_percentile', 0),
                "germline_content": result.get('germline_content', 0),
                "mutations_count": len(result.get('vh_mutations', [])),
                "germlines": result.get('germlines', {}),
                "summary": result.get('summary', ''),
                "success": True
            }
        
        except Exception as e:
            return {
                "sequence_id": sequence_id,
                "error": str(e),
                "success": False
            }
    
    def evaluate_batch(
        self,
        sequences: List[Dict],
        output_excel: Optional[str] = None,
        stop_on_error: bool = False
    ) -> pd.DataFrame:
        """
        Evaluate multiple sequences with progress tracking
        
        Args:
            sequences: List of dicts with 'sequence', 'sequence_id' keys
            output_excel: Save results to Excel file
            stop_on_error: Halt on first error vs skip and continue
        
        Returns:
            DataFrame with evaluation results
        """
        results = []
        total = len(sequences)
        
        self._log(f"\n{'='*60}")
        self._log(f"Processing {total} sequences...")
        self._log(f"{'='*60}\n")
        
        for idx, seq_dict in enumerate(sequences, 1):
            seq_id = seq_dict.get('sequence_id', f'seq_{idx}')
            vh = seq_dict.get('sequence', seq_dict.get('vh_sequence', ''))
            vl = seq_dict.get('vl_sequence', None)
            
            self._log(f"[{idx}/{total}] {seq_id}... ", end="", flush=True)
            
            try:
                result = self.evaluate_single(
                    vh_sequence=vh,
                    vl_sequence=vl,
                    sequence_id=seq_id
                )
                results.append(result)
                
                if result['success']:
                    score = result['humanness_score']
                    self._log(f"✓ Humanness={score:.1f}%")
                else:
                    self._log(f"❌ {result['error']}")
                    if stop_on_error:
                        raise Exception(result['error'])
            
            except Exception as e:
                self._log(f"❌ {str(e)}")
                results.append({
                    "sequence_id": seq_id,
                    "error": str(e),
                    "success": False
                })
                if stop_on_error:
                    raise
        
        # Convert to DataFrame
        df = pd.DataFrame(results)
        
        # Save if requested
        if output_excel and 'humanness_score' in df.columns:
            df.to_excel(output_excel, index=False)
            self._log(f"\n✅ Results saved to {output_excel}")
        
        # Print summary
        self._print_summary(df)
        
        return df
    
    def evaluate_csv(
        self,
        csv_path: str,
        output_excel: Optional[str] = None,
        vh_column: str = "designed_chain_sequence",
        id_column: str = "id",
        stop_on_error: bool = False
    ) -> pd.DataFrame:
        """
        Evaluate sequences from CSV file
        
        Args:
            csv_path: Path to CSV with sequence column
            output_excel: Output filename (auto-generated if None)
            vh_column: Column name with VH sequences
            id_column: Column name with sequence IDs
            stop_on_error: Halt on first error
        
        Returns:
            DataFrame with evaluation results
        """
        # Load CSV
        csv_file = Path(csv_path)
        if not csv_file.exists():
            raise FileNotFoundError(f"CSV not found: {csv_path}")
        
        df_input = pd.read_csv(csv_path)
        self._log(f"📊 Loaded {len(df_input)} sequences from {csv_file.name}")
        
        # Check columns exist
        if vh_column not in df_input.columns:
            raise ValueError(
                f"Column '{vh_column}' not found. Available: {df_input.columns.tolist()}"
            )
        
        # Build sequence list
        sequences = []
        for _, row in df_input.iterrows():
            seq_id = str(row.get(id_column, '')) if id_column in df_input.columns else ''
            sequences.append({
                'sequence_id': seq_id,
                'vh_sequence': row[vh_column],
                'rank': row.get('final_rank', row.get('rank', None))
            })
        
        # Evaluate
        results_df = self.evaluate_batch(
            sequences=sequences,
            output_excel=output_excel or f"{csv_file.stem}_humanness.xlsx",
            stop_on_error=stop_on_error
        )
        
        return results_df
    
    def _print_summary(self, df: pd.DataFrame):
        """Print summary statistics"""
        if 'humanness_score' not in df.columns:
            return
        
        successful = df[df['success'] == True] if 'success' in df.columns else df
        if len(successful) == 0:
            self._log("\n⚠️  No successful evaluations")
            return
        
        humanness = successful['humanness_score'].dropna()
        
        self._log("\n" + "="*60)
        self._log("📈 SUMMARY STATISTICS")
        self._log("="*60)
        self._log(f"Total sequences:  {len(df)}")
        self._log(f"Successful:       {len(successful)} ({100*len(successful)/len(df):.0f}%)")
        
        if len(humanness) > 0:
            self._log(f"\nHumanness Score (OASis Identity %):")
            self._log(f"  Mean:           {humanness.mean():.2f}%")
            self._log(f"  Median:         {humanness.median():.2f}%")
            self._log(f"  Std Dev:        {humanness.std():.2f}%")
            self._log(f"  Min:            {humanness.min():.2f}%")
            self._log(f"  Max:            {humanness.max():.2f}%")
            
            # Breakdown by quality
            excellent = len(humanness[humanness > 75])
            good = len(humanness[(humanness > 70) & (humanness <= 75)])
            fair = len(humanness[(humanness > 60) & (humanness <= 70)])
            poor = len(humanness[humanness <= 60])
            
            self._log(f"\nQuality Distribution:")
            self._log(f"  Excellent (>75%):  {excellent:3d} sequences")
            self._log(f"  Good     (70-75%): {good:3d} sequences")
            self._log(f"  Fair     (60-70%): {fair:3d} sequences")
            self._log(f"  Poor     (<60%):   {poor:3d} sequences")
        
        self._log("="*60 + "\n")


# Convenience functions for direct import
def evaluate_single(
    vh_sequence: str,
    vl_sequence: Optional[str] = None,
    sequence_id: str = ""
) -> Dict:
    """Quick single sequence evaluation"""
    evaluator = HumannessEvaluator()
    return evaluator.evaluate_single(
        vh_sequence=vh_sequence,
        vl_sequence=vl_sequence,
        sequence_id=sequence_id
    )


def evaluate_csv(
    csv_path: str,
    output_excel: Optional[str] = None,
    vh_column: str = "designed_chain_sequence"
) -> pd.DataFrame:
    """Quick CSV batch evaluation"""
    evaluator = HumannessEvaluator()
    return evaluator.evaluate_csv(
        csv_path=csv_path,
        output_excel=output_excel,
        vh_column=vh_column
    )


def evaluate_batch(
    sequences: List[Dict],
    output_excel: Optional[str] = None
) -> pd.DataFrame:
    """Quick batch evaluation from sequence list"""
    evaluator = HumannessEvaluator()
    return evaluator.evaluate_batch(
        sequences=sequences,
        output_excel=output_excel
    )


if __name__ == "__main__":
    # CLI usage
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Evaluate humanness scores for antibody sequences"
    )
    parser.add_argument(
        "csv_path",
        help="Path to CSV file with sequences"
    )
    parser.add_argument(
        "-o", "--output",
        help="Output Excel filename",
        default=None
    )
    parser.add_argument(
        "--vh-column",
        default="designed_chain_sequence",
        help="Column name with VH sequences"
    )
    
    args = parser.parse_args()
    
    try:
        evaluate_csv(
            csv_path=args.csv_path,
            output_excel=args.output,
            vh_column=args.vh_column
        )
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
