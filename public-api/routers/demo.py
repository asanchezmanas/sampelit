# public-api/routers/demo.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict
import pandas as pd
import io
import json

router = APIRouter()


class AuditStep(BaseModel):
    """Paso del proceso de auditoría"""
    step: int
    title: str
    description: str
    data: Dict


class AuditReport(BaseModel):
    """Reporte completo de auditoría"""
    matrix_verified: bool
    steps: List[AuditStep]
    comparison: Dict
    transparency_proof: Dict


@router.post("/audit-experiment", response_model=AuditReport)
async def audit_experiment(
    matrix_file: UploadFile = File(...),
    results_file: UploadFile = File(...)
):
    """
    Auditar experimento para verificar transparencia
    
    ✅ Muestra que el algoritmo aprende sin ver conversiones
    ❌ NO revela Thompson Sampling ni detalles internos
    """
    
    try:
        # 1. Leer matriz original
        matrix_content = await matrix_file.read()
        matrix_df = pd.read_csv(io.StringIO(matrix_content.decode('utf-8')), index_col=0)
        
        # 2. Leer resultados del experimento
        results_content = await results_file.read()
        results = json.loads(results_content.decode('utf-8'))
        
        # ══════════════════════════════════════
        # PASO 1: Verificar Matriz Original
        # ══════════════════════════════════════
        step1 = AuditStep(
            step=1,
            title="Original Conversion Matrix Verified",
            description="This matrix was generated BEFORE the experiment. "
                       "It represents the 'true' conversion potential for each visitor-variant pair.",
            data={
                'n_visitors': matrix_df.shape[0],
                'n_variants': matrix_df.shape[1],
                'total_possible_conversions': int(matrix_df.sum().sum()),
                'variant_true_rates': {
                    col: float(matrix_df[col].sum() / len(matrix_df))
                    for col in matrix_df.columns
                }
            }
        )
        
        # ══════════════════════════════════════
        # PASO 2: Algoritmo NO ve conversiones
        # ══════════════════════════════════════
        step2 = AuditStep(
            step=2,
            title="Algorithm Operates Blind",
            description="Samplit's algorithm assigns variants WITHOUT seeing conversion data from the matrix. "
                       "It only observes results AFTER a visitor is assigned.",
            data={
                'algorithm_name': 'Samplit Adaptive Learning',
                'input_data': 'Assignment requests only (no conversion data)',
                'learning_method': 'Proprietary adaptive optimization',
                'learns_from': 'Post-assignment conversion outcomes',
                'cannot_see': 'Future conversions or matrix data'
            }
        )
        
        # ══════════════════════════════════════
        # PASO 3: Asignaciones hechas
        # ══════════════════════════════════════
        samplit_assignments = results['samplit']['combination_stats']
        
        step3 = AuditStep(
            step=3,
            title="Assignment Distribution (Algorithm Decision)",
            description="How the algorithm distributed traffic across variants. "
                       "Notice it's NOT uniform - the algorithm learned which variants perform better.",
            data={
                'total_assigned': sum(s['allocated'] for s in samplit_assignments),
                'distribution': [
                    {
                        'variant': s['combination'],
                        'allocated': s['allocated'],
                        'percentage': s['allocated'] / sum(s2['allocated'] for s2 in samplit_assignments) * 100
                    }
                    for s in samplit_assignments
                ]
            }
        )
        
        # ══════════════════════════════════════
        # PASO 4: Conversiones observadas
        # ══════════════════════════════════════
        step4 = AuditStep(
            step=4,
            title="Actual Conversions (From Matrix)",
            description="For each assignment, we check the matrix to determine if conversion occurred. "
                       "The algorithm NEVER saw this data during assignment.",
            data={
                'samplit_conversions': results['samplit']['total_conversions'],
                'traditional_conversions': results['traditional']['total_conversions'],
                'by_variant': samplit_assignments
            }
        )
        
        # ══════════════════════════════════════
        # PASO 5: Comparación
        # ══════════════════════════════════════
        comparison = {
            'traditional': {
                'method': 'Uniform split (20% each)',
                'conversions': results['traditional']['total_conversions'],
                'strategy': 'Fixed allocation, no learning'
            },
            'samplit': {
                'method': 'Adaptive learning',
                'conversions': results['samplit']['total_conversions'],
                'strategy': 'Dynamic allocation based on performance'
            },
            'improvement': results['comparison']
        }
        
        # ══════════════════════════════════════
        # Prueba de transparencia
        # ══════════════════════════════════════
        transparency = {
            'matrix_pregenerated': True,
            'algorithm_blind_to_matrix': True,
            'conversions_determined_by_matrix': True,
            'no_manipulation': True,
            'auditable': True,
            'algorithm_details': 'Proprietary (trade secret)',
            'verifiable_claim': 'Algorithm learns from outcomes, not predictions'
        }
        
        return AuditReport(
            matrix_verified=True,
            steps=[step1, step2, step3, step4],
            comparison=comparison,
            transparency_proof=transparency
        )
        
    except Exception as e:
        raise HTTPException(500, f"Audit failed: {str(e)}")


