"""
Hierarchy Builder

Builds multi-level segment hierarchy for cascade allocation.

Copyright (c) 2024 Samplit Technologies
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


@dataclass
class SegmentNode:
    """
    Node in segment hierarchy tree
    
    Example:
        Global (root)
        ├─ country:US
        │  ├─ device:mobile
        │  │  ├─ source:instagram
        │  │  └─ source:google
        │  └─ device:desktop
        └─ country:UK
    """
    level: int
    feature_name: str
    feature_value: str
    segment_key: str
    samples: int = 0
    conversions: int = 0
    conversion_rate: float = 0.0
    
    # Tree structure
    parent: Optional['SegmentNode'] = None
    children: List['SegmentNode'] = field(default_factory=list)
    
    # Metadata
    is_leaf: bool = False
    depth: int = 0
    
    def add_child(self, child: 'SegmentNode'):
        """Add child node"""
        child.parent = self
        child.depth = self.depth + 1
        self.children.append(child)
    
    def get_path(self) -> List[str]:
        """Get path from root to this node"""
        path = []
        node = self
        while node.parent is not None:
            path.append(f"{node.feature_name}:{node.feature_value}")
            node = node.parent
        return list(reversed(path))
    
    def get_ancestors(self) -> List['SegmentNode']:
        """Get all ancestor nodes"""
        ancestors = []
        node = self.parent
        while node is not None:
            ancestors.append(node)
            node = node.parent
        return ancestors


class HierarchyBuilder:
    """
    Builds hierarchical segment structure
    
    Creates multi-level segmentation tree from context features.
    
    Hierarchy Levels (example):
        Level 0: Global (all users)
        Level 1: Geographic (country)
        Level 2: Device (mobile, tablet, desktop)
        Level 3: Traffic Source (google, facebook, etc)
        Level 4: Temporal (hour, day_of_week)
    
    Configuration:
        hierarchy_levels: List of feature names in order
        min_samples_per_level: Min samples needed to create child nodes
        max_depth: Maximum tree depth
        prune_ineffective: Remove nodes that don't improve performance
    
    Example:
        >>> builder = HierarchyBuilder(db_pool, {
        ...     'hierarchy_levels': ['country', 'device', 'source'],
        ...     'min_samples_per_level': [1000, 500, 200],
        ...     'max_depth': 3
        ... })
        >>> 
        >>> tree = await builder.build_hierarchy(experiment_id)
        >>> 
        >>> # Navigate tree
        >>> root = tree
        >>> us_node = root.children[0]  # country:US
        >>> mobile_node = us_node.children[0]  # device:mobile
    """
    
    def __init__(self, db_pool, config: Optional[Dict[str, Any]] = None):
        self.db = db_pool
        self.config = config or {}
        
        # Configuration
        self.hierarchy_levels = self.config.get('hierarchy_levels', ['country', 'device', 'source'])
        self.min_samples_per_level = self.config.get('min_samples_per_level', [1000, 500, 200])
        self.max_depth = self.config.get('max_depth', 3)
        self.prune_ineffective = self.config.get('prune_ineffective', True)
        
        logger.info(
            f"Initialized HierarchyBuilder: "
            f"levels={self.hierarchy_levels}, "
            f"max_depth={self.max_depth}"
        )
    
    # ========================================================================
    # MAIN BUILD
    # ========================================================================
    
    async def build_hierarchy(
        self,
        experiment_id: UUID
    ) -> SegmentNode:
        """
        Build complete hierarchy tree
        
        Process:
        1. Create root node (global)
        2. For each level in hierarchy:
           - Fetch segments at this level
           - Create child nodes
           - Recurse to next level
        3. Prune ineffective nodes
        4. Calculate statistics
        
        Args:
            experiment_id: Experiment UUID
        
        Returns:
            Root node of hierarchy tree
        """
        logger.info(f"Building hierarchy for experiment {experiment_id}")
        
        # ─────────────────────────────────────────────────────────────
        # Create root node (global)
        # ─────────────────────────────────────────────────────────────
        global_stats = await self._get_global_stats(experiment_id)
        
        root = SegmentNode(
            level=0,
            feature_name='global',
            feature_value='all',
            segment_key='global',
            samples=global_stats['samples'],
            conversions=global_stats['conversions'],
            conversion_rate=global_stats['conversion_rate'],
            depth=0
        )
        
        # ─────────────────────────────────────────────────────────────
        # Build tree recursively
        # ─────────────────────────────────────────────────────────────
        await self._build_level(experiment_id, root, level_idx=0)
        
        # ─────────────────────────────────────────────────────────────
        # Prune ineffective nodes
        # ─────────────────────────────────────────────────────────────
        if self.prune_ineffective:
            self._prune_tree(root)
        
        # ─────────────────────────────────────────────────────────────
        # Calculate tree statistics
        # ─────────────────────────────────────────────────────────────
        stats = self._calculate_tree_stats(root)
        logger.info(
            f"Built hierarchy: {stats['total_nodes']} nodes, "
            f"{stats['leaf_nodes']} leaves, "
            f"max_depth={stats['max_depth']}"
        )
        
        return root
    
    async def _build_level(
        self,
        experiment_id: UUID,
        parent_node: SegmentNode,
        level_idx: int
    ):
        """
        Recursively build tree level
        
        Args:
            experiment_id: Experiment UUID
            parent_node: Parent node to attach children to
            level_idx: Current level index in hierarchy_levels
        """
        # Check depth limit
        if level_idx >= len(self.hierarchy_levels):
            parent_node.is_leaf = True
            return
        
        if parent_node.depth >= self.max_depth:
            parent_node.is_leaf = True
            return
        
        # Get feature for this level
        feature_name = self.hierarchy_levels[level_idx]
        
        # Get min samples threshold for this level
        min_samples = (
            self.min_samples_per_level[level_idx]
            if level_idx < len(self.min_samples_per_level)
            else 100
        )
        
        # Check if parent has enough samples to split
        if parent_node.samples < min_samples:
            parent_node.is_leaf = True
            return
        
        # ─────────────────────────────────────────────────────────────
        # Fetch child segments
        # ─────────────────────────────────────────────────────────────
        children_data = await self._fetch_child_segments(
            experiment_id,
            parent_segment_key=parent_node.segment_key,
            feature_name=feature_name,
            min_samples=min_samples
        )
        
        if not children_data:
            parent_node.is_leaf = True
            return
        
        # ─────────────────────────────────────────────────────────────
        # Create child nodes
        # ─────────────────────────────────────────────────────────────
        for child_data in children_data:
            child_node = SegmentNode(
                level=level_idx + 1,
                feature_name=feature_name,
                feature_value=child_data['feature_value'],
                segment_key=child_data['segment_key'],
                samples=child_data['samples'],
                conversions=child_data['conversions'],
                conversion_rate=child_data['conversion_rate']
            )
            
            parent_node.add_child(child_node)
            
            # Recurse to next level
            await self._build_level(experiment_id, child_node, level_idx + 1)
        
        # Mark as leaf if no children were created
        if not parent_node.children:
            parent_node.is_leaf = True
    
    async def _fetch_child_segments(
        self,
        experiment_id: UUID,
        parent_segment_key: str,
        feature_name: str,
        min_samples: int
    ) -> List[Dict[str, Any]]:
        """
        Fetch child segments for a parent node
        
        Returns segments that:
        - Start with parent_segment_key (or are global if parent is root)
        - Add one more feature (feature_name)
        - Have at least min_samples
        """
        async with self.db.acquire() as conn:
            if parent_segment_key == 'global':
                # Root level - get all segments with just this feature
                rows = await conn.fetch("""
                    SELECT 
                        segment_key,
                        context_features,
                        total_visits as samples,
                        total_conversions as conversions,
                        CASE 
                            WHEN total_visits > 0
                            THEN total_conversions::FLOAT / total_visits
                            ELSE 0.0
                        END as conversion_rate
                    FROM context_segments
                    WHERE experiment_id = $1
                      AND total_visits >= $2
                      AND context_features ? $3
                      AND jsonb_array_length(jsonb_object_keys(context_features)) = 1
                    ORDER BY total_visits DESC
                """, experiment_id, min_samples, feature_name)
            else:
                # Non-root level - get segments that extend parent
                rows = await conn.fetch("""
                    SELECT 
                        segment_key,
                        context_features,
                        total_visits as samples,
                        total_conversions as conversions,
                        CASE 
                            WHEN total_visits > 0
                            THEN total_conversions::FLOAT / total_visits
                            ELSE 0.0
                        END as conversion_rate
                    FROM context_segments
                    WHERE experiment_id = $1
                      AND total_visits >= $2
                      AND context_features ? $3
                      AND segment_key LIKE $4 || '%'
                    ORDER BY total_visits DESC
                """, experiment_id, min_samples, feature_name, parent_segment_key)
        
        children = []
        for row in rows:
            feature_value = row['context_features'].get(feature_name)
            if feature_value:
                children.append({
                    'segment_key': row['segment_key'],
                    'feature_value': feature_value,
                    'samples': row['samples'],
                    'conversions': row['conversions'],
                    'conversion_rate': row['conversion_rate']
                })
        
        return children
    
    async def _get_global_stats(self, experiment_id: UUID) -> Dict[str, Any]:
        """Get global statistics for experiment"""
        async with self.db.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT 
                    SUM(total_visitors) as samples,
                    SUM(total_conversions) as conversions
                FROM element_variants
                WHERE experiment_id = $1
                  AND status = 'active'
            """, experiment_id)
        
        samples = row['samples'] or 0
        conversions = row['conversions'] or 0
        
        return {
            'samples': samples,
            'conversions': conversions,
            'conversion_rate': conversions / samples if samples > 0 else 0.0
        }
    
    # ========================================================================
    # TREE OPERATIONS
    # ========================================================================
    
    def _prune_tree(self, root: SegmentNode):
        """
        Prune nodes that don't improve performance
        
        Removes nodes where:
        - Child performance is not significantly different from parent
        - Child has too few samples to be reliable
        """
        self._prune_node(root)
    
    def _prune_node(self, node: SegmentNode):
        """Recursively prune node and children"""
        if node.is_leaf:
            return
        
        # Prune children first (bottom-up)
        for child in list(node.children):  # Copy list to allow modification
            self._prune_node(child)
        
        # Check if children should be pruned
        children_to_remove = []
        
        for child in node.children:
            # Prune if child doesn't improve over parent
            if not self._is_improvement(child, node):
                children_to_remove.append(child)
        
        # Remove pruned children
        for child in children_to_remove:
            node.children.remove(child)
            logger.debug(f"Pruned node: {child.segment_key}")
        
        # Mark as leaf if no children remain
        if not node.children:
            node.is_leaf = True
    
    def _is_improvement(
        self,
        child: SegmentNode,
        parent: SegmentNode,
        threshold: float = 0.05
    ) -> bool:
        """
        Check if child represents significant improvement over parent
        
        Args:
            child: Child node
            parent: Parent node
            threshold: Minimum improvement threshold (5% default)
        
        Returns:
            True if child is significantly different
        """
        # Need minimum samples
        if child.samples < 50:
            return False
        
        # Calculate improvement
        improvement = abs(child.conversion_rate - parent.conversion_rate)
        relative_improvement = (
            improvement / parent.conversion_rate
            if parent.conversion_rate > 0
            else 0.0
        )
        
        return relative_improvement >= threshold
    
    def _calculate_tree_stats(self, root: SegmentNode) -> Dict[str, Any]:
        """Calculate tree statistics"""
        total_nodes = 0
        leaf_nodes = 0
        max_depth = 0
        
        def traverse(node: SegmentNode):
            nonlocal total_nodes, leaf_nodes, max_depth
            
            total_nodes += 1
            if node.is_leaf:
                leaf_nodes += 1
            max_depth = max(max_depth, node.depth)
            
            for child in node.children:
                traverse(child)
        
        traverse(root)
        
        return {
            'total_nodes': total_nodes,
            'leaf_nodes': leaf_nodes,
            'max_depth': max_depth,
            'branching_factor': (total_nodes - 1) / max(max_depth, 1)
        }
    
    # ========================================================================
    # TREE SEARCH
    # ========================================================================
    
    def find_node(
        self,
        root: SegmentNode,
        context: Dict[str, Any]
    ) -> Optional[SegmentNode]:
        """
        Find most specific node matching context
        
        Traverses tree following context features to find
        deepest matching node.
        
        Args:
            root: Root node
            context: User context
        
        Returns:
            Most specific matching node
        """
        current = root
        
        for level_idx, feature_name in enumerate(self.hierarchy_levels):
            if feature_name not in context:
                break
            
            feature_value = context[feature_name]
            
            # Find matching child
            matching_child = None
            for child in current.children:
                if child.feature_value == feature_value:
                    matching_child = child
                    break
            
            if matching_child is None:
                # No matching child - return current
                break
            
            current = matching_child
        
        return current
    
    def get_cascade_path(
        self,
        root: SegmentNode,
        context: Dict[str, Any]
    ) -> List[SegmentNode]:
        """
        Get cascade path for context
        
        Returns path from most specific to root (fallback order).
        
        Example:
            [
                device:mobile|source:instagram|country:US,  # Most specific
                device:mobile|country:US,                   # Fallback 1
                country:US,                                 # Fallback 2
                global                                      # Fallback 3
            ]
        """
        # Find most specific node
        specific_node = self.find_node(root, context)
        
        # Build path to root
        path = [specific_node]
        current = specific_node.parent
        
        while current is not None:
            path.append(current)
            current = current.parent
        
        return path
