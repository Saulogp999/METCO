import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import minimize

# ==========================================
# CONFIGURACIÓN DE LA PÁGINA
# ==========================================
st.set_page_config(
    page_title="Cotizador y Optimizador Minero - CUNI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚖️ Cotizador y Optimizador de Liquidación Minera")
st.markdown("Herramienta para valoración de lotes de mineral/concentrado (Cu, Au, Ag, As) y optimización de mezclas (blending).")

# ==========================================
# INICIALIZACIÓN DE ESTADO (SESSION STATE)
# ==========================================
if "lotes" not in st.session_state:
    st.session_state.lotes = pd.DataFrame([
        {
            "Lote": "Lote A",
            "Toneladas (TMS)": 100.0,
            "Ley Cu (%)": 5.5,
            "Ley Au (oz/TC)": 0.15,
            "Ley Ag (oz/TC)": 2.5,
            "Arsénico (%)": 2.8,
            "Precio Compra ($/TMS)": 450.0
        },
        {
            "Lote": "Lote B",
            "Toneladas (TMS)": 150.0,
            "Ley Cu (%)": 3.8,
            "Ley Au (oz/TC)": 0.20,
            "Ley Ag (oz/TC)": 3.0,
            "Arsénico (%)": 3.6,
            "Precio Compra ($/TMS)": 380.0
        }
    ])

# ==========================================
# PARÁMETROS COMERCIALES EN SIDEBAR
# ==========================================
st.sidebar.header("📊 Cotizaciones y Parámetros")

st.sidebar.subheader("Precios de Mercado (METCO / LME)")
precio_cu = st.sidebar.number_input("Precio Cobre ($/lb)", value=4.10, step=0.05)
precio_au = st.sidebar.number_input("Precio Oro ($/oz)", value=2400.0, step=10.0)
precio_ag = st.sidebar.number_input("Precio Plata ($/oz)", value=28.0, step=0.5)

st.sidebar.subheader("Porcentajes Pagables")
st.sidebar.info("Cobre: Mínimo 4% de ley para aplicar 75% de pagable. Si es menor a 4%, el pagable es 0%.")
pagable_au_pct = st.sidebar.slider("Pagable Oro (%)", min_value=0.0, max_value=100.0, value=90.0) / 100.0
pagable_ag_pct = st.sidebar.slider("Pagable Plata (%)", min_value=0.0, max_value=100.0, value=85.0) / 100.0

st.sidebar.subheader("Deducciones y Costos ($/TMS)")
maquila_tc = st.sidebar.number_input("Maquila (TC $ / TMS)", value=120.0, step=5.0)
gastos_logisticos = st.sidebar.number_input("Gastos Logísticos ($ / TMS)", value=35.0, step=2.0)
costo_cuni = st.sidebar.number_input("Costos CUNI / Operativos ($ / TMS)", value=25.0, step=2.0)
aplica_igv = st.sidebar.checkbox("Incluir IGV (18%) en costo total", value=True)

# ==========================================
# FUNCIONES DE CÁLCULO
# ==========================================
def calcular_penalizacion_arsenico(as_pct):
    """
    Penalización escalonada para Arsénico (%):
    - As < 3.0%: $0
    - 3.0% <= As <= 3.5%: $5 por cada 0.1% sobre 3.0%
    - As > 3.5%: $25 base + $8 por cada 0.1% sobre 3.5%
    """
    if as_pct < 3.0:
        return 0.0
    elif 3.0 <= as_pct <= 3.5:
        return ((as_pct - 3.0) / 0.1) * 5.0
    else:
        return 25.0 + ((as_pct - 3.5) / 0.1) * 8.0

def calcular_pagable_cu(ley_cu):
    """
    Cobre: Mínimo 4% de ley para pagar el 75%.
    """
    if ley_cu >= 4.0:
        return 0.75
    return 0.0

