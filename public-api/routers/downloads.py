# public-api/routers/downloads.py

from fastapi import APIRouter, HTTPException, Query, Path
from fastapi.responses import FileResponse, StreamingResponse
from typing import Literal
import pandas as pd
import json
import os

from utils.file_exporters import ExperimentFileExporter

router = APIRouter()


@router.get("/conversion-matrix/{experiment_id}")
async def download_conversion_matrix(
    experiment_id: str = Path(..., description="Experiment ID"),
    format: Literal['csv', 'excel'] = Query('csv', description="Output format")
):
    """
    Descargar matriz de conversiones
    
    Formatos:
    - csv: Simple CSV
    - excel: Excel con múltiples hojas y formato
    """
    
    try:
        # Cargar matriz
        matrix_path = f'demo_single_element_matrix.csv'  # Or from DB
        if not os.path.exists(matrix_path):
            raise HTTPException(404, "Matrix not found")
        
        matrix_df = pd.read_csv(matrix_path, index_col='visitor_id')
        
        # Cargar metadata
        metadata_path = f'demo_single_element_metadata.json'
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        # Exportar
        exporter = ExperimentFileExporter(experiment_id)
        
        if format == 'csv':
            filepath = exporter.export_conversion_matrix_csv(matrix_df)
            media_type = 'text/csv'
        else:  # excel
            filepath = exporter.export_conversion_matrix_excel(matrix_df, metadata)
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        return FileResponse(
            path=filepath,
            media_type=media_type,
            filename=os.path.basename(filepath)
        )
        
    except FileNotFoundError:
        raise HTTPException(404, "Conversion matrix not found")
    except Exception as e:
        raise HTTPException(500, f"Download failed: {str(e)}")


@router.get("/audit-log/{experiment_id}")
async def download_audit_log(
    experiment_id: str = Path(..., description="Experiment ID"),
    format: Literal['csv', 'excel'] = Query('csv', description="Output format")
):
    """
    Descargar audit log (registro de decisiones)
    
    Formatos:
    - csv: CSV simple con todas las decisiones
    - excel: Excel con hojas múltiples (decisiones, resumen, timeline)
    """
    
    try:
        # Cargar audit log
        audit_path = 'audit_decisions.csv'
        if not os.path.exists(audit_path):
            raise HTTPException(404, "Audit log not found. Run experiment first.")
        
        decisions_df = pd.read_csv(audit_path)
        
        # Exportar
        exporter = ExperimentFileExporter(experiment_id)
        
        if format == 'csv':
            filepath = exporter.export_audit_log_csv(decisions_df)
            media_type = 'text/csv'
        else:  # excel
            filepath = exporter.export_audit_log_excel(decisions_df)
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        return FileResponse(
            path=filepath,
            media_type=media_type,
            filename=os.path.basename(filepath)
        )
        
    except FileNotFoundError:
        raise HTTPException(404, "Audit log not found")
    except Exception as e:
        raise HTTPException(500, f"Download failed: {str(e)}")


@router.get("/results/{experiment_id}")
async def download_results(
    experiment_id: str = Path(..., description="Experiment ID")
):
    """
    Descargar resultados comparativos (Excel)
    
    Incluye:
    - Resumen ejecutivo
    - Comparación tradicional vs Samplit
    - Info de verificación
    """
    
    try:
        # Cargar resultados
        results_path = 'demo_comparison_results.json'
        if not os.path.exists(results_path):
            raise HTTPException(404, "Results not found. Run experiment first.")
        
        with open(results_path, 'r') as f:
            results = json.load(f)
        
        # Exportar
        exporter = ExperimentFileExporter(experiment_id)
        
        filepath = exporter.export_results_excel(
            traditional_results=results['traditional'],
            samplit_results=results['samplit'],
            comparison=results['comparison']
        )
        
        return FileResponse(
            path=filepath,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=os.path.basename(filepath)
        )
        
    except FileNotFoundError:
        raise HTTPException(404, "Results not found")
    except Exception as e:
        raise HTTPException(500, f"Download failed: {str(e)}")


