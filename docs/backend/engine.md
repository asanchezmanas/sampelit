# 🧠 Motor de Optimización (Engine)

**Versión**: 1.0  
**Última actualización**: Diciembre 2024  
**Nivel**: Intermediate 🟡

---

## 🎯 ¿Qué es el Motor de Optimización?

El **Engine** es el cerebro algorítmico de Samplit. Implementa algoritmos de **Multi-Armed Bandit** que:

1. Deciden qué variante mostrar a cada visitante
2. Aprenden de los resultados en tiempo real
3. Optimizan automáticamente hacia la variante ganadora

```
Visitante llega
      │
      ▼
┌─────────────────┐
│     ENGINE      │ ← Thompson Sampling
│   (Allocator)   │
└───────┬─────────┘
        │
        ▼
  ┌───────────┐
  │ Variante  │ ← Decisión inteligente
  └───────────┘
```

---

## 📁 Estructura de Archivos

```
engine/
├── __init__.py
├── core/
│   ├── __init__.py           # Exports públicos
│   ├── _base.py              # Clase base abstracta
│   ├── allocators/
│   │   ├── __init__.py
│   │   ├── bayesian.py       # Thompson Sampling (principal)
│   │   ├── _bayesian.py      # Lógica matemática
│   │   ├── sequential.py     # A/B clásico (round-robin)
│   │   ├── _explore.py       # Estrategias de exploración
│   │   └── _registry.py      # Registro de allocators
│   └── math/
│       └── statistics.py     # Funciones estadísticas
└── state/
    └── state_manager.py      # Gestión de estado encriptado
```

---

## 📄 Archivos Clave Explicados

---

### 1️⃣ `_base.py` - Clase Base Abstracta

**Propósito**: Define la interfaz que todos los allocators deben implementar.

```python
# engine/core/_base.py

"""
Base Allocator - Contrato para todos los algoritmos de asignación.

🎓 PATRÓN: Strategy Pattern
───────────────────────────
Permite cambiar el algoritmo de asignación sin modificar el resto del código.

ExperimentService no sabe qué allocator usa, solo llama:
    allocator.select(variants)

Esto permite:
- Añadir nuevos algoritmos fácilmente
- Testear diferentes estrategias
- Configurar por experimento
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseAllocator(ABC):
    """
    Interfaz abstracta para algoritmos de asignación.
    
    Todos los allocators DEBEN implementar:
    - select(): Elegir una variante de la lista
    - update(): Actualizar estado tras una conversión
    """
    
    @abstractmethod
    def select(
        self,
        variants: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Selecciona la mejor variante para mostrar.
        
        Args:
            variants: Lista de variantes disponibles
                [
                    {
                        "id": "var-1",
                        "name": "Control",
                        "total_allocations": 1000,
                        "total_conversions": 80
                    },
                    ...
                ]
            context: Contexto opcional (device, hora, etc.)
        
        Returns:
            La variante seleccionada
        
        🎓 NOTA IMPORTANTE:
        ──────────────────
        Esta función debe ser DETERMINÍSTICA para el mismo estado.
        La aleatoriedad viene de muestrear distribuciones,
        no de random() sin sentido.
        """
        pass
    
    @abstractmethod
    def update(
        self,
        variant_id: str,
        reward: float,
        context: Dict[str, Any] = None
    ) -> None:
        """
        Actualiza el estado del allocator tras observar un resultado.
        
        Args:
            variant_id: ID de la variante que recibió el resultado
            reward: Recompensa observada (1.0 = conversión, 0.0 = no conversión)
            context: Contexto opcional
        
        🎓 APRENDIZAJE EN LÍNEA:
        ───────────────────────
        Esta función permite que el allocator "aprenda" de cada interacción.
        Con cada conversión, actualiza sus "creencias" sobre qué variante es mejor.
        """
        pass
    
    def get_state(self) -> Dict[str, Any]:
        """
        Obtiene el estado interno del allocator.
        
        Útil para:
        - Persistencia (guardar en DB)
        - Debugging
        - Auditoría
        """
        return {}
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """
        Restaura el estado interno del allocator.
        
        Usado al reiniciar el servidor para continuar desde donde estaba.
        """
        pass
```