def liquidar_lote(row):
    tms = row["Toneladas (TMS)"]
    ley_cu = row["Ley Cu (%)"]
    ley_au = row["Ley Au (oz/TC)"]
    ley_ag = row["Ley Ag (oz/TC)"]
    as_pct = row["Arsénico (%)"]
    precio_compra = row["Precio Compra ($/TMS)"]

    # 1. Valor Pagable de Metales por TMS
    factor_pagable_cu = calcular_pagable_cu(ley_cu)
    val_cu = (ley_cu / 100.0) * 2204.62 * factor_pagable_cu * precio_cu
    val_au = ley_au * pagable_au_pct * precio_au
    val_ag = ley_ag * pagable_ag_pct * precio_ag
    
    valor_bruto_tms = val_cu + val_au + val_ag

    # 2. Penalización por Arsénico
    penalizacion_as = calcular_penalizacion_arsenico(as_pct)

    # 3. Costos Totales de Liquidación por TMS
    costo_operativo_tms = maquila_tc + gastos_logisticos + costo_cuni + penalizacion_as
    
    # 4. Valor Neto de Liquidación por TMS
    valor_neto_tms = valor_bruto_tms - costo_operativo_tms
    if aplica_igv:
        valor_neto_tms_con_igv = valor_neto_tms * 1.18
    else:
        valor_neto_tms_con_igv = valor_neto_tms

    # 5. Evaluación de Compra (Semáforo sin confusiones de valores negativos)
    margen_bruto_tms = valor_neto_tms - precio_compra
    
    # Cálculo de margen porcentual normalizado (evita valores negativos o incongruentes)
    if valor_neto_tms > 0 and margen_bruto_tms > 0:
        pct_margen = (margen_bruto_tms / valor_neto_tms) * 100.0
    else:
        pct_margen = 0.0

    # Determinar Semáforo
    if margen_bruto_tms > 15.0:
        semaforo = "🟢 COMPRAR (Rentable)"
    elif 0.0 <= margen_bruto_tms <= 15.0:
        semaforo = "🟡 EVALUAR (Margen Bajo)"
    else:
        semaforo = "🔴 NO COMPRAR (Pérdida)"

    utilidad_total = margen_bruto_tms * tms

    return pd.Series({
        "Valor Pagable Cu ($/TMS)": round(val_cu, 2),
        "Valor Pagable Au ($/TMS)": round(val_au, 2),
        "Valor Pagable Ag ($/TMS)": round(val_ag, 2),
        "Valor Bruto ($/TMS)": round(valor_bruto_tms, 2),
        "Penalización As ($/TMS)": round(penalizacion_as, 2),
        "Valor Neto Liquidación ($/TMS)": round(valor_neto_tms, 2),
        "Margen Bruto ($/TMS)": round(margen_bruto_tms, 2),
        "Rentabilidad Est. (%)": round(pct_margen, 1),
        "Semáforo Compra": semaforo,
        "Utilidad Total ($)": round(utilidad_total, 2)
    })

# ==========================================
# SECCIÓN 1: GESTIÓN Y EDICIÓN DE LOTES
# ==========================================
st.header("📋 Gestión de Lotes")
st.markdown("Edita los valores en la tabla o añade nuevos lotes. Haz clic en guardar para aplicar cambios.")

# Editor interactivo
df_editado = st.data_editor(
    st.session_state.lotes,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_lotes"
)

col_btn1, col_btn2 = st.columns([1, 4])
with col_btn1:
    if st.button("💾 Confirmar y Guardar Cambios"):
        st.session_state.lotes = df_editado
        st.success("¡Lotes actualizados con éxito!")

# ==========================================
# SECCIÓN 2: RESULTADOS DE LIQUIDACIÓN
# ==========================================
st.header("💵 Resultado de Liquidación por Lote")

if not df_editado.empty:
    df_resultados = df_editado.apply(liquidar_lote, axis=1)
    df_completo = pd.concat([df_editado, df_resultados], axis=1)

    st.dataframe(
        df_completo[[
            "Lote", "Toneladas (TMS)", "Ley Cu (%)", "Arsénico (%)",
            "Precio Compra ($/TMS)", "Valor Neto Liquidación ($/TMS)",
            "Penalización As ($/TMS)", "Margen Bruto ($/TMS)",
            "Rentabilidad Est. (%)", "Semáforo Compra", "Utilidad Total ($)"
        ]],
        use_container_width=True
    )

    # Métricas Globales
    st.subheader("📌 Resumen Global")
    total_tms = df_completo["Toneladas (TMS)"].sum()
    utilidad_global = df_completo["Utilidad Total ($)"].sum()
    margen_promedio = utilidad_global / total_tms if total_tms > 0 else 0

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Total Toneladas (TMS)", f"{total_tms:,.2f}")
    col_m2.metric("Utilidad Proyectada Total", f"${utilidad_global:,.2f}")
    col_m3.metric("Margen Promedio", f"${margen_promedio:,.2f} / TMS")

