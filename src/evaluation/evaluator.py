"""Main evaluation orchestrator for model performance assessment.

This module provides a high-level interface to coordinate different types
of evaluations including entity tagging, sample quality, and comprehensive
reporting.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from .config import EvaluationConfig
from .metrics import EvaluationMetrics
from .entity_evaluator import EntityTagEvaluator


class ModelEvaluator:
    """Main evaluation orchestrator for comprehensive model assessment.
    
    This class coordinates different evaluation components and provides
    a unified interface for running evaluations and generating reports.
    """
    
    def __init__(self, config: Optional[EvaluationConfig] = None):
        """Initialize evaluator with configuration.
        
        Args:
            config: EvaluationConfig instance, creates default if None
        """
        self.config = config or EvaluationConfig()
        self.config.ensure_directories()
        
        # Initialize evaluation components
        self.metrics_calculator = EvaluationMetrics(self.config)
        self.entity_evaluator = EntityTagEvaluator(self.config)
        
        # Track evaluation sessions
        self.current_session = None
    
    def start_evaluation_session(self, session_name: Optional[str] = None) -> str:
        """Start a new evaluation session.
        
        Args:
            session_name: Optional name for the session
            
        Returns:
            str: Session identifier
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if session_name:
            session_id = f"{session_name}_{timestamp}"
        else:
            session_id = f"evaluation_{timestamp}"
        
        self.current_session = {
            'session_id': session_id,
            'start_time': time.time(),
            'timestamp': timestamp,
            'results': {}
        }
        
        print(f"Started evaluation session: {session_id}")
        return session_id
    
    def evaluate_toy_sample_quality(self, products: List[Dict[str, Any]], 
                                   session_name: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate the quality and composition of a toy sample.
        
        Args:
            products: List of product dictionaries from toy sample
            session_name: Optional name for this evaluation
            
        Returns:
            Dict containing comprehensive sample quality metrics
        """
        if not self.current_session:
            self.start_evaluation_session(session_name)
        
        print(f"Evaluating toy sample quality for {len(products)} products...")
        
        # Calculate comprehensive metrics using the metrics calculator
        quality_results = self.metrics_calculator.calculate_comprehensive_metrics(products)
        
        # Store results in current session
        self.current_session['results']['sample_quality'] = quality_results
        
        return quality_results
    
    def evaluate_entity_extraction(self, predictions: List[List[Dict]], 
                                  ground_truths: List[List[Dict]],
                                  session_name: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate entity extraction performance.
        
        Args:
            predictions: List of predicted entity lists (one per sample)
            ground_truths: List of ground truth entity lists (one per sample)
            session_name: Optional name for this evaluation
            
        Returns:
            Dict containing entity extraction evaluation results
        """
        if not self.current_session:
            self.start_evaluation_session(session_name)
        
        print(f"Evaluating entity extraction for {len(predictions)} samples...")
        
        # Run comprehensive entity evaluation
        entity_results = self.entity_evaluator.evaluate_batch(predictions, ground_truths)
        
        # Calculate attribute-level summary
        attribute_summary = self.entity_evaluator.calculate_attribute_summary(entity_results)
        entity_results['attribute_summary'] = attribute_summary
        
        # Store results in current session
        self.current_session['results']['entity_extraction'] = entity_results
        
        return entity_results
    
    def evaluate_single_entity_sample(self, predicted_entities: List[Dict], 
                                     true_entities: List[Dict]) -> Dict[str, Any]:
        """Evaluate a single sample for entity extraction.
        
        Args:
            predicted_entities: List of predicted entity dictionaries
            true_entities: List of ground truth entity dictionaries
            
        Returns:
            Dict containing single sample evaluation metrics
        """
        return self.entity_evaluator.evaluate_single_sample(predicted_entities, true_entities)
    
    def run_comprehensive_evaluation(self, 
                                   toy_sample: Optional[List[Dict[str, Any]]] = None,
                                   entity_predictions: Optional[List[List[Dict]]] = None,
                                   entity_ground_truths: Optional[List[List[Dict]]] = None,
                                   session_name: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive evaluation including sample quality and entity extraction.
        
        Args:
            toy_sample: Optional toy sample for quality evaluation
            entity_predictions: Optional entity predictions for extraction evaluation
            entity_ground_truths: Optional entity ground truths for extraction evaluation
            session_name: Optional name for the evaluation session
            
        Returns:
            Dict containing all evaluation results
        """
        session_id = self.start_evaluation_session(session_name)
        results = {'session_id': session_id}
        
        # Evaluate toy sample quality if provided
        if toy_sample is not None:
            print("\n" + "=" * 60)
            print("EVALUATING TOY SAMPLE QUALITY")
            print("=" * 60)
            results['sample_quality'] = self.evaluate_toy_sample_quality(toy_sample)
        
        # Evaluate entity extraction if data provided
        if entity_predictions is not None and entity_ground_truths is not None:
            print("\n" + "=" * 60)
            print("EVALUATING ENTITY EXTRACTION")
            print("=" * 60)
            results['entity_extraction'] = self.evaluate_entity_extraction(
                entity_predictions, entity_ground_truths
            )
        
        # Finalize session
        self.current_session['end_time'] = time.time()
        self.current_session['duration'] = self.current_session['end_time'] - self.current_session['start_time']
        results['session_info'] = {
            'session_id': session_id,
            'duration_seconds': self.current_session['duration'],
            'timestamp': self.current_session['timestamp']
        }
        
        print(f"\nCompleted evaluation session: {session_id}")
        print(f"Duration: {self.current_session['duration']:.2f} seconds")
        
        return results
    
    def generate_evaluation_report(self, results: Dict[str, Any], 
                                  output_path: Optional[Path] = None,
                                  include_detailed: bool = None) -> Path:
        """Generate comprehensive evaluation report.
        
        Args:
            results: Evaluation results dictionary
            output_path: Optional path for report file
            include_detailed: Whether to include detailed breakdown
            
        Returns:
            Path: Path to generated report file
        """
        if output_path is None:
            session_id = results.get('session_id', 'unknown')
            output_path = self.config.reports_dir / f"evaluation_report_{session_id}.json"
        
        if include_detailed is None:
            include_detailed = self.config.include_detailed_breakdown
        
        # Prepare report data
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'evaluator_config': {
                    'similarity_threshold': self.config.similarity_threshold,
                    'precision_digits': self.config.precision_digits,
                    'include_detailed_breakdown': include_detailed
                }
            },
            'session_info': results.get('session_info', {}),
            'summary': self._generate_summary(results),
            'detailed_results': results if include_detailed else {}
        }
        
        # Save report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"Generated evaluation report: {output_path}")
        return output_path
    
    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate executive summary from evaluation results.
        
        Args:
            results: Complete evaluation results
            
        Returns:
            Dict: Summary statistics and key findings
        """
        summary = {}
        
        # Sample quality summary
        if 'sample_quality' in results:
            sq = results['sample_quality']
            summary['sample_quality'] = {
                'overall_quality_score': sq.get('overall_quality_score', 0.0),
                'sample_size': sq.get('sample_size', 0),
                'entity_coverage_rate': sq.get('entity_coverage', {}).get('entity_coverage_rate', 0.0),
                'image_validity_rate': sq.get('image_validity', {}).get('url_validity_rate', 0.0),
                'group_diversity_score': sq.get('diversity_metrics', {}).get('group_diversity', 0.0)
            }
        
        # Entity extraction summary
        if 'entity_extraction' in results:
            ee = results['entity_extraction']
            macro_avg = ee.get('macro_averages', {})
            summary['entity_extraction'] = {
                'exact_match_rate': macro_avg.get('exact_match', 0.0),
                'partial_match_f1': macro_avg.get('partial_match_f1', 0.0),
                'semantic_f1': macro_avg.get('semantic_f1', 0.0),
                'eighty_percent_accuracy': macro_avg.get('eighty_percent_accuracy', 0.0),
                'total_samples': ee.get('summary', {}).get('total_samples', 0),
                'success_rate': ee.get('summary', {}).get('success_rate', 0.0)
            }
            
            # Top performing attributes
            if 'attribute_summary' in ee:
                attr_summary = ee['attribute_summary']
                top_attrs = sorted(
                    attr_summary.items(), 
                    key=lambda x: x[1]['mean_f1'], 
                    reverse=True
                )[:5]
                summary['top_performing_attributes'] = {
                    attr: {'f1': metrics['mean_f1'], 'samples': metrics['num_samples']}
                    for attr, metrics in top_attrs
                }
        
        return summary
    
    def save_session_results(self, output_path: Optional[Path] = None) -> Path:
        """Save current session results to file.
        
        Args:
            output_path: Optional path for results file
            
        Returns:
            Path: Path to saved results file
        """
        if not self.current_session:
            raise ValueError("No active evaluation session to save")
        
        if output_path is None:
            session_id = self.current_session['session_id']
            output_path = self.config.results_dir / f"session_{session_id}.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_session, f, ensure_ascii=False, indent=2)
        
        print(f"Saved session results: {output_path}")
        return output_path
    
    def load_session_results(self, session_path: Path) -> Dict[str, Any]:
        """Load previous session results from file.
        
        Args:
            session_path: Path to session results file
            
        Returns:
            Dict: Loaded session results
        """
        with open(session_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        print(f"Loaded session: {session_data.get('session_id', 'unknown')}")
        return session_data
    
    def compare_sessions(self, session_paths: List[Path]) -> Dict[str, Any]:
        """Compare results across multiple evaluation sessions.
        
        Args:
            session_paths: List of paths to session result files
            
        Returns:
            Dict: Comparison analysis
        """
        sessions = []
        for path in session_paths:
            try:
                session = self.load_session_results(path)
                sessions.append(session)
            except Exception as e:
                print(f"Warning: Could not load session from {path}: {e}")
        
        if len(sessions) < 2:
            raise ValueError("Need at least 2 sessions to compare")
        
        # Extract key metrics for comparison
        comparison = {
            'sessions': [],
            'metric_comparison': {},
            'trends': {}
        }
        
        for session in sessions:
            session_id = session.get('session_id', 'unknown')
            results = session.get('results', {})
            
            session_summary = {'session_id': session_id}
            
            # Extract sample quality metrics if available
            if 'sample_quality' in results:
                sq = results['sample_quality']
                session_summary.update({
                    'overall_quality_score': sq.get('overall_quality_score', 0.0),
                    'entity_coverage_rate': sq.get('entity_coverage', {}).get('entity_coverage_rate', 0.0)
                })
            
            # Extract entity extraction metrics if available
            if 'entity_extraction' in results:
                ee = results['entity_extraction']
                macro_avg = ee.get('macro_averages', {})
                session_summary.update({
                    'exact_match': macro_avg.get('exact_match', 0.0),
                    'semantic_f1': macro_avg.get('semantic_f1', 0.0)
                })
            
            comparison['sessions'].append(session_summary)
        
        return comparison
