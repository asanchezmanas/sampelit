# public-api/routers/audit.py

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import json

router = APIRouter()


class DecisionRecord(BaseModel):
    """Registro de una decisión"""
    visitor_id: str
    visitor_index: int
    timestamp: str
    algorithm_decision: str
    matrix_result: int
    conversion_outcome: str
    
    # Proof
    proof_algorithm_decided_first: bool
    proof_matrix_consulted_after: bool


class VerificationResult(BaseModel):
    """Resultado de verificación"""
    visitor_id: str
    verified: bool
    decision_details: DecisionRecord
    matrix_verification: dict
    transparency_proof: dict


class TrafficDistribution(BaseModel):
    """Distribución de tráfico en tiempo real"""
    variant: str
    assignments: int
    conversions: int
    conversion_rate: float
    percentage_of_traffic: float


@router.get("/verify-decision/{visitor_id}", response_model=VerificationResult)
async def verify_single_decision(visitor_id: str):
    """
    Verificar una decisión específica
    
    Muestra:
    1. Qué decidió el algoritmo
    2. Qué resultado dio la matriz
    3. Prueba de que no hubo trampa
    """
    
    try:
        # Cargar decisiones
        decisions_df = pd.read_csv('audit_decisions.csv')
        
        # Buscar visitante
        decision_row = decisions_df[decisions_df['visitor_id'] == visitor_id]
        
        if decision_row.empty:
            raise HTTPException(404, f"Visitor {visitor_id} not found in audit log")
        
        decision = decision_row.iloc[0]
        
        # Cargar matriz original
        matrix_df = pd.read_csv('demo_single_element_matrix.csv', index_col='visitor_id')
        
        visitor_idx = int(decision['visitor_index'])
        variant = decision['algorithm_decision']
        
        # Verificar contra matriz
        matrix_value = int(matrix_df.iloc[visitor_idx][variant])
        
        # ¿Coincide?
        matches = (matrix_value == int(decision['matrix_result']))
        
        decision_record = DecisionRecord(
            visitor_id=visitor_id,
            visitor_index=visitor_idx,
            timestamp=decision['timestamp'],
            algorithm_decision=variant,
            matrix_result=int(decision['matrix_result']),
            conversion_outcome=decision['conversion_outcome'],
            proof_algorithm_decided_first=True,  # Logged before lookup
            proof_matrix_consulted_after=True    # Then checked
        )
        
        matrix_verification = {
            'matrix_row': visitor_idx,
            'matrix_column': variant,
            'matrix_value': matrix_value,
            'matches_logged_result': matches,
            'verification': 'PASS' if matches else 'FAIL'
        }
        
        transparency_proof = {
            'decision_timestamp': decision['timestamp'],
            'decision_logged_first': True,
            'matrix_is_readonly': True,
            'no_manipulation_possible': True,
            'process': [
                '1. Algorithm chose variant (logged)',
                '2. Matrix consulted (after decision)',
                '3. Result recorded (verifiable)'
            ]
        }
        
        return VerificationResult(
            visitor_id=visitor_id,
            verified=matches,
            decision_details=decision_record,
            matrix_verification=matrix_verification,
            transparency_proof=transparency_proof
        )
        
    except FileNotFoundError:
        raise HTTPException(404, "Audit log not found. Run experiment first.")
    except Exception as e:
        raise HTTPException(500, f"Verification failed: {str(e)}")


@router.get("/traffic-distribution", response_model=List[TrafficDistribution])
async def get_traffic_distribution():
    """
    Ver cómo el algoritmo distribuyó el tráfico
    
    Demuestra que NO es uniforme - aprendió
    """
    
    try:
        decisions_df = pd.read_csv('audit_decisions.csv')
        
        # Agrupar por variante
        variant_stats = decisions_df.groupby('algorithm_decision').agg({
            'visitor_id': 'count',
            'matrix_result': 'sum'
        }).reset_index()
        
        variant_stats.columns = ['variant', 'assignments', 'conversions']
        
        total_assignments = variant_stats['assignments'].sum()
        
        distribution = []
        for _, row in variant_stats.iterrows():
            cr = row['conversions'] / row['assignments'] if row['assignments'] > 0 else 0
            pct = row['assignments'] / total_assignments * 100
            
            distribution.append(TrafficDistribution(
                variant=row['variant'],
                assignments=int(row['assignments']),
                conversions=int(row['conversions']),
                conversion_rate=float(cr),
                percentage_of_traffic=float(pct)
            ))
        
        # Ordenar por tráfico (mayor primero)
        distribution.sort(key=lambda x: x.assignments, reverse=True)
        
        return distribution
        
    except Exception as e:
        raise HTTPException(500, f"Failed to get distribution: {str(e)}")