---

### 2️⃣ `bayesian.py` - Thompson Sampling

**Propósito**: Implementación principal del algoritmo Thompson Sampling.

```python
# engine/core/allocators/bayesian.py

"""
Thompson Sampling - El algoritmo estrella de Samplit.

🎓 ¿QUÉ ES THOMPSON SAMPLING?
────────────────────────────
Un algoritmo de Multi-Armed Bandit que balancea EXPLORACIÓN vs EXPLOTACIÓN.

Imagina un casino con 3 máquinas tragaperras:
- No sabes cuál paga mejor
- Cada jugada cuesta dinero
- ¿Cómo maximizas ganancias?

Estrategias:
1. EXPLORAR: Probar todas por igual para aprender → Lento
2. EXPLOTAR: Solo jugar la que parece mejor → Arriesgado (quizás no es la mejor)
3. THOMPSON SAMPLING: Balance inteligente → Óptimo

Cómo funciona:
1. Cada variante tiene una "creencia" modelada como distribución Beta
2. Muestreamos un valor de cada distribución
3. Elegimos la variante con el mayor valor muestreado
4. Observamos resultado y actualizamos creencias

La magia: Variantes con más incertidumbre tienen más probabilidad
de ser elegidas (exploración), pero variantes que funcionan bien
también tienen alta probabilidad (explotación).
"""

import numpy as np
from typing import List, Dict, Any, Optional
import logging
from ._base import BaseAllocator

logger = logging.getLogger(__name__)


class BayesianAllocator(BaseAllocator):
    """
    Thompson Sampling con distribución Beta.
    
    🎓 DISTRIBUCIÓN BETA:
    ────────────────────
    - Describe la probabilidad de un evento binario (éxito/fracaso)
    - Parámetros: α (alpha) y β (beta)
    - α = número de éxitos + 1
    - β = número de fracasos + 1
    
    Propiedades:
    - Media = α / (α + β)
    - A más datos → Distribución más "apretada" (menos incertidumbre)
    - Al inicio (α=1, β=1) → Distribución uniforme (máxima incertidumbre)
    
    Ejemplo visual:
    
    Pocos datos (α=3, β=7):
            ▂▃▄▅▆▇█▇▆▅▄▃▂
        0%  10% 20% 30% 40%   ← Amplio rango de posibilidades
    
    Muchos datos (α=30, β=70):
              ▂▄█▄▂
        0%  10% 20% 30% 40%   ← Más certeza sobre el valor real
    """
    
    def __init__(
        self,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
        min_samples: int = 0
    ):
        """
        Inicializa el allocator.
        
        Args:
            prior_alpha: Prior α (default 1.0 = uniforme)
            prior_beta: Prior β (default 1.0 = uniforme)
            min_samples: Mínimo de muestras antes de optimizar
                         (útil si quieres fase inicial 50/50)
        
        🎓 ¿QUÉ SON LOS PRIORS?
        ─────────────────────
        Los priors representan tu "creencia inicial" antes de ver datos.
        
        prior_alpha=1, prior_beta=1 → "No sé nada" (uniforme)
        prior_alpha=10, prior_beta=10 → "Creo que CR ~50%, pero no estoy seguro"
        prior_alpha=1, prior_beta=9 → "Creo que CR ~10%"
        
        En general, priors uniformes (1,1) son la opción más neutral.
        """
        self.prior_alpha = prior_alpha
        self.prior_beta = prior_beta
        self.min_samples = min_samples
        
        # Estado interno: estadísticas por variante
        self._variant_stats: Dict[str, Dict[str, float]] = {}
    
    def select(
        self,
        variants: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Selecciona una variante usando Thompson Sampling.
        
        🎓 ALGORITMO PASO A PASO:
        ────────────────────────
        
        1. Para cada variante, calculamos α y β:
           α = conversiones + prior_alpha
           β = (visitas - conversiones) + prior_beta
        
        2. Muestreamos un valor de Beta(α, β):
           sample ~ Beta(α, β)
        
        3. Elegimos la variante con el sample más alto
        
        Ejemplo con 3 variantes:
        
        Variante A: 100 visitas, 8 conversiones
          α = 8 + 1 = 9
          β = 92 + 1 = 93
          Sample: 0.07 (sacado de Beta(9, 93))
        
        Variante B: 100 visitas, 12 conversiones
          α = 12 + 1 = 13
          β = 88 + 1 = 89
          Sample: 0.15 (sacado de Beta(13, 89))
        
        Variante C: 50 visitas, 5 conversiones (menos datos)
          α = 5 + 1 = 6
          β = 45 + 1 = 46
          Sample: 0.18 (mayor incertidumbre → más variabilidad)
        
        → Elegimos C (0.18 > 0.15 > 0.07)
        
        Nota: C tiene menos datos, así que su sample puede ser muy alto
        o muy bajo. Esto es la EXPLORACIÓN automática.
        """
        
        if not variants:
            raise ValueError("No variants provided")
        
        # Caso especial: pocas muestras → distribución uniforme
        total_samples = sum(v.get('total_allocations', 0) for v in variants)
        if total_samples < self.min_samples:
            # Selección aleatoria uniforme (exploración pura)
            return np.random.choice(variants)
        
        # Thompson Sampling
        samples = []
        
        for variant in variants:
            variant_id = variant.get('id')
            allocations = variant.get('total_allocations', 0)
            conversions = variant.get('total_conversions', 0)
            
            # Calcular parámetros Beta
            alpha = conversions + self.prior_alpha
            beta = (allocations - conversions) + self.prior_beta
            
            # Validar parámetros (deben ser > 0)
            alpha = max(alpha, 0.01)
            beta = max(beta, 0.01)
            
            # Muestrear de la distribución Beta
            sample = np.random.beta(alpha, beta)
            
            samples.append({
                'variant': variant,
                'sample': sample,
                'alpha': alpha,
                'beta': beta,
                'expected_cr': alpha / (alpha + beta)  # Media de la distribución
            })
            
            logger.debug(
                f"Variante {variant.get('name')}: "
                f"α={alpha:.1f}, β={beta:.1f}, "
                f"E[CR]={alpha/(alpha+beta):.3f}, "
                f"sample={sample:.4f}"
            )
        
        # Seleccionar variante con mayor sample
        winner = max(samples, key=lambda x: x['sample'])
        
        logger.debug(f"Variante seleccionada: {winner['variant'].get('name')}")
        
        return winner['variant']
    
    def update(
        self,
        variant_id: str,
        reward: float,
        context: Dict[str, Any] = None
    ) -> None:
        """
        Actualiza estadísticas tras observar un resultado.
        
        🎓 APRENDIZAJE BAYESIANO:
        ───────────────────────
        Cada observación actualiza nuestra "creencia" sobre la variante.
        
        Si reward=1 (conversión): α aumenta → Mayor probabilidad estimada
        Si reward=0 (no conversión): β aumenta → Menor probabilidad estimada
        
        Esto es el "Bayesian posterior update":
        Prior: Beta(α, β)
        + Observación
        = Posterior: Beta(α + reward, β + (1 - reward))
        """
        
        if variant_id not in self._variant_stats:
            self._variant_stats[variant_id] = {
                'alpha': self.prior_alpha,
                'beta': self.prior_beta,
                'total_samples': 0,
                'total_rewards': 0
            }
        
        stats = self._variant_stats[variant_id]
        stats['total_samples'] += 1
        stats['total_rewards'] += reward
        
        # Actualizar parámetros Beta
        if reward > 0:
            stats['alpha'] += reward
        else:
            stats['beta'] += (1 - reward)
        
        logger.debug(
            f"Updated variant {variant_id}: "
            f"α={stats['alpha']:.1f}, β={stats['beta']:.1f}"
        )
    
    def get_variant_probability(
        self,
        variant: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calcula estadísticas de probabilidad para una variante.
        
        Returns:
            {
                "expected_cr": 0.085,      # Tasa de conversión esperada
                "ci_lower": 0.065,         # Intervalo de confianza inferior
                "ci_upper": 0.110,         # Intervalo de confianza superior
                "uncertainty": 0.045       # Ancho del intervalo (incertidumbre)
            }
        """
        from scipy import stats as scipy_stats
        
        allocations = variant.get('total_allocations', 0)
        conversions = variant.get('total_conversions', 0)
        
        alpha = conversions + self.prior_alpha
        beta = (allocations - conversions) + self.prior_beta
        
        # Media de la distribución Beta
        expected_cr = alpha / (alpha + beta)
        
        # Intervalo de credibilidad del 95% (equivalente Bayesiano al CI)
        ci_lower = scipy_stats.beta.ppf(0.025, alpha, beta)
        ci_upper = scipy_stats.beta.ppf(0.975, alpha, beta)
        
        return {
            "expected_cr": round(expected_cr, 4),
            "ci_lower": round(ci_lower, 4),
            "ci_upper": round(ci_upper, 4),
            "uncertainty": round(ci_upper - ci_lower, 4),
            "alpha": alpha,
            "beta": beta
        }
    
    def calculate_win_probability(
        self,
        variants: List[Dict[str, Any]],
        n_simulations: int = 10000
    ) -> Dict[str, float]:
        """
        Calcula la probabilidad de que cada variante sea la mejor.
        
        🎓 SIMULACIÓN MONTE CARLO:
        ─────────────────────────
        1. Simulamos N "mundos posibles"
        2. En cada mundo, muestreamos de cada distribución Beta
        3. Contamos en cuántos mundos gana cada variante
        4. win_probability = victorias / N
        
        Ejemplo con N=10,000:
        - Variante A gana en 3,200 mundos → 32% prob de ser mejor
        - Variante B gana en 6,800 mundos → 68% prob de ser mejor
        
        Args:
            variants: Lista de variantes con estadísticas
            n_simulations: Número de simulaciones (más = más preciso)
        
        Returns:
            {"var-1": 0.32, "var-2": 0.68}
        """
        
        n_variants = len(variants)
        if n_variants == 0:
            return {}
        
        # Preparar parámetros
        alphas = []
        betas = []
        variant_ids = []
        
        for v in variants:
            allocations = v.get('total_allocations', 0)
            conversions = v.get('total_conversions', 0)
            
            alphas.append(conversions + self.prior_alpha)
            betas.append((allocations - conversions) + self.prior_beta)
            variant_ids.append(v.get('id'))
        
        # Generar muestras (matriz n_simulations x n_variants)
        samples = np.zeros((n_simulations, n_variants))
        for i in range(n_variants):
            samples[:, i] = np.random.beta(alphas[i], betas[i], n_simulations)
        
        # Encontrar ganador en cada simulación
        winners = np.argmax(samples, axis=1)
        
        # Contar victorias
        win_counts = np.bincount(winners, minlength=n_variants)
        win_probs = win_counts / n_simulations
        
        return {
            variant_ids[i]: round(float(win_probs[i]), 4)
            for i in range(n_variants)
        }
    
    def get_state(self) -> Dict[str, Any]:
        """Serializa el estado para persistencia."""
        return {
            'prior_alpha': self.prior_alpha,
            'prior_beta': self.prior_beta,
            'min_samples': self.min_samples,
            'variant_stats': self._variant_stats
        }
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """Restaura el estado desde persistencia."""
        self.prior_alpha = state.get('prior_alpha', 1.0)
        self.prior_beta = state.get('prior_beta', 1.0)
        self.min_samples = state.get('min_samples', 0)
        self._variant_stats = state.get('variant_stats', {})
```

