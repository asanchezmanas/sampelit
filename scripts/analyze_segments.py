# scripts/analyze_segments.py

"""
CLI tool for segment analysis

Usage:
    python scripts/analyze_segments.py <experiment_id> [--min-samples 50]
"""

import asyncio
import asyncpg
import os
import sys
from tabulate import tabulate

from engine.services.contextual_service import ContextualService


async def analyze_experiment(experiment_id: str, min_samples: int = 50):
    """Analyze segments for experiment"""
    
    database_url = os.getenv('DATABASE_URL')
    pool = await asyncpg.create_pool(database_url)
    
    try:
        service = ContextualService(pool)
        
        print(f"\n{'='*80}")
        print(f"SEGMENT ANALYSIS: {experiment_id}")
        print(f"{'='*80}\n")
        
        # Get insights
        insights = await service.get_segment_insights(experiment_id)
        
        # Print summary
        print("📊 SUMMARY")
        print(f"  Total Segments: {insights['summary']['total_segments']}")
        print(f"  High Performers: {insights['summary']['high_performers']}")
        print(f"  Underperformers: {insights['summary']['underperformers']}")
        print()
        
        # Print top segments
        print("🏆 TOP SEGMENTS")
        if insights['top_segments']:
            table_data = [
                [
                    s['segment_key'],
                    s['visits'],
                    f"{s['conversion_rate']*100:.2f}%",
                    s['best_variant'] or 'N/A'
                ]
                for s in insights['top_segments']
            ]
            print(tabulate(
                table_data,
                headers=['Segment', 'Visits', 'CR', 'Best Variant'],
                tablefmt='grid'
            ))
        else:
            print("  No segments with sufficient data yet")
        print()
        
        # Print high performers
        if insights['high_performing_segments']:
            print("📈 HIGH PERFORMING SEGMENTS (>20% lift)")
            table_data = [
                [
                    s['segment_key'],
                    s['variant'],
                    f"{s['segment_cr']*100:.2f}%",
                    f"{s['global_cr']*100:.2f}%",
                    f"+{s['lift_percent']:.0f}%"
                ]
                for s in insights['high_performing_segments']
            ]
            print(tabulate(
                table_data,
                headers=['Segment', 'Variant', 'Segment CR', 'Global CR', 'Lift'],
                tablefmt='grid'
            ))
            print()
        
        # Print underperformers
        if insights['underperforming_segments']:
            print("📉 UNDERPERFORMING SEGMENTS (<-20% lift)")
            table_data = [
                [
                    s['segment_key'],
                    s['variant'],
                    f"{s['segment_cr']*100:.2f}%",
                    f"{s['global_cr']*100:.2f}%",
                    f"{s['lift_percent']:.0f}%"
                ]
                for s in insights['underperforming_segments']
            ]
            print(tabulate(
                table_data,
                headers=['Segment', 'Variant', 'Segment CR', 'Global CR', 'Lift'],
                tablefmt='grid'
            ))
            print()
        
        # Print traffic distribution
        print("🚦 TRAFFIC DISTRIBUTION")
        if insights['traffic_distribution']:
            table_data = [
                [s['segment'], s['visits'], f"{s['percent']:.1f}%"]
                for s in insights['traffic_distribution']
            ]
            print(tabulate(
                table_data,
                headers=['Segment', 'Visits', '% of Traffic'],
                tablefmt='grid'
            ))
        print()
        
        # Print recommendations
        print("💡 RECOMMENDATIONS")
        for i, rec in enumerate(insights['recommendations'], 1):
            print(f"  {i}. {rec}")
        print()
        
        print(f"{'='*80}\n")
        
    finally:
        await pool.close()


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python analyze_segments.py <experiment_id> [--min-samples N]")
        sys.exit(1)
    
    experiment_id = sys.argv[1]
    min_samples = 50
    
    if '--min-samples' in sys.argv:
        idx = sys.argv.index('--min-samples')
        min_samples = int(sys.argv[idx + 1])
    
    asyncio.run(analyze_experiment(experiment_id, min_samples))
```

**Output esperado:**
```
================================================================================
SEGMENT ANALYSIS: exp_abc123
================================================================================

📊 SUMMARY
  Total Segments: 12
  High Performers: 3
  Underperformers: 2

🏆 TOP SEGMENTS
+----------------------------------+---------+--------+---------------+
| Segment                          | Visits  | CR     | Best Variant  |
+==================================+=========+========+===============+
| device:mobile|source:instagram   | 2,543   | 18.2%  | Variant B     |
+----------------------------------+---------+--------+---------------+
| device:desktop|source:google     | 1,892   | 15.1%  | Variant A     |
+----------------------------------+---------+--------+---------------+
| device:mobile|source:facebook    | 1,234   | 12.5%  | Variant B     |
+----------------------------------+---------+--------+---------------+

📈 HIGH PERFORMING SEGMENTS (>20% lift)
+----------------------------------+------------+-------------+------------+-------+
| Segment                          | Variant    | Segment CR  | Global CR  | Lift  |
+==================================+============+=============+============+=======+
| device:mobile|source:instagram   | Variant B  | 18.20%      | 12.00%     | +52%  |
+----------------------------------+------------+-------------+------------+-------+
| device:desktop|source:google     | Variant A  | 15.10%      | 12.00%     | +26%  |
+----------------------------------+------------+-------------+------------+-------+

📉 UNDERPERFORMING SEGMENTS (<-20% lift)
+----------------------------------+------------+-------------+------------+-------+
| Segment                          | Variant    | Segment CR  | Global CR  | Lift  |
+==================================+============+=============+============+=======+
| device:tablet|source:direct      | Variant A  | 6.50%       | 12.00%     | -46%  |
+----------------------------------+------------+-------------+------------+-------+

🚦 TRAFFIC DISTRIBUTION
+----------------------------------+---------+--------------+
| Segment                          | Visits  | % of Traffic |
+==================================+=========+==============+
| device:mobile|source:instagram   | 2,543   | 32.1%        |
+----------------------------------+---------+--------------+
| device:desktop|source:google     | 1,892   | 23.9%        |
+----------------------------------+---------+--------------+
| device:mobile|source:facebook    | 1,234   | 15.6%        |
+----------------------------------+---------+--------------+

💡 RECOMMENDATIONS
  1. 🎯 Focus on device:mobile|source:instagram: 52% lift with variant 'Variant B'
  2. ⚠️ Segment device:tablet|source:direct underperforming: 46% worse than average
  3. 💡 Consider creating separate experiments for top 3 segments

================================================================================