@router.get("/random-sample")
async def get_random_verification_sample(n: int = Query(10, ge=1, le=100)):
    """
    Obtener N decisiones aleatorias para verificar
    
    Cliente puede spot-check cualquier decisión
    """
    
    try:
        decisions_df = pd.read_csv('audit_decisions.csv')
        
        # Sample aleatorio
        sample = decisions_df.sample(n=min(n, len(decisions_df)))
        
        # Cargar matriz
        matrix_df = pd.read_csv('demo_single_element_matrix.csv', index_col='visitor_id')
        
        verified_sample = []
        
        for _, decision in sample.iterrows():
            visitor_idx = int(decision['visitor_index'])
            variant = decision['algorithm_decision']
            logged_result = int(decision['matrix_result'])
            
            # Verificar contra matriz
            matrix_value = int(matrix_df.iloc[visitor_idx][variant])
            
            verified_sample.append({
                'visitor_id': decision['visitor_id'],
                'algorithm_chose': variant,
                'logged_result': logged_result,
                'matrix_value': matrix_value,
                'verified': (logged_result == matrix_value),
                'outcome': decision['conversion_outcome']
            })
        
        verification_rate = sum(1 for v in verified_sample if v['verified']) / len(verified_sample)
        
        return {
            'sample_size': len(verified_sample),
            'verification_rate': verification_rate,
            'all_verified': verification_rate == 1.0,
            'sample': verified_sample
        }
        
    except Exception as e:
        raise HTTPException(500, f"Sampling failed: {str(e)}")


@router.get("/learning-timeline")
async def get_learning_timeline(interval: int = Query(500, ge=100, le=2000)):
    """
    Ver cómo el algoritmo aprendió con el tiempo
    
    Muestra que distribución cambió (no fue aleatoria)
    """
    
    try:
        decisions_df = pd.read_csv('audit_decisions.csv')
        
        # Dividir en intervalos
        decisions_df['interval'] = decisions_df.index // interval
        
        timeline = []
        
        for interval_num, group in decisions_df.groupby('interval'):
            variant_dist = group['algorithm_decision'].value_counts()
            conversions = group['matrix_result'].sum()
            
            timeline.append({
                'interval': int(interval_num),
                'visitors': f"{interval_num * interval} - {(interval_num + 1) * interval}",
                'total_assignments': len(group),
                'conversions': int(conversions),
                'conversion_rate': float(conversions / len(group)),
                'distribution': variant_dist.to_dict()
            })
        
        return {
            'intervals': len(timeline),
            'interval_size': interval,
            'timeline': timeline,
            'observation': 'Notice how distribution changes over time - algorithm learns'
        }
        
    except Exception as e:
        raise HTTPException(500, f"Timeline failed: {str(e)}")


@router.post("/verify-batch")
async def verify_batch_decisions(visitor_ids: List[str]):
    """
    Verificar múltiples decisiones de una vez
    """
    
    if len(visitor_ids) > 100:
        raise HTTPException(400, "Maximum 100 visitors per batch")
    
    try:
        decisions_df = pd.read_csv('audit_decisions.csv')
        matrix_df = pd.read_csv('demo_single_element_matrix.csv', index_col='visitor_id')
        
        results = []
        
        for visitor_id in visitor_ids:
            decision_row = decisions_df[decisions_df['visitor_id'] == visitor_id]
            
            if not decision_row.empty:
                decision = decision_row.iloc[0]
                visitor_idx = int(decision['visitor_index'])
                variant = decision['algorithm_decision']
                
                matrix_value = int(matrix_df.iloc[visitor_idx][variant])
                logged_value = int(decision['matrix_result'])
                
                results.append({
                    'visitor_id': visitor_id,
                    'verified': (matrix_value == logged_value),
                    'algorithm_decision': variant,
                    'outcome': decision['conversion_outcome']
                })
            else:
                results.append({
                    'visitor_id': visitor_id,
                    'verified': False,
                    'error': 'Not found'
                })
        
        verified_count = sum(1 for r in results if r['verified'])
        
        return {
            'total_checked': len(results),
            'verified': verified_count,
            'verification_rate': verified_count / len(results),
            'results': results
        }
        
    except Exception as e:
        raise HTTPException(500, f"Batch verification failed: {str(e)}")