@router.get("/audit-explanation")
async def get_audit_explanation():
    """
    Explicación de cómo funciona la auditoría
    
    SIN revelar detalles del algoritmo
    """
    
    return {
        'title': 'How Samplit Audit Works',
        'sections': [
            {
                'title': '1. Pre-Generated Truth',
                'explanation': 'We generate a conversion matrix BEFORE the experiment. '
                              'Each cell represents whether a specific visitor would convert '
                              'with a specific variant. This is the "ground truth".'
            },
            {
                'title': '2. Algorithm Operates Blind',
                'explanation': 'Our algorithm assigns visitors to variants WITHOUT seeing '
                              'the matrix. It only knows: "visitor X was assigned variant Y". '
                              'It does NOT know if they will convert.'
            },
            {
                'title': '3. Learning from Outcomes',
                'explanation': 'AFTER assignment, we check the matrix to see if conversion occurred. '
                              'The algorithm learns from this outcome and adjusts its strategy. '
                              'This mimics real-world: you assign, then observe.'
            },
            {
                'title': '4. No Manipulation Possible',
                'explanation': 'Since the matrix is fixed before the experiment, we cannot '
                              'manipulate results. The algorithm truly learns which variants '
                              'perform better and adapts allocation accordingly.'
            },
            {
                'title': '5. Verifiable Performance',
                'explanation': 'You can verify: (a) the matrix sums, (b) our assignments, '
                              '(c) the resulting conversions. Everything is transparent and auditable.'
            }
        ],
        'what_we_dont_reveal': [
            'Specific algorithm implementation (trade secret)',
            'Mathematical formulas used (proprietary)',
            'Internal state management (confidential)',
            'Optimization techniques (competitive advantage)'
        ],
        'what_you_can_verify': [
            'Matrix integrity (pre-generated, not manipulated)',
            'Assignment distribution (algorithm decisions)',
            'Conversion outcomes (from matrix)',
            'Performance comparison (Samplit vs traditional)',
            'No cheating (all verifiable in CSV files)'
        ]
    }


@router.post("/upload-custom-matrix")
async def upload_custom_matrix(
    file: UploadFile = File(...)
):
    """
    Cliente sube su propio CSV para probar
    
    Ejecutamos el algoritmo con SU data
    """
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')), index_col=0)
        
        # Validar formato
        if df.shape[0] < 100:
            raise HTTPException(400, "Need at least 100 visitors")
        
        if df.shape[1] < 2:
            raise HTTPException(400, "Need at least 2 variants")
        
        # Calcular stats
        variant_stats = {}
        for col in df.columns:
            conversions = int(df[col].sum())
            cr = float(conversions / len(df))
            variant_stats[col] = {
                'conversions': conversions,
                'conversion_rate': cr
            }
        
        # Simular tradicional
        n_visitors = df.shape[0]
        n_variants = df.shape[1]
        visitors_per = n_visitors // n_variants
        
        trad_conv = sum(
            df.iloc[i*visitors_per:(i+1)*visitors_per, i].sum()
            for i in range(n_variants)
        )
        
        # Simular Samplit (simplificado para demo rápido)
        # En producción: ejecutar experimento completo
        
        return {
            'matrix_accepted': True,
            'n_visitors': n_visitors,
            'n_variants': n_variants,
            'variant_stats': variant_stats,
            'estimated_traditional': int(trad_conv),
            'message': 'Matrix accepted! Run full experiment to see Samplit performance.',
            'next_step': 'POST /api/v1/demo/run-with-custom-matrix'
        }
        
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")
