# public-api/routers/demo.py

@router.post("/compare-approaches")
async def compare_sequential_vs_multielement(
    monthly_visitors: int,
    n_elements: int = 3,
    variants_per_element: int = 3
):
    """
    Compara approach secuencial vs multi-elemento
    
    Muestra el valor diferencial de Samplit
    """
    
    # Secuencial (tradicional)
    weeks_per_test = 2
    total_weeks_sequential = n_elements * weeks_per_test
    visitors_sequential = (total_weeks_sequential / 4) * monthly_visitors
    avg_improvement_sequential = 0.10 * n_elements  # 10% por elemento
    
    # Multi-elemento (Samplit)
    weeks_multielement = 3
    visitors_multielement = (weeks_multielement / 4) * monthly_visitors
    # Mejora incluye sinergia (+20% por interacciones)
    avg_improvement_multielement = (0.10 * n_elements) * 1.20
    
    return {
        'sequential': {
            'weeks': total_weeks_sequential,
            'visitors_used': int(visitors_sequential),
            'improvement': f"{avg_improvement_sequential:.0%}",
            'combinations_tested': n_elements * variants_per_element
        },
        'multielement': {
            'weeks': weeks_multielement,
            'visitors_used': int(visitors_multielement),
            'improvement': f"{avg_improvement_multielement:.0%}",
            'combinations_tested': variants_per_element ** n_elements,
            'synergy_bonus': '+20% from interactions'
        },
        'advantage': {
            'time_saved': f"{total_weeks_sequential - weeks_multielement} weeks",
            'extra_improvement': f"+{(avg_improvement_multielement - avg_improvement_sequential):.0%}",
            'efficiency': f"{((avg_improvement_multielement / weeks_multielement) / (avg_improvement_sequential / total_weeks_sequential)):.1f}x faster learning"
        }
    }
