"""Comprehensive sample quality metrics for evaluation.

This module implements metrics to assess the quality and diversity of a
product sample (e.g., toy_sample) without relying on external models.
It focuses on structure, coverage, distribution, and basic data hygiene.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

from .config import EvaluationConfig

Product = Dict[str, Any]
MetricResult = Dict[str, Any]


class EvaluationMetrics:
    """Calculate quality and diversity metrics for product samples.

    This class provides a set of methods to evaluate a list of product dicts
    that follow the common structure used in this project:
      - title: str
      - group: str (e.g., "زنانه", "مردانه", ... or "نامشخص")
      - product: str (product type)
      - image_url: str
      - entities: List[Dict{name: str, values: List[str]}]
      - quality_score or quality_band (optional)
    """

    def __init__(self, config: EvaluationConfig):
        self.config = config

    # ------------------------------
    # Public API
    # ------------------------------
    def calculate_comprehensive_metrics(
        self, products: List[Product]
    ) -> Dict[str, Any]:
        """Compute a comprehensive set of metrics for a sample.

        Args:
            products: List of product dicts
        Returns:
            Dict with multiple sections and an overall quality score.
        """
        if not isinstance(products, list):
            raise ValueError("products must be a list of dicts")

        self.config.ensure_directories()

        group_dist = self.calculate_group_distribution(products)
        entity_cov = self.calculate_entity_coverage(products)
        title_stats = self.calculate_title_analysis(products)
        image_stats = self.calculate_image_validity(products)
        quality_dist = self.calculate_quality_distribution(products)
        diversity = self.calculate_sample_diversity(products)

        overall = self._calculate_overall_quality_score(
            {
                "entity_coverage_rate": entity_cov.get("entity_coverage_rate", 0.0),
                "url_validity_rate": image_stats.get("url_validity_rate", 0.0),
                "group_diversity": diversity.get("group_diversity", 0.0),
                "entity_diversity": diversity.get("entity_diversity", 0.0),
                "overall_diversity_score": diversity.get(
                    "overall_diversity_score", 0.0
                ),
            }
        )

        return {
            "sample_size": len(products),
            "group_distribution": group_dist,
            "entity_coverage": entity_cov,
            "title_analysis": title_stats,
            "image_validity": image_stats,
            "quality_distribution": quality_dist,
            "diversity_metrics": diversity,
            "overall_quality_score": overall,
        }

    # ------------------------------
    # Individual metric calculators
    # ------------------------------
    def calculate_group_distribution(self, products: List[Product]) -> MetricResult:
        groups: List[str] = []
        for p in products:
            g = (p.get("group") or "").strip()
            groups.append(g if g else "نامشخص")
        cnt = Counter(groups)
        total = max(len(products), 1)
        return {
            "total_products": len(products),
            "unique_groups": len(cnt),
            "group_counts": dict(cnt),
            "group_percentages": {k: round(v * 100 / total, 2) for k, v in cnt.items()},
            "most_common_group": cnt.most_common(1)[0] if cnt else None,
            "group_diversity_score": self._shannon_diversity_from_counter(cnt),
        }

    def calculate_entity_coverage(self, products: List[Product]) -> MetricResult:
        all_entities: List[str] = []
        entities_per_product: List[int] = []
        with_entities = 0
        for p in products:
            ents = p.get("entities") or []
            names = [
                e.get("name") for e in ents if isinstance(e, dict) and e.get("name")
            ]
            all_entities.extend(names)
            entities_per_product.append(len(names))
            if names:
                with_entities += 1
        total = max(len(products), 1)
        freq = Counter(all_entities)
        return {
            "total_products": len(products),
            "products_with_entities": with_entities,
            "entity_coverage_rate": round(with_entities * 100 / total, 2),
            "unique_entities": len(freq),
            "total_entity_occurrences": len(all_entities),
            "avg_entities_per_product": round(sum(entities_per_product) / total, 2),
            "entity_count_distribution": dict(Counter(entities_per_product)),
            "most_common_entities": freq.most_common(10),
            "entities_appearing_once": sum(1 for c in freq.values() if c == 1),
            "entity_diversity_score": self._shannon_diversity_from_counter(freq),
        }

    def calculate_title_analysis(self, products: List[Product]) -> MetricResult:
        lengths: List[int] = []
        empty = 0
        for p in products:
            title = (p.get("title") or "").strip()
            if not title:
                empty += 1
            lengths.append(len(title))
        total = max(len(products), 1)
        short = sum(1 for L in lengths if L < 20)
        medium = sum(1 for L in lengths if 30 <= L <= 50)
        long = sum(1 for L in lengths if L > 100)
        return {
            "total_products": len(products),
            "empty_titles": empty,
            "avg_title_length": round(sum(lengths) / total, 2),
            "min_title_length": min(lengths) if lengths else 0,
            "max_title_length": max(lengths) if lengths else 0,
            "short_titles_count": short,
            "medium_titles_count": medium,
            "long_titles_count": long,
            "short_titles_percentage": round(short * 100 / total, 2),
            "medium_titles_percentage": round(medium * 100 / total, 2),
            "long_titles_percentage": round(long * 100 / total, 2),
        }

    def calculate_image_validity(self, products: List[Product]) -> MetricResult:
        valid = 0
        unique = set()
        missing = 0
        exts: List[str] = []
        for p in products:
            url = (p.get("image_url") or "").strip()
            if not url:
                missing += 1
                continue
            if url.startswith(("http://", "https://")) or url.startswith("data:"):
                valid += 1
                unique.add(url.lower())
                ext = self._extract_ext(url)
                if ext:
                    exts.append(ext)
        ext_cnt = Counter(exts)
        total = max(len(products), 1)
        valid_rate = round(valid * 100 / total, 2)
        uniq_rate = round((len(unique) * 100 / valid), 2) if valid else 0.0
        return {
            "total_products": len(products),
            "valid_image_urls": valid,
            "unique_image_urls": len(unique),
            "missing_image_urls": missing,
            "url_validity_rate": valid_rate,
            "url_uniqueness_rate": uniq_rate,
            "duplicate_urls": max(valid - len(unique), 0),
            "image_extension_distribution": dict(ext_cnt),
            "most_common_extension": ext_cnt.most_common(1)[0] if ext_cnt else None,
        }

    def calculate_quality_distribution(self, products: List[Product]) -> MetricResult:
        bands: List[str] = []
        missing = 0
        for p in products:
            band = p.get("quality_band")
            if band:
                bands.append(str(band))
                continue
            score = p.get("quality_score")
            if isinstance(score, (int, float)):
                bands.append(self._score_to_band(score))
            else:
                bands.append("Unknown")
                missing += 1
        cnt = Counter(bands)
        total = max(len(products), 1)
        return {
            "total_products": len(products),
            "missing_quality_info": missing,
            "quality_distribution": dict(cnt),
            "quality_percentages": {
                k: round(v * 100 / total, 2) for k, v in cnt.items()
            },
            "weighted_quality_score": self._weighted_quality(cnt),
        }

    def calculate_sample_diversity(self, products: List[Product]) -> MetricResult:
        types = [str((p.get("product") or "").strip()) for p in products]
        type_cnt = Counter([t for t in types if t])
        group_div = self._shannon_diversity([p.get("group", "") for p in products])
        entity_div = self._entity_shannon(products)
        type_div = self._shannon_diversity(types)
        return {
            "product_type_diversity": type_div,
            "group_diversity": group_div,
            "entity_diversity": entity_div,
            "overall_diversity_score": round(
                (group_div + entity_div + type_div) / 3, 4
            ),
            "unique_product_types": len(type_cnt),
            "most_common_product_types": type_cnt.most_common(5),
        }

    # ------------------------------
    # Helpers
    # ------------------------------
    def _extract_ext(self, url: str) -> str:
        m = re.search(r"\.([a-zA-Z0-9]+)(?:\?|$)", url or "")
        return f".{m.group(1).lower()}" if m else ""

    def _score_to_band(self, score: float) -> str:
        if score >= 90:
            return "Excellent"
        if score >= 80:
            return "Good"
        if score >= 60:
            return "Fair"
        return "Poor"

    def _weighted_quality(self, cnt: Counter) -> float:
        total = sum(cnt.values()) or 1
        w = self.config.quality_weights
        weighted = sum(
            cnt.get(b, 0) * w.get(b, 1.0)
            for b in set(list(cnt.keys()) + list(w.keys()))
        )
        return round(weighted / total, self.config.precision_digits)

    def _shannon_diversity_from_counter(self, counter: Counter) -> float:
        if not counter:
            return 0.0
        total = sum(counter.values())
        if total == 0:
            return 0.0
        H = 0.0
        for c in counter.values():
            p = c / total
            if p > 0:
                H -= p * math.log(p)
        return round(H, self.config.precision_digits)

    def _shannon_diversity(self, items: List[str]) -> float:
        cnt = Counter([i for i in items if i])
        return self._shannon_diversity_from_counter(cnt)

    def _entity_shannon(self, products: List[Product]) -> float:
        all_names: List[str] = []
        for p in products:
            ents = p.get("entities") or []
            all_names.extend(
                [e.get("name") for e in ents if isinstance(e, dict) and e.get("name")]
            )
        return self._shannon_diversity(all_names)

    def _calculate_overall_quality_score(self, parts: Dict[str, float]) -> float:
        # weights similar to previous design
        weights = {
            "entity_coverage_rate": 0.25,
            "url_validity_rate": 0.20,
            "group_diversity": 0.20,
            "entity_diversity": 0.20,
            "overall_diversity_score": 0.15,
        }
        score = 0.0
        for k, w in weights.items():
            v = parts.get(k, 0.0)
            # Normalize percentages if needed
            norm = (v / 100.0) if v > 1 else v
            score += norm * w
        return round(score, self.config.precision_digits)

    # ------------------------------
    # Persistence helpers
    # ------------------------------
    def save_metrics_report(self, metrics: Dict[str, Any], output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, ensure_ascii=False, indent=2)
