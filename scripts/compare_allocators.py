# scripts/compare_allocators.py

"""
Compare performance of different allocators

Usage:
    python scripts/compare_allocators.py thompson ucb --trials 1000
"""

import asyncio
import argparse
import random
from typing import List, Dict, Any
from engine.core import _get_allocator


class SimulatedExperiment:
    """
    Simulates an A/B test with known true conversion rates
    
    Measures:
    - Regret (how much worse than optimal)
    - Final distribution
    - Convergence speed
    """
    
    def __init__(
        self,
        true_rates: List[float],
        allocator_strategy: str,
        allocator_config: Dict[str, Any]
    ):
        self.true_rates = true_rates
        self.n_variants = len(true_rates)
        self.best_rate = max(true_rates)
        
        # Create allocator
        self.allocator = _get_allocator(allocator_strategy, allocator_config)
        
        # State
        self.variants = [
            {
                'id': f'variant_{i}',
                '_internal_state': {
                    'samples': 0,
                    'success_count': 1,  # Prior
                    'failure_count': 1   # Prior
                }
            }
            for i in range(self.n_variants)
        ]
        
        # Metrics
        self.total_reward = 0.0
        self.optimal_reward = 0.0
        self.selections = [0] * self.n_variants
    
    async def run_trial(self):
        """Run one trial (one visitor)"""
        
        # Select variant
        selected_id = await self.allocator.select(self.variants, {})
        variant_idx = int(selected_id.split('_')[1])
        
        # Simulate conversion with true rate
        true_rate = self.true_rates[variant_idx]
        converted = random.random() < true_rate
        reward = 1.0 if converted else 0.0
        
        # Update state
        variant = self.variants[variant_idx]
        state = variant['_internal_state']
        
        state['samples'] += 1
        if converted:
            state['success_count'] += 1
        else:
            state['failure_count'] = state.get('failure_count', 1) + 1
        
        # Track metrics
        self.selections[variant_idx] += 1
        self.total_reward += reward
        self.optimal_reward += self.best_rate
        
        return variant_idx, reward
    
    async def run(self, n_trials: int):
        """Run full experiment"""
        
        for _ in range(n_trials):
            await self.run_trial()
    
    def get_results(self) -> Dict[str, Any]:
        """Get experiment results"""
        
        regret = self.optimal_reward - self.total_reward
        
        return {
            'total_trials': sum(self.selections),
            'total_reward': self.total_reward,
            'optimal_reward': self.optimal_reward,
            'regret': regret,
            'regret_percent': (regret / self.optimal_reward) * 100,
            'selections': self.selections,
            'selection_percent': [
                (s / sum(self.selections)) * 100
                for s in self.selections
            ]
        }


async def compare_allocators(
    strategies: List[str],
    true_rates: List[float],
    n_trials: int = 1000,
    n_replications: int = 10
):
    """
    Compare multiple allocators
    
    Args:
        strategies: List of allocator strategies to compare
        true_rates: True conversion rates for variants
        n_trials: Number of trials per experiment
        n_replications: Number of times to repeat (for averaging)
    """
    
    print(f"\n{'='*70}")
    print(f"ALLOCATOR COMPARISON")
    print(f"{'='*70}")
    print(f"\nTrue conversion rates: {true_rates}")
    print(f"Best possible rate: {max(true_rates):.1%}")
    print(f"Trials per experiment: {n_trials}")
    print(f"Replications: {n_replications}")
    print()
    
    results_by_strategy = {}
    
    for strategy in strategies:
        print(f"\n🔄 Running {strategy}...")
        
        # Run multiple replications
        all_results = []
        
        for rep in range(n_replications):
            experiment = SimulatedExperiment(
                true_rates=true_rates,
                allocator_strategy=strategy,
                allocator_config={}
            )
            
            await experiment.run(n_trials)
            results = experiment.get_results()
            all_results.append(results)
        
        # Average results
        avg_regret = sum(r['regret'] for r in all_results) / n_replications
        avg_regret_pct = sum(r['regret_percent'] for r in all_results) / n_replications
        
        avg_selections = [
            sum(r['selections'][i] for r in all_results) / n_replications
            for i in range(len(true_rates))
        ]
        
        avg_selection_pct = [
            (s / n_trials) * 100
            for s in avg_selections
        ]
        
        results_by_strategy[strategy] = {
            'avg_regret': avg_regret,
            'avg_regret_pct': avg_regret_pct,
            'avg_selections': avg_selections,
            'avg_selection_pct': avg_selection_pct,
        }
    
    # Print comparison table
    print(f"\n{'='*70}")
    print("RESULTS")
    print(f"{'='*70}\n")
    
    print(f"{'Strategy':<20} {'Regret':<15} {'Regret %':<15} {'Best Variant %':<15}")
    print(f"{'-'*70}")
    
    for strategy, results in results_by_strategy.items():
        best_idx = true_rates.index(max(true_rates))
        best_pct = results['avg_selection_pct'][best_idx]
        
        print(
            f"{strategy:<20} "
            f"{results['avg_regret']:<15.2f} "
            f"{results['avg_regret_pct']:<15.2f}% "
            f"{best_pct:<15.1f}%"
        )
    
    # Selection distribution
    print(f"\n\nSelection Distribution:")
    print(f"{'-'*70}")
    
    for i, rate in enumerate(true_rates):
        print(f"\nVariant {i} (true CR: {rate:.1%}):")
        for strategy, results in results_by_strategy.items():
            pct = results['avg_selection_pct'][i]
            bar = '█' * int(pct / 2)
            print(f"  {strategy:<15} {pct:>5.1f}% {bar}")
    
    # Winner
    print(f"\n{'='*70}")
    winner = min(results_by_strategy.items(), key=lambda x: x[1]['avg_regret'])
    print(f"🏆 WINNER: {winner[0]} (lowest regret: {winner[1]['avg_regret']:.2f})")
    print(f"{'='*70}\n")


async def main():
    parser = argparse.ArgumentParser(description='Compare allocators')
    parser.add_argument(
        'strategies',
        nargs='+',
        help='Allocator strategies to compare (e.g., thompson ucb epsilon_greedy)'
    )
    parser.add_argument(
        '--rates',
        nargs='+',
        type=float,
        default=[0.05, 0.08, 0.12],
        help='True conversion rates (default: 0.05 0.08 0.12)'
    )
    parser.add_argument(
        '--trials',
        type=int,
        default=1000,
        help='Number of trials per experiment (default: 1000)'
    )
    parser.add_argument(
        '--replications',
        type=int,
        default=10,
        help='Number of replications for averaging (default: 10)'
    )
    
    args = parser.parse_args()
    
    await compare_allocators(
        strategies=args.strategies,
        true_rates=args.rates,
        n_trials=args.trials,
        n_replications=args.replications
    )


if __name__ == '__main__':
    asyncio.run(main())