---

### 3️⃣ `sequential.py` - A/B Testing Clásico

**Propósito**: Allocator simple para A/B testing tradicional (sin optimización).

```python
# engine/core/allocators/sequential.py

"""
Sequential Allocator - A/B Testing clásico.

🎓 ¿CUÁNDO USAR ESTO EN VEZ DE THOMPSON SAMPLING?
─────────────────────────────────────────────────
Thompson Sampling es casi siempre mejor, PERO:

1. Tests cortos (< 1 semana): No hay tiempo para que TS aprenda
2. Requisitos de muestra iguales: Si necesitas exactamente 50/50
3. Comparación con históricos: Si quieres comparar con datos anteriores
4. Regulaciones: Algunos sectores requieren distribución uniforme

En la práctica, ~95% de los experimentos deberían usar Thompson Sampling.
"""

import random
from typing import List, Dict, Any
from ._base import BaseAllocator


class SequentialAllocator(BaseAllocator):
    """
    Distribución uniforme (round-robin ponderado).
    
    Cada variante tiene un "peso" y la distribución es proporcional.
    Peso 1:1 → 50/50
    Peso 2:1 → 66/33
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Args:
            weights: Pesos por variante {"var-1": 1.0, "var-2": 1.0}
                     Si None, distribución uniforme
        """
        self.weights = weights or {}
    
    def select(
        self,
        variants: List[Dict[str, Any]],
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Selecciona variante con distribución ponderada.
        
        🎓 ALGORITMO:
        ────────────
        1. Asignar pesos (default = 1.0 para todos)
        2. Normalizar pesos a probabilidades
        3. Selección aleatoria ponderada
        """
        
        if not variants:
            raise ValueError("No variants provided")
        
        # Obtener pesos
        weights = []
        for v in variants:
            variant_id = v.get('id')
            weight = self.weights.get(variant_id, 1.0)
            weights.append(weight)
        
        # Normalizar a probabilidades
        total_weight = sum(weights)
        if total_weight == 0:
            probabilities = [1/len(variants)] * len(variants)
        else:
            probabilities = [w / total_weight for w in weights]
        
        # Selección aleatoria ponderada
        cumulative = 0
        r = random.random()
        
        for i, prob in enumerate(probabilities):
            cumulative += prob
            if r <= cumulative:
                return variants[i]
        
        # Fallback (no debería llegar aquí)
        return variants[-1]
    
    def update(
        self,
        variant_id: str,
        reward: float,
        context: Dict[str, Any] = None
    ) -> None:
        """
        No hace nada - este allocator no aprende.
        
        🎓 DIFERENCIA CLAVE CON THOMPSON SAMPLING:
        ─────────────────────────────────────────
        SequentialAllocator: Distribución fija, no cambia
        BayesianAllocator: Aprende y adapta la distribución
        """
        pass  # Este allocator no aprende
```

