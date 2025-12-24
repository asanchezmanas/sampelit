"""
Cluster Validation Module
Professional metrics for evaluating clustering quality.

Copyright (c) 2024 Samplit Technologies
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from sklearn.metrics import (
    silhouette_score, 
    silhouette_samples,
    davies_bouldin_score,
    calinski_harabasz_score
)
from scipy.spatial.distance import cdist
import logging

logger = logging.getLogger(__name__)


@dataclass
class ClusteringMetrics:
    """
    Comprehensive clustering quality metrics
    
    Attributes:
        silhouette_score: Overall silhouette score [-1, 1]
            - Values near 1: Well-separated clusters
            - Values near 0: Overlapping clusters
            - Values near -1: Points assigned to wrong clusters
            
        silhouette_per_cluster: Silhouette score per cluster
        
        davies_bouldin_score: Davies-Bouldin index [0, ∞)
            - Lower is better
            - 0 = perfect separation
            
        calinski_harabasz_score: Variance ratio [0, ∞)
            - Higher is better
            - Measures between-cluster vs within-cluster variance
            
        inertia: Within-cluster sum of squares
            - Lower is better (but watch for overfitting)
            
        cluster_sizes: Number of samples per cluster
        
        cluster_separations: Distance between cluster centroids
        
        cluster_compactness: Within-cluster variance per cluster
    """
    silhouette_score: float
    silhouette_per_cluster: Dict[int, float]
    davies_bouldin_score: float
    calinski_harabasz_score: float
    inertia: float
    cluster_sizes: Dict[int, int]
    cluster_separations: Dict[Tuple[int, int], float]
    cluster_compactness: Dict[int, float]
    
    def is_good_quality(self) -> bool:
        """
        Quick quality check based on thresholds
        
        Returns:
            True if clustering meets minimum quality standards
        """
        return (
            self.silhouette_score >= 0.3 and  # Reasonable separation
            self.davies_bouldin_score <= 2.0 and  # Not too overlapping
            min(self.cluster_sizes.values()) >= 10  # No tiny clusters
        )
    
    def get_quality_grade(self) -> str:
        """
        Categorize clustering quality
        
        Returns:
            'excellent', 'good', 'fair', 'poor', or 'bad'
        """
        if self.silhouette_score >= 0.7:
            return 'excellent'
        elif self.silhouette_score >= 0.5:
            return 'good'
        elif self.silhouette_score >= 0.3:
            return 'fair'
        elif self.silhouette_score >= 0.2:
            return 'poor'
        else:
            return 'bad'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'silhouette_score': float(self.silhouette_score),
            'silhouette_per_cluster': {
                int(k): float(v) for k, v in self.silhouette_per_cluster.items()
            },
            'davies_bouldin_score': float(self.davies_bouldin_score),
            'calinski_harabasz_score': float(self.calinski_harabasz_score),
            'inertia': float(self.inertia),
            'cluster_sizes': {
                int(k): int(v) for k, v in self.cluster_sizes.items()
            },
            'cluster_separations': {
                f"{k[0]}-{k[1]}": float(v) 
                for k, v in self.cluster_separations.items()
            },
            'cluster_compactness': {
                int(k): float(v) for k, v in self.cluster_compactness.items()
            },
            'quality_grade': self.get_quality_grade(),
            'is_good_quality': self.is_good_quality()
        }


class ClusterValidator:
    """
    Validates clustering quality using multiple metrics
    
    This class provides comprehensive evaluation of clustering results
    using industry-standard metrics from sklearn and custom heuristics.
    
    Example:
        >>> validator = ClusterValidator()
        >>> metrics = validator.evaluate(X, labels, centroids)
        >>> 
        >>> if metrics.is_good_quality():
        ...     print(f"✅ Good clustering: {metrics.silhouette_score:.3f}")
        ... else:
        ...     print(f"❌ Poor clustering: {metrics.get_quality_grade()}")
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ClusterValidator")
    
    # ========================================================================
    # MAIN EVALUATION
    # ========================================================================
    
    def evaluate(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        centroids: Optional[np.ndarray] = None
    ) -> ClusteringMetrics:
        """
        Comprehensive evaluation of clustering quality
        
        Args:
            X: Feature matrix (n_samples, n_features)
            labels: Cluster assignments (n_samples,)
            centroids: Cluster centers (n_clusters, n_features) - optional
            
        Returns:
            ClusteringMetrics with all quality measures
        """
        n_samples, n_features = X.shape
        n_clusters = len(np.unique(labels))
        
        self.logger.info(
            f"Evaluating clustering: {n_samples} samples, "
            f"{n_clusters} clusters, {n_features} features"
        )
        
        # ─────────────────────────────────────────────────────────────────
        # Silhouette Score (Primary metric)
        # ─────────────────────────────────────────────────────────────────
        try:
            silhouette_avg = silhouette_score(X, labels)
            silhouette_samples_vals = silhouette_samples(X, labels)
            
            # Per-cluster silhouette
            silhouette_per_cluster = {}
            for cluster_id in np.unique(labels):
                mask = labels == cluster_id
                cluster_silhouette = np.mean(silhouette_samples_vals[mask])
                silhouette_per_cluster[int(cluster_id)] = float(cluster_silhouette)
            
        except Exception as e:
            self.logger.error(f"Silhouette calculation failed: {e}")
            silhouette_avg = -1.0
            silhouette_per_cluster = {}
        
        # ─────────────────────────────────────────────────────────────────
        # Davies-Bouldin Index
        # ─────────────────────────────────────────────────────────────────
        try:
            db_score = davies_bouldin_score(X, labels)
        except Exception as e:
            self.logger.error(f"Davies-Bouldin calculation failed: {e}")
            db_score = float('inf')
        
        # ─────────────────────────────────────────────────────────────────
        # Calinski-Harabasz Index (Variance Ratio)
        # ─────────────────────────────────────────────────────────────────
        try:
            ch_score = calinski_harabasz_score(X, labels)
        except Exception as e:
            self.logger.error(f"Calinski-Harabasz calculation failed: {e}")
            ch_score = 0.0
        
        # ─────────────────────────────────────────────────────────────────
        # Inertia (Within-cluster sum of squares)
        # ─────────────────────────────────────────────────────────────────
        if centroids is not None:
            inertia = self._calculate_inertia(X, labels, centroids)
        else:
            # Compute centroids
            centroids = self._compute_centroids(X, labels)
            inertia = self._calculate_inertia(X, labels, centroids)
        
        # ─────────────────────────────────────────────────────────────────
        # Cluster Sizes
        # ─────────────────────────────────────────────────────────────────
        cluster_sizes = {}
        for cluster_id in np.unique(labels):
            cluster_sizes[int(cluster_id)] = int(np.sum(labels == cluster_id))
        
        # ─────────────────────────────────────────────────────────────────
        # Cluster Separations (distances between centroids)
        # ─────────────────────────────────────────────────────────────────
        cluster_separations = self._calculate_separations(centroids)
        
        # ─────────────────────────────────────────────────────────────────
        # Cluster Compactness (within-cluster variance)
        # ─────────────────────────────────────────────────────────────────
        cluster_compactness = self._calculate_compactness(X, labels, centroids)
        
        # ─────────────────────────────────────────────────────────────────
        # Build metrics object
        # ─────────────────────────────────────────────────────────────────
        metrics = ClusteringMetrics(
            silhouette_score=float(silhouette_avg),
            silhouette_per_cluster=silhouette_per_cluster,
            davies_bouldin_score=float(db_score),
            calinski_harabasz_score=float(ch_score),
            inertia=float(inertia),
            cluster_sizes=cluster_sizes,
            cluster_separations=cluster_separations,
            cluster_compactness=cluster_compactness
        )
        
        self.logger.info(
            f"Evaluation complete: Silhouette={silhouette_avg:.3f}, "
            f"Quality={metrics.get_quality_grade()}"
        )
        
        return metrics
    
    # ========================================================================
    # HELPER CALCULATIONS
    # ========================================================================
    
    def _compute_centroids(
        self, 
        X: np.ndarray, 
        labels: np.ndarray
    ) -> np.ndarray:
        """Compute cluster centroids"""
        n_clusters = len(np.unique(labels))
        n_features = X.shape[1]
        
        centroids = np.zeros((n_clusters, n_features))
        
        for cluster_id in range(n_clusters):
            mask = labels == cluster_id
            if np.sum(mask) > 0:
                centroids[cluster_id] = np.mean(X[mask], axis=0)
        
        return centroids
    
    def _calculate_inertia(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        centroids: np.ndarray
    ) -> float:
        """
        Calculate within-cluster sum of squares (inertia)
        
        Formula: Σ ||x_i - c_k||² for x_i in cluster k
        """
        inertia = 0.0
        
        for cluster_id in range(len(centroids)):
            mask = labels == cluster_id
            cluster_points = X[mask]
            
            if len(cluster_points) > 0:
                distances = np.sum(
                    (cluster_points - centroids[cluster_id]) ** 2,
                    axis=1
                )
                inertia += np.sum(distances)
        
        return float(inertia)
    
    def _calculate_separations(
        self,
        centroids: np.ndarray
    ) -> Dict[Tuple[int, int], float]:
        """
        Calculate pairwise distances between cluster centroids
        
        Returns:
            Dictionary mapping (cluster_i, cluster_j) -> distance
        """
        n_clusters = len(centroids)
        separations = {}
        
        for i in range(n_clusters):
            for j in range(i + 1, n_clusters):
                distance = float(np.linalg.norm(centroids[i] - centroids[j]))
                separations[(i, j)] = distance
        
        return separations
    
    def _calculate_compactness(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        centroids: np.ndarray
    ) -> Dict[int, float]:
        """
        Calculate within-cluster variance for each cluster
        
        Lower variance = more compact cluster
        """
        compactness = {}
        
        for cluster_id in range(len(centroids)):
            mask = labels == cluster_id
            cluster_points = X[mask]
            
            if len(cluster_points) > 1:
                # Variance = average squared distance to centroid
                distances = np.sum(
                    (cluster_points - centroids[cluster_id]) ** 2,
                    axis=1
                )
                variance = float(np.mean(distances))
            else:
                variance = 0.0
            
            compactness[int(cluster_id)] = variance
        
        return compactness
    
    # ========================================================================
    # QUALITY CHECKS
    # ========================================================================
    
    def check_cluster_balance(
        self,
        cluster_sizes: Dict[int, int],
        min_size: int = 10,
        max_imbalance_ratio: float = 10.0
    ) -> Dict[str, Any]:
        """
        Check if clusters are reasonably balanced
        
        Args:
            cluster_sizes: Dict mapping cluster_id -> size
            min_size: Minimum acceptable cluster size
            max_imbalance_ratio: Max ratio between largest and smallest cluster
            
        Returns:
            Dictionary with balance assessment
        """
        sizes = list(cluster_sizes.values())
        
        if not sizes:
            return {
                'balanced': False,
                'issues': ['No clusters found']
            }
        
        min_cluster_size = min(sizes)
        max_cluster_size = max(sizes)
        imbalance_ratio = max_cluster_size / max(min_cluster_size, 1)
        
        issues = []
        
        # Check minimum size
        if min_cluster_size < min_size:
            issues.append(
                f"Cluster too small: {min_cluster_size} < {min_size} samples"
            )
        
        # Check imbalance
        if imbalance_ratio > max_imbalance_ratio:
            issues.append(
                f"Clusters imbalanced: ratio {imbalance_ratio:.1f}x "
                f"(max allowed: {max_imbalance_ratio}x)"
            )
        
        return {
            'balanced': len(issues) == 0,
            'min_size': int(min_cluster_size),
            'max_size': int(max_cluster_size),
            'imbalance_ratio': float(imbalance_ratio),
            'issues': issues
        }
    
    def check_cluster_separation(
        self,
        cluster_separations: Dict[Tuple[int, int], float],
        min_separation: float = 0.5
    ) -> Dict[str, Any]:
        """
        Check if clusters are well-separated
        
        Args:
            cluster_separations: Dict of pairwise centroid distances
            min_separation: Minimum acceptable separation
            
        Returns:
            Dictionary with separation assessment
        """
        if not cluster_separations:
            return {
                'well_separated': False,
                'issues': ['No separation data available']
            }
        
        separations = list(cluster_separations.values())
        min_sep = min(separations)
        avg_sep = np.mean(separations)
        
        issues = []
        
        if min_sep < min_separation:
            issues.append(
                f"Clusters too close: min separation {min_sep:.3f} "
                f"< threshold {min_separation}"
            )
        
        return {
            'well_separated': len(issues) == 0,
            'min_separation': float(min_sep),
            'avg_separation': float(avg_sep),
            'max_separation': float(max(separations)),
            'issues': issues
        }
    
    def generate_report(self, metrics: ClusteringMetrics) -> str:
        """
        Generate human-readable quality report
        
        Args:
            metrics: ClusteringMetrics object
            
        Returns:
            Formatted string report
        """
        report = []
        report.append("=" * 80)
        report.append("CLUSTERING QUALITY REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Overall quality
        grade = metrics.get_quality_grade()
        grade_emoji = {
            'excellent': '🌟',
            'good': '✅',
            'fair': '⚠️',
            'poor': '❌',
            'bad': '💥'
        }.get(grade, '❓')
        
        report.append(f"Overall Quality: {grade_emoji} {grade.upper()}")
        report.append("")
        
        # Primary metrics
        report.append("Primary Metrics:")
        report.append(f"  Silhouette Score:        {metrics.silhouette_score:.3f}")
        report.append(f"    Interpretation: {'✅ Good' if metrics.silhouette_score >= 0.3 else '❌ Poor'}")
        report.append(f"  Davies-Bouldin Index:    {metrics.davies_bouldin_score:.3f}")
        report.append(f"    Interpretation: {'✅ Good' if metrics.davies_bouldin_score <= 2.0 else '❌ Poor'}")
        report.append(f"  Calinski-Harabasz Score: {metrics.calinski_harabasz_score:.1f}")
        report.append(f"  Inertia:                 {metrics.inertia:.1f}")
        report.append("")
        
        # Cluster sizes
        report.append("Cluster Sizes:")
        for cluster_id, size in sorted(metrics.cluster_sizes.items()):
            report.append(f"  Cluster {cluster_id}: {size:5d} samples")
        report.append("")
        
        # Per-cluster silhouette
        report.append("Per-Cluster Silhouette:")
        for cluster_id, score in sorted(metrics.silhouette_per_cluster.items()):
            emoji = '✅' if score >= 0.3 else ('⚠️' if score >= 0.2 else '❌')
            report.append(f"  Cluster {cluster_id}: {emoji} {score:.3f}")
        report.append("")
        
        # Balance check
        balance = self.check_cluster_balance(metrics.cluster_sizes)
        report.append("Balance Check:")
        if balance['balanced']:
            report.append("  ✅ Clusters are reasonably balanced")
        else:
            report.append("  ❌ Clusters are imbalanced:")
            for issue in balance['issues']:
                report.append(f"    - {issue}")
        report.append("")
        
        # Separation check
        separation = self.check_cluster_separation(metrics.cluster_separations)
        report.append("Separation Check:")
        if separation['well_separated']:
            report.append("  ✅ Clusters are well-separated")
        else:
            report.append("  ❌ Clusters overlap:")
            for issue in separation['issues']:
                report.append(f"    - {issue}")
        report.append("")
        
        # Recommendations
        report.append("Recommendations:")
        if metrics.is_good_quality():
            report.append("  ✅ Clustering quality is acceptable for production use")
        else:
            report.append("  ⚠️  Consider the following improvements:")
            if metrics.silhouette_score < 0.3:
                report.append("    - Try different number of clusters")
                report.append("    - Check feature engineering (normalization, encoding)")
            if metrics.davies_bouldin_score > 2.0:
                report.append("    - Clusters may be overlapping - try fewer clusters")
            if min(metrics.cluster_sizes.values()) < 10:
                report.append("    - Some clusters too small - reduce n_clusters")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


# ============================================================================
# UTILITIES
# ============================================================================

def compare_clusterings(
    metrics1: ClusteringMetrics,
    metrics2: ClusteringMetrics,
    names: Tuple[str, str] = ("Clustering 1", "Clustering 2")
) -> Dict[str, Any]:
    """
    Compare two clustering results
    
    Args:
        metrics1: First clustering metrics
        metrics2: Second clustering metrics
        names: Names for the two clusterings
        
    Returns:
        Dictionary with comparison results
    """
    comparison = {
        'winner': None,
        'metrics_comparison': {},
        'summary': []
    }
    
    # Compare each metric
    metrics_to_compare = [
        ('silhouette_score', 'higher'),
        ('davies_bouldin_score', 'lower'),
        ('calinski_harabasz_score', 'higher'),
    ]
    
    scores = {names[0]: 0, names[1]: 0}
    
    for metric_name, better_direction in metrics_to_compare:
        val1 = getattr(metrics1, metric_name)
        val2 = getattr(metrics2, metric_name)
        
        if better_direction == 'higher':
            winner = names[0] if val1 > val2 else names[1]
            better_val = max(val1, val2)
        else:
            winner = names[0] if val1 < val2 else names[1]
            better_val = min(val1, val2)
        
        scores[winner] += 1
        
        comparison['metrics_comparison'][metric_name] = {
            names[0]: float(val1),
            names[1]: float(val2),
            'winner': winner,
            'better_value': float(better_val)
        }
    
    # Overall winner
    comparison['winner'] = max(scores, key=scores.get)
    comparison['scores'] = scores
    
    # Summary
    comparison['summary'].append(
        f"{comparison['winner']} is better overall "
        f"({scores[comparison['winner']]}/{len(metrics_to_compare)} metrics)"
    )
    
    return comparison