# ==========================================
# SECCIÓN 3: OPTIMIZADOR DE MEZCLAS (BLENDING)
# ==========================================
st.header("🔄 Optimizador de Mezclas (Blending)")
st.markdown("Encuentra la proporción óptima para maximizar la utilidad reduciendo penalizaciones por Arsénico.")

with st.form("form_blending"):
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        max_as_blend = st.number_input("Ley Máxima de Arsénico permitida en mezcla (%)", value=3.0, step=0.1)
    with col_opt2:
        min_cu_blend = st.number_input("Ley Mínima de Cobre requerida en mezcla (%)", value=4.0, step=0.1)
    
    submit_opt = st.form_submit_button("🚀 Calcular Mezcla Óptima")

if submit_opt and not df_editado.empty:
    disponibles = df_editado["Toneladas (TMS)"].values
    leyes_cu = df_editado["Ley Cu (%)"].values
    leyes_as = df_editado["Arsénico (%)"].values
    utilidades_unitarias = df_resultados["Margen Bruto ($/TMS)"].values

    # Función objetivo a minimizar (negativo de la utilidad total)
    def funcion_objetivo(weights):
        return -np.sum(weights * utilidades_unitarias)

    # Restricciones
    constraints = [
        # Restricción Arsénico: sum(w_i * as_i) / sum(w_i) <= max_as_blend
        {'type': 'ineq', 'fun': lambda w: max_as_blend * np.sum(w) - np.sum(w * leyes_as)},
        # Restricción Cobre: sum(w_i * cu_i) / sum(w_i) >= min_cu_blend
        {'type': 'ineq', 'fun': lambda w: np.sum(w * leyes_cu) - min_cu_blend * np.sum(w)}
    ]

    # Límites por cada lote (0 <= toneladas_usadas <= toneladas_disponibles)
    bounds = [(0, disp) for disp in disponibles]
    x0 = disponibles / 2.0

    res = minimize(funcion_objetivo, x0, method='SLSQP', bounds=bounds, constraints=constraints)

    if res.success:
        toneladas_optimas = res.x
        df_editado_blend = df_editado.copy()
        df_editado_blend["TMS a Mezclar"] = np.round(toneladas_optimas, 2)
        
        tms_totales_blend = np.sum(toneladas_optimas)
        if tms_totales_blend > 0:
            ley_cu_prom = np.sum(toneladas_optimas * leyes_cu) / tms_totales_blend
            ley_as_prom = np.sum(toneladas_optimas * leyes_as) / tms_totales_blend
            utilidad_max = -res.fun

            st.success("✅ ¡Mezcla óptima calculada exitosamente!")
            
            st.dataframe(
                df_editado_blend[["Lote", "Toneladas (TMS)", "TMS a Mezclar", "Ley Cu (%)", "Arsénico (%)"]],
                use_container_width=True
            )

            col_b1, col_b2, col_b3 = st.columns(3)
            col_b1.metric("Toneladas Mezcladas", f"{tms_totales_blend:,.2f} TMS")
            col_b2.metric("Ley Mezcla Cu (%)", f"{ley_cu_prom:.2f}%")
            col_b3.metric("Ley Mezcla As (%)", f"{ley_as_prom:.2f}%")
            st.metric("Utilidad Máxima Proyectada de la Mezcla", f"${utilidad_max:,.2f}")
        else:
            st.warning("No es posible realizar una mezcla con los límites especificados y los lotes disponibles.")
    else:
        st.error("No se encontró una solución factible con los parámetros ingresados. Revisa los límites de Arsénico o Cobre.")
