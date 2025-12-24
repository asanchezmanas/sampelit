"""
Tree Visualizer

Visualizes segment hierarchy tree.

Copyright (c) 2024 Samplit Technologies
"""

from typing import Dict, Any, List
import json
from .hierarchy_builder import SegmentNode


class TreeVisualizer:
    """
    Visualizes hierarchical segment tree
    
    Formats:
    - ASCII tree (terminal)
    - JSON (API)
    - HTML (web dashboard)
    - DOT (Graphviz)
    
    Example:
        >>> visualizer = TreeVisualizer()
        >>> 
        >>> print(visualizer.to_ascii(root))
        Global (100K visits, 5.0% CR)
        ├─ country:US (60K visits, 6.0% CR)
        │  ├─ device:mobile (35K visits, 7.5% CR)
        │  │  ├─ source:instagram (15K visits, 9.0% CR) ⭐
        │  │  └─ source:google (10K visits, 6.5% CR)
        │  └─ device:desktop (25K visits, 4.5% CR)
        └─ country:UK (20K visits, 4.0% CR)
    """
    
    def __init__(self):
        pass
    
    # ========================================================================
    # ASCII FORMAT
    # ========================================================================
    
    def to_ascii(
        self,
        root: SegmentNode,
        show_stats: bool = True,
        highlight_best: bool = True
    ) -> str:
        """
        Generate ASCII tree representation
        
        Args:
            root: Root node
            show_stats: Show samples and conversion rate
            highlight_best: Highlight best performing nodes
        
        Returns:
            ASCII tree string
        """
        lines = []
        
        # Find best CR for highlighting
        best_cr = 0.0
        if highlight_best:
            best_cr = self._find_best_cr(root)
        
        self._ascii_node(root, lines, prefix="", is_last=True, best_cr=best_cr, show_stats=show_stats)
        
        return "\n".join(lines)
    
    def _ascii_node(
        self,
        node: SegmentNode,
        lines: List[str],
        prefix: str,
        is_last: bool,
        best_cr: float,
        show_stats: bool
    ):
        """Recursively build ASCII tree"""
        # Node label
        if node.level == 0:
            label = "Global"
        else:
            label = f"{node.feature_name}:{node.feature_value}"
        
        # Stats
        if show_stats:
            stats = f" ({node.samples:,} visits, {node.conversion_rate*100:.1f}% CR)"
            label += stats
        
        # Highlight if best
        if abs(node.conversion_rate - best_cr) < 0.001 and node.conversion_rate > 0:
            label += " ⭐"
        
        # Tree structure
        connector = "└─ " if is_last else "├─ "
        lines.append(prefix + connector + label)
        
        # Children
        if node.children:
            extension = "   " if is_last else "│  "
            for i, child in enumerate(node.children):
                is_last_child = (i == len(node.children) - 1)
                self._ascii_node(
                    child,
                    lines,
                    prefix + extension,
                    is_last_child,
                    best_cr,
                    show_stats
                )
    
    def _find_best_cr(self, root: SegmentNode) -> float:
        """Find best conversion rate in tree"""
        best = root.conversion_rate
        
        def traverse(node: SegmentNode):
            nonlocal best
            if node.conversion_rate > best:
                best = node.conversion_rate
            for child in node.children:
                traverse(child)
        
        traverse(root)
        return best
    
    # ========================================================================
    # JSON FORMAT
    # ========================================================================
    
    def to_json(self, root: SegmentNode) -> Dict[str, Any]:
        """
        Generate JSON representation
        
        Returns:
            Nested dict representing tree
        """
        def node_to_dict(node: SegmentNode) -> Dict[str, Any]:
            return {
                'level': node.level,
                'feature_name': node.feature_name,
                'feature_value': node.feature_value,
                'segment_key': node.segment_key,
                'samples': node.samples,
                'conversions': node.conversions,
                'conversion_rate': node.conversion_rate,
                'is_leaf': node.is_leaf,
                'depth': node.depth,
                'children': [node_to_dict(child) for child in node.children]
            }
        
        return node_to_dict(root)
    
    def to_json_string(self, root: SegmentNode, indent: int = 2) -> str:
        """Generate formatted JSON string"""
        return json.dumps(self.to_json(root), indent=indent)
    
    # ========================================================================
    # HTML FORMAT
    # ========================================================================
    
    def to_html(self, root: SegmentNode) -> str:
        """
        Generate HTML representation with collapsible nodes
        
        Returns:
            HTML string with CSS and JavaScript
        """
        html = """
<!DOCTYPE html>
<html>
<head>
    <style>
        .tree { font-family: monospace; margin: 20px; }
        .node { margin-left: 20px; }
        .node-label { cursor: pointer; padding: 5px; }
        .node-label:hover { background-color: #f0f0f0; }
        .best { color: #d4af37; font-weight: bold; }
        .stats { color: #666; font-size: 0.9em; }
        .toggle { display: inline-block; width: 20px; }
        .children { display: block; }
        .children.collapsed { display: none; }
    </style>
</head>
<body>
    <div class="tree">
"""
        
        # Find best CR
        best_cr = self._find_best_cr(root)
        
        html += self._html_node(root, best_cr)
        
        html += """
    </div>
    <script>
        function toggleNode(id) {
            const children = document.getElementById('children-' + id);
            const toggle = document.getElementById('toggle-' + id);
            if (children.classList.contains('collapsed')) {
                children.classList.remove('collapsed');
                toggle.textContent = '▼';
            } else {
                children.classList.add('collapsed');
                toggle.textContent = '▶';
            }
        }
    </script>
</body>
</html>
"""
        return html
    
    def _html_node(self, node: SegmentNode, best_cr: float, node_id: str = "0") -> str:
        """Generate HTML for node"""
        # Label
        if node.level == 0:
            label = "Global"
        else:
            label = f"{node.feature_name}:{node.feature_value}"
        
        # Stats
        stats = f"{node.samples:,} visits, {node.conversion_rate*100:.1f}% CR"
        
        # Best marker
        is_best = abs(node.conversion_rate - best_cr) < 0.001 and node.conversion_rate > 0
        best_class = " best" if is_best else ""
        best_marker = " ⭐" if is_best else ""
        
        html = f'<div class="node">\n'
        
        if node.children:
            html += f'  <div class="node-label{best_class}" onclick="toggleNode(\'{node_id}\')">\n'
            html += f'    <span class="toggle" id="toggle-{node_id}">▼</span>\n'
        else:
            html += f'  <div class="node-label{best_class}">\n'
            html += f'    <span class="toggle"> </span>\n'
        
        html += f'    <strong>{label}</strong> <span class="stats">({stats})</span>{best_marker}\n'
        html += f'  </div>\n'
        
        # Children
        if node.children:
            html += f'  <div class="children" id="children-{node_id}">\n'
            for i, child in enumerate(node.children):
                child_id = f"{node_id}-{i}"
                html += self._html_node(child, best_cr, child_id)
            html += f'  </div>\n'
        
        html += '</div>\n'
        
        return html
    
    # ========================================================================
    # DOT FORMAT (Graphviz)
    # ========================================================================
    
    def to_dot(self, root: SegmentNode) -> str:
        """
        Generate DOT format for Graphviz
        
        Can be rendered with: dot -Tpng tree.dot -o tree.png
        
        Returns:
            DOT string
        """
        lines = []
        lines.append("digraph SegmentTree {")
        lines.append("  node [shape=box, style=rounded];")
        lines.append("  rankdir=TB;")
        lines.append("")
        
        # Find best CR for coloring
        best_cr = self._find_best_cr(root)
        
        # Generate nodes and edges
        node_counter = [0]  # Use list to maintain reference
        
        def add_node(node: SegmentNode) -> str:
            node_id = f"node{node_counter[0]}"
            node_counter[0] += 1
            
            # Label
            if node.level == 0:
                label = "Global"
            else:
                label = f"{node.feature_name}:\\n{node.feature_value}"
            
            label += f"\\n{node.samples:,} visits\\n{node.conversion_rate*100:.1f}% CR"
            
            # Color
            if abs(node.conversion_rate - best_cr) < 0.001 and node.conversion_rate > 0:
                color = "gold"
                style = "filled,bold"
            else:
                color = "lightblue"
                style = "filled"
            
            lines.append(f'  {node_id} [label="{label}", fillcolor={color}, style="{style}"];')
            
            # Children
            for child in node.children:
                child_id = add_node(child)
                lines.append(f"  {node_id} -> {child_id};")
            
            return node_id
        
        add_node(root)
        
        lines.append("}")
        
        return "\n".join(lines)
    
    # ========================================================================
    # SUMMARY STATS
    # ========================================================================
    
    def get_summary(self, root: SegmentNode) -> Dict[str, Any]:
        """
        Get summary statistics about tree
        
        Returns:
            {
                'total_nodes': 15,
                'leaf_nodes': 8,
                'max_depth': 3,
                'total_samples': 100000,
                'best_segment': {...},
                'worst_segment': {...}
            }
        """
        total_nodes = 0
        leaf_nodes = 0
        max_depth = 0
        total_samples = 0
        
        best_node = None
        worst_node = None
        
        def traverse(node: SegmentNode):
            nonlocal total_nodes, leaf_nodes, max_depth, total_samples, best_node, worst_node
            
            total_nodes += 1
            total_samples += node.samples
            max_depth = max(max_depth, node.depth)
            
            if node.is_leaf:
                leaf_nodes += 1
            
            # Track best/worst (excluding root)
            if node.level > 0:
                if best_node is None or node.conversion_rate > best_node.conversion_rate:
                    best_node = node
                if worst_node is None or node.conversion_rate < worst_node.conversion_rate:
                    worst_node = node
            
            for child in node.children:
                traverse(child)
        
        traverse(root)
        
        return {
            'total_nodes': total_nodes,
            'leaf_nodes': leaf_nodes,
            'max_depth': max_depth,
            'total_samples': total_samples,
            'avg_samples_per_node': total_samples / total_nodes if total_nodes > 0 else 0,
            'best_segment': {
                'segment_key': best_node.segment_key,
                'conversion_rate': best_node.conversion_rate,
                'samples': best_node.samples
            } if best_node else None,
            'worst_segment': {
                'segment_key': worst_node.segment_key,
                'conversion_rate': worst_node.conversion_rate,
                'samples': worst_node.samples
            } if worst_node else None
        }