@router.get("/experiment-details/{experiment_id}")
async def download_experiment_details(
    experiment_id: str = Path(..., description="Experiment ID"),
    format: Literal['json', 'excel'] = Query('json', description="Output format")
):
    """
    Descargar detalles completos del experimento
    
    Formatos:
    - json: Configuración completa en JSON
    - excel: Formato legible con hojas
    """
    
    try:
        # En producción: cargar de DB
        # Por ahora simulamos
        experiment_data = {
            'id': experiment_id,
            'name': 'Demo Experiment',
            'description': 'Single-element demo with 5 variants',
            'status': 'completed',
            'created_at': '2025-12-13T10:00:00Z',
            'started_at': '2025-12-13T10:05:00Z',
            'completed_at': '2025-12-13T11:00:00Z',
            'variants': [
                {'name': 'Variant A', 'description': 'Sign Up Now', 'total_assignments': 892, 'total_conversions': 25},
                {'name': 'Variant B', 'description': 'Get Started Free', 'total_assignments': 4521, 'total_conversions': 190},
                {'name': 'Variant C', 'description': 'Try It Free', 'total_assignments': 2103, 'total_conversions': 74},
                {'name': 'Variant D', 'description': 'Start Your Trial', 'total_assignments': 1567, 'total_conversions': 49},
                {'name': 'Variant E', 'description': 'Join Today', 'total_assignments': 917, 'total_conversions': 22}
            ]
        }
        
        exporter = ExperimentFileExporter(experiment_id)
        
        if format == 'json':
            filepath = exporter.export_experiment_details_json(experiment_data)
            media_type = 'application/json'
        else:  # excel
            filepath = exporter.export_experiment_details_excel(experiment_data)
            media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        return FileResponse(
            path=filepath,
            media_type=media_type,
            filename=os.path.basename(filepath)
        )
        
    except Exception as e:
        raise HTTPException(500, f"Download failed: {str(e)}")


@router.get("/complete-package/{experiment_id}")
async def download_complete_package(
    experiment_id: str = Path(..., description="Experiment ID")
):
    """
    Descargar paquete COMPLETO (ZIP)
    
    Incluye:
    - Matriz de conversiones (CSV + Excel)
    - Audit log (CSV + Excel)
    - Resultados (Excel)
    - Detalles experimento (JSON + Excel)
    - README con instrucciones
    - MANIFEST.json
    """
    
    try:
        # Cargar todos los datos
        matrix_df = pd.read_csv('demo_single_element_matrix.csv', index_col='visitor_id')
        decisions_df = pd.read_csv('audit_decisions.csv')
        
        with open('demo_single_element_metadata.json', 'r') as f:
            metadata = json.load(f)
        
        with open('demo_comparison_results.json', 'r') as f:
            results = json.load(f)
        
        # Experiment data (mock)
        experiment_data = {
            'id': experiment_id,
            'name': 'Demo Experiment',
            'description': 'Complete audit package',
            'status': 'completed',
            'created_at': '2025-12-13T10:00:00Z',
            'variants': []  # ... cargar de DB
        }
        
        # Crear package
        exporter = ExperimentFileExporter(experiment_id)
        
        zip_filepath = exporter.create_complete_package(
            matrix_df=matrix_df,
            decisions_df=decisions_df,
            metadata=metadata,
            traditional_results=results['traditional'],
            samplit_results=results['samplit'],
            comparison=results['comparison'],
            experiment_data=experiment_data
        )
        
        return FileResponse(
            path=zip_filepath,
            media_type='application/zip',
            filename=os.path.basename(zip_filepath)
        )
        
    except FileNotFoundError as e:
        raise HTTPException(404, f"Required file not found: {str(e)}")
    except Exception as e:
        raise HTTPException(500, f"Package creation failed: {str(e)}")


@router.get("/list-available/{experiment_id}")
async def list_available_downloads(
    experiment_id: str = Path(..., description="Experiment ID")
):
    """
    Listar todos los archivos disponibles para descargar
    """
    
    available_files = {
        'conversion_matrix': {
            'formats': ['csv', 'excel'],
            'description': 'Pre-generated conversion matrix',
            'endpoints': {
                'csv': f'/api/v1/downloads/conversion-matrix/{experiment_id}?format=csv',
                'excel': f'/api/v1/downloads/conversion-matrix/{experiment_id}?format=excel'
            }
        },
        'audit_log': {
            'formats': ['csv', 'excel'],
            'description': 'Complete audit trail of all decisions',
            'endpoints': {
                'csv': f'/api/v1/downloads/audit-log/{experiment_id}?format=csv',
                'excel': f'/api/v1/downloads/audit-log/{experiment_id}?format=excel'
            }
        },
        'results': {
            'formats': ['excel'],
            'description': 'Comparative results (Traditional vs Samplit)',
            'endpoints': {
                'excel': f'/api/v1/downloads/results/{experiment_id}'
            }
        },
        'experiment_details': {
            'formats': ['json', 'excel'],
            'description': 'Complete experiment configuration',
            'endpoints': {
                'json': f'/api/v1/downloads/experiment-details/{experiment_id}?format=json',
                'excel': f'/api/v1/downloads/experiment-details/{experiment_id}?format=excel'
            }
        },
        'complete_package': {
            'formats': ['zip'],
            'description': 'All files in a single ZIP package',
            'endpoints': {
                'zip': f'/api/v1/downloads/complete-package/{experiment_id}'
            }
        }
    }
    
    return {
        'experiment_id': experiment_id,
        'available_downloads': available_files,
        'note': 'All files include timestamps in filename for version control'
    }
