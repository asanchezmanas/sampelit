# Estructura Corporativa y Tributación

Guía sobre la optimización legal y fiscal para Samplit.

---

## 🏛️ El Modelo de Holding

La estructura más recomendada para un negocio de software con visión de inversión a largo plazo es la **Holding por encima**.

### Diagrama de Estructura
```
      ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
      ┃      HOLDING COMPANY        ┃  <-- Tú eres el dueño aquí
      ┃    (Acumula patrimonio)     ┃
      ┗━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┛
                           ┃
            ┏━━━━━━━━━━━━━━┻━━━━━━━━━━━━━━┓
            ┃      OPERATING COMPANY     ┃  <-- Samplit (Riesgos, clientes)
            ┃       (Genera cash)        ┃
            ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### Ventajas de una Holding
1. **Separación de Riesgos**: Si la operativa tiene un problema legal o técnico grave, el dinero que ya has subido a la holding está legalmente protegido.
2. **Diferimiento Fiscal**: Puedes mover beneficios de la operativa a la holding para reinvertir en otros activos (ETFs, inmuebles) sin pagar IRPF personal (solo pagas el Impuesto de Sociedades, que suele ser mucho menor).
3. **Exención por Participación**: En muchos países (como España), los dividendos de la hija a la madre están exentos en un 95% (solo tributas por el 5% restante al tipo de sociedades).
4. **Optimización del Exit**: Si algún día vendes Samplit, el dinero entra en la holding. Puedes usarlo para montar otro negocio sin que Hacienda se lleve el 20-50% en el camino al bolsillo personal.

---

## 🌍 Opciones Geográficas (Solo Founder)

### 1. España (SL + Holding)
*   **Pro**: Familiaridad, 95% exención dividendos intra-grupo, deducibilidad de gastos de I-D.
*   **Contra**: Cuota de autónomos, burocracia, impuestos sobre dividendos personales altos (19-28%).
*   **Ideal si**: Vives en España y quieres simplicidad bancaria inicial.

### 2. Estonia (e-Residency)
*   **Pro**: 0% impuesto sobre beneficios reinvertidos. Solo pagas (20/80) cuando sacas dividendos. 100% digital.
*   **Contra**: Necesitas una holding si quieres separar inversiones a largo plazo de la operativa. Si vives en España, Hacienda puede reclamar la gestión efectiva (CFC rules).
*   **Ideal si**: Eres un "digital nomad" o quieres reinvertir el 100% del beneficio en el software inicial.

### 3. Países Bajos (BV / STAK)
*   **Pro**: El "estándar" europeo para tech. Excelente exención por participación (100% exenta si >5% participación).
*   **Contra**: Costes de mantenimiento altos (gestoría, notarios).
*   **Ideal si**: Planeas levantar capital venture o escalar a niveles enterprise internacionales rápidamente.

---

## 💸 Estrategia de Tributación (Cascada)

1.  **Ingresos**: Clientes pagan a la Operativa.
2.  **Gastos Operativos**: Hosting, herramientas, marketing (se restan antes de impuestos).
3.  **Impuesto de Sociedades**: La operativa paga sobre el beneficio neto (~25% en ES).
4.  **Dividendo a la Holding**: Subes el excedente. Solo pagas un pequeño % por la gestión (efectivamente <1.25%).
5.  **Reinversión**: La holding compra ETFs/Bonos. El dinero crece "bruto" (sin pasar por IRPF).
6.  **Sueldo Personal**: Te pagas un sueldo mínimo de la holding para cubrir tus gastos vitales. Solo pagas IRPF por esa parte.

---

## ⚠️ Consideraciones de "Gestión Efectiva"

Si vives en un país de alta tributación (España, Francia, Alemania) pero montas la holding en un paraíso o país low-tax (Andorra, Estonia):
- Hacienda mirará **dónde se toman las decisiones**.
- Si tú decides todo desde tu casa en Barcelona, para ellos la empresa es española.
- **Consejo**: Mantén la estructura simple y legal en tu país de residencia hasta que el beneficio anual justifique una mudanza física de residencia.

---

## ♟️ Táctica Recomendada para el Inicio

1.  **MVP/Validación**: Autónomo o SL sencilla.
2.  **Tracción (€5k+ MRR)**: Crear la Holding y la Operativa.
3.  **Escala (€20k+ MRR)**: Optimizar vía I-D y posiblemente buscar jurisdicciones más eficientes si el tipo impositivo efectivo sube demasiado.

---

## 📋 Acciones Siguientes

- [ ] Consultar con un gestor especializado en **fiscalidad internacional**.
- [ ] Definir el país de la Holding basado en tu residencia actual.
- [ ] Configurar Stripe para que liquide a la cuenta de la Operativa.