---

## 🔢 Comparación de Algoritmos

| Aspecto | Sequential (A/B clásico) | Thompson Sampling |
|---------|-------------------------|-------------------|
| **Distribución** | Fija (ej: 50/50) | Dinámica (aprende) |
| **Exploración** | Ninguna | Automática |
| **Explotación** | Ninguna | Automática |
| **Velocidad de aprendizaje** | N/A | Rápida |
| **Regret** | Alto | Bajo |
| **Cuándo usar** | Tests cortos, regulación | Siempre que sea posible |

🎓 **"Regret"**: Pérdida acumulada por no mostrar siempre la mejor variante.
Thompson Sampling minimiza el regret al balancear exploración y explotación.

---

## 📊 Ejemplo Práctico

```python
# Ejemplo de uso del motor

from engine.core.allocators.bayesian import BayesianAllocator

# Crear allocator
allocator = BayesianAllocator()

# Datos de variantes
variants = [
    {"id": "var-1", "name": "Control", "total_allocations": 1000, "total_conversions": 80},
    {"id": "var-2", "name": "Variante B", "total_allocations": 1000, "total_conversions": 120},
]

# Seleccionar variante para un visitante
selected = allocator.select(variants)
print(f"Mostrar: {selected['name']}")

# Calcular probabilidades de ganar
win_probs = allocator.calculate_win_probability(variants)
print(f"Prob de ganar: {win_probs}")
# Output: {"var-1": 0.02, "var-2": 0.98}
```

---

## 📚 Recursos Adicionales

Para profundizar en la teoría:

1. **Thompson Sampling Tutorial**: [Google Research Paper](https://arxiv.org/abs/1707.02038)
2. **Multi-Armed Bandits Book**: "Bandit Algorithms" by Lattimore & Szepesvári
3. **Beta Distribution**: [Interactive Visualization](https://seeing-theory.brown.edu/)

**Próximo paso**: [Ver Scripts de Mantenimiento](./scripts.md)

