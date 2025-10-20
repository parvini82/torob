"""Example usage of the evaluation modules.

This example demonstrates how to use the integrated evaluation system
for both toy sample quality assessment and entity extraction evaluation.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from evaluation import ModelEvaluator, EvaluationConfig, EntityTagEvaluator
from data import DataConfig, DataDownloader, ToySampleGenerator


def example_toy_sample_evaluation():
    """Example of evaluating toy sample quality."""
    print("=" * 60)
    print("TOY SAMPLE QUALITY EVALUATION EXAMPLE")
    print("=" * 60)
    
    # Initialize configurations
    data_config = DataConfig()
    eval_config = EvaluationConfig()
    
    # Initialize evaluator
    evaluator = ModelEvaluator(eval_config)
    
    # Example toy sample (in practice, this would come from ToySampleGenerator)
    example_products = [
        {
            "title": "کت شلوار مردانه آبان طرح ساده",
            "group": "مردانه",
            "product": "کت شلوار",
            "image_url": "https://example.com/image1.jpg",
            "entities": [
                {"name": "جنس", "values": ["لنین"]},
                {"name": "نوع کلی", "values": ["کت شلوار آبان"]},
                {"name": "رنگ", "values": ["آبی"]}
            ],
            "quality_score": 85
        },
        {
            "title": "تیشرت زنانه نخی",
            "group": "زنانه",
            "product": "تیشرت",
            "image_url": "https://example.com/image2.jpg",
            "entities": [
                {"name": "جنس", "values": ["نخ"]},
                {"name": "نوع کلی", "values": ["تیشرت"]}
            ],
            "quality_score": 78
        },
        {
            "title": "کفش ورزشی پسرانه",
            "group": "پسرانه",
            "product": "کفش",
            "image_url": "https://example.com/image3.jpg",
            "entities": [
                {"name": "نوع کلی", "values": ["کفش ورزشی"]},
                {"name": "رنگ", "values": ["مشکی", "سفید"]}
            ],
            "quality_score": 92
        }
    ]
    
    # Run evaluation
    results = evaluator.evaluate_toy_sample_quality(example_products, "example_sample")
    
    # Print key results
    print(f"\nSample Quality Results:")
    print(f"Overall Quality Score: {results['overall_quality_score']:.3f}")
    print(f"Sample Size: {results['sample_size']}")
    print(f"Entity Coverage Rate: {results['entity_coverage']['entity_coverage_rate']:.1f}%")
    print(f"Image Validity Rate: {results['image_validity']['url_validity_rate']:.1f}%")
    print(f"Group Diversity Score: {results['diversity_metrics']['group_diversity']:.3f}")
    
    return results


def example_entity_extraction_evaluation():
    """Example of evaluating entity extraction performance."""
    print("\n" + "=" * 60)
    print("ENTITY EXTRACTION EVALUATION EXAMPLE")
    print("=" * 60)
    
    # Initialize evaluator
    eval_config = EvaluationConfig()
    evaluator = ModelEvaluator(eval_config)
    
    # Example predictions and ground truths
    predictions = [
        [  # Sample 1 predictions
            {"name": "جنس", "values": ["لنین"]},
            {"name": "نوع کلی", "values": ["کت شلوار آبان"]}
        ],
        [  # Sample 2 predictions
            {"name": "جنس", "values": ["نخ پنبه"]},
            {"name": "رنگ", "values": ["قرمز"]}
        ],
        [  # Sample 3 predictions
            {"name": "نوع کلی", "values": ["کفش ورزشی"]},
            {"name": "رنگ", "values": ["مشکی"]}
        ]
    ]
    
    ground_truths = [
        [  # Sample 1 ground truth
            {"name": "جنس", "values": ["لنین"]},
            {"name": "نوع کلی", "values": ["کت شلوار آبان"]},
            {"name": "رنگ", "values": ["آبی"]}
        ],
        [  # Sample 2 ground truth
            {"name": "جنس", "values": ["نخ"]},
            {"name": "رنگ", "values": ["قرمز"]}
        ],
        [  # Sample 3 ground truth
            {"name": "نوع کلی", "values": ["کفش ورزشی"]},
            {"name": "رنگ", "values": ["مشکی", "سفید"]}
        ]
    ]
    
    # Run evaluation
    results = evaluator.evaluate_entity_extraction(predictions, ground_truths, "example_entities")
    
    # Print key results
    print(f"\nEntity Extraction Results:")
    macro_avg = results['macro_averages']
    print(f"Exact Match Rate: {macro_avg['exact_match']:.3f}")
    print(f"Partial Match F1: {macro_avg['partial_match_f1']:.3f}")
    print(f"Semantic F1: {macro_avg['semantic_f1']:.3f}")
    print(f"80% Accuracy: {macro_avg['eighty_percent_accuracy']:.3f}")
    print(f"Valid Samples: {macro_avg['num_valid_samples']}/{len(predictions)}")
    
    # Print per-attribute performance
    if 'attribute_summary' in results:
        print("\nPer-Attribute Performance:")
        for attr_name, metrics in results['attribute_summary'].items():
            print(f"  {attr_name}: F1={metrics['mean_f1']:.3f}, Precision={metrics['mean_precision']:.3f}, Recall={metrics['mean_recall']:.3f}")
    
    return results


def example_comprehensive_evaluation():
    """Example of running comprehensive evaluation."""
    print("\n" + "=" * 60)
    print("COMPREHENSIVE EVALUATION EXAMPLE")
    print("=" * 60)
    
    # Initialize evaluator
    eval_config = EvaluationConfig()
    evaluator = ModelEvaluator(eval_config)
    
    # Prepare sample data (in practice, load from actual sources)
    toy_sample = [
        {
            "title": "محصول نمونه ۱",
            "group": "مردانه",
            "product": "پیراهن",
            "image_url": "https://example.com/image1.jpg",
            "entities": [{"name": "رنگ", "values": ["آبی"]}],
            "quality_score": 80
        },
        {
            "title": "محصول نمونه ۲",
            "group": "زنانه",
            "product": "مانتو",
            "image_url": "https://example.com/image2.jpg",
            "entities": [{"name": "جنس", "values": ["پارچه"]}],
            "quality_score": 75
        }
    ]
    
    entity_predictions = [
        [{"name": "رنگ", "values": ["آبی"]}],
        [{"name": "جنس", "values": ["پارچه"]}]
    ]
    
    entity_ground_truths = [
        [{"name": "رنگ", "values": ["آبی"]}],
        [{"name": "جنس", "values": ["پارچه"]}]
    ]
    
    # Run comprehensive evaluation
    results = evaluator.run_comprehensive_evaluation(
        toy_sample=toy_sample,
        entity_predictions=entity_predictions,
        entity_ground_truths=entity_ground_truths,
        session_name="comprehensive_example"
    )
    
    # Generate report
    report_path = evaluator.generate_evaluation_report(results)
    print(f"\nGenerated evaluation report: {report_path}")
    
    return results


def example_single_entity_evaluation():
    """Example of evaluating a single entity sample."""
    print("\n" + "=" * 60)
    print("SINGLE ENTITY EVALUATION EXAMPLE")
    print("=" * 60)
    
    # Initialize entity evaluator directly
    eval_config = EvaluationConfig()
    entity_evaluator = EntityTagEvaluator(eval_config)
    
    # Example single sample
    predicted_entities = [
        {"name": "جنس", "values": ["لنین"]},
        {"name": "نوع کلی", "values": ["کت شلوار آبان"]}
    ]
    
    true_entities = [
        {"name": "جنس", "values": ["لنین"]},
        {"name": "نوع کلی", "values": ["کت شلوار آبان"]}
    ]
    
    # Evaluate single sample
    single_result = entity_evaluator.evaluate_single_sample(predicted_entities, true_entities)
    
    print("Single Sample Evaluation:")
    print(f"Exact Match: {single_result['exact_match']}")
    print(f"Partial Match F1: {single_result['partial_match']['f1']:.3f}")
    print(f"Semantic F1: {single_result['semantic_similarity']['semantic_f1']:.3f}")
    print(f"80% Accuracy: {single_result['eighty_percent_accuracy']}")
    
    return single_result


if __name__ == "__main__":
    print("Running Evaluation Examples...\n")
    
    try:
        # Run individual examples
        toy_results = example_toy_sample_evaluation()
        entity_results = example_entity_extraction_evaluation()
        single_results = example_single_entity_evaluation()
        comprehensive_results = example_comprehensive_evaluation()
        
        print("\n" + "=" * 60)
        print("ALL EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error running examples: {e}")
        import traceback
        traceback.print_exc()
