import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize

# --- CONFIGURACIÓN DE PÁGINA MÓVIL ---
st.set_page_config(
    page_title="Mezcla Óptima - CUNI",
    page_icon="⚒️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- ESTILOS CSS PARA MÓVIL ---
st.markdown("""
<style>
    .main-header {
        font-size: 22px !important;
        font-weight: bold;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 12px;
    }
    .metric-card {
        background-color: #F0FDF4;
        border: 2px solid #22C55E;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
    }
    div[data-testid="stMetricValue"] { font-size: 22px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚒️ Cotizador & Blend de Minerales (CUNI)</div>', unsafe_allow_html=True)

# --- LÓGICA DE TABLA DE PAGABLES ---
def get_pagables(au_pond, ag_pond, cu_pond):
    # Au
    if au_pond < 1.01: p_au = 0.0
    elif au_pond <= 1.50: p_au = 0.60
    elif au_pond <= 2.00: p_au = 0.69
    else: p_au = 0.75
    
    # Ag
    if ag_pond <= 100: p_ag = 0.0
    elif ag_pond <= 120: p_ag = 0.50
    elif ag_pond <= 150: p_ag = 0.60
    elif ag_pond <= 199: p_ag = 0.65
    elif ag_pond <= 300: p_ag = 0.72
    else: p_ag = 0.75
    
    # Cu
    if cu_pond <= 0.01: p_cu = 0.0
    elif cu_pond <= 0.02: p_cu = 0.60
    elif cu_pond <= 0.0299: p_cu = 0.65
    elif cu_pond <= 0.0399: p_cu = 0.70
    elif cu_pond <= 0.0550: p_cu = 0.75
    elif cu_pond <= 0.0700: p_cu = 0.78
    else: p_cu = 0.81
    
    return p_au, p_ag, p_cu

# --- MOTOR DE CÁLCULO DE COTIZACIÓN ---
def calcular_cotizacion(weights, df_lotes, kitco_au, kitco_ag, kitco_cu, tc, flete_usd, maquila_usd):
    weights = np.array(weights)
    peso_total = np.sum(weights)
    
    if peso_total <= 1e-5:
        return {
            'peso_total': 0, 'au_pond': 0, 'ag_pond': 0, 'cu_pond': 0, 'as_pond': 0,
            'mineral_cost': 0, 'logistica': 0, 'valor_neto': 0, 'cuni': 0, 'ganancia': -1e9, 'margen': 0
        }
    
    au_pond = np.sum(weights * df_lotes['Au (g/t)']) / peso_total
    ag_pond = np.sum(weights * df_lotes['Ag (g/t)']) / peso_total
    cu_pond = np.sum(weights * df_lotes['Cu (%)'] / 100.0) / peso_total if df_lotes['Cu (%)'].max() > 1 else np.sum(weights * df_lotes['Cu (%)']) / peso_total
    as_pond = np.sum(weights * df_lotes['As (%)'] / 100.0) / peso_total if df_lotes['As (%)'].max() > 1 else np.sum(weights * df_lotes['As (%)']) / peso_total
    
    p_au, p_ag, p_cu = get_pagables(au_pond, ag_pond, cu_pond)
    
    parcial_au = au_pond * min(p_au, 0.75) * kitco_au / 31.1035
    parcial_ag = ag_pond * min(p_ag, 0.75) * kitco_ag / 31.1035
    parcial_cu = cu_pond * min(p_cu, 0.75) * kitco_cu
    
    t11 = parcial_au + parcial_ag + parcial_cu
    
    mineral_cost = np.sum(weights * df_lotes['Precio ($/t)'])
    logistica = flete_usd * peso_total
    venta_mineral = peso_total * 0.99 # 1% merma
    valor_neto = (t11 - maquila_usd) * venta_mineral
    cuni = 15 * peso_total * 1.18
    ganancia = valor_neto - cuni - mineral_cost - logistica
    margen = ganancia / valor_neto if valor_neto > 0 else 0
    
    return {
        'peso_total': peso_total,
        'au_pond': au_pond,
        'ag_pond': ag_pond,
        'cu_pond': cu_pond * 100.0 if cu_pond <= 1 else cu_pond,
        'as_pond': as_pond * 100.0 if as_pond <= 1 else as_pond,
        'mineral_cost': mineral_cost,
        'logistica': logistica,
        'valor_neto': valor_neto,
        'cuni': cuni,
        'ganancia': ganancia,
        'margen': margen
    }

# --- PARÁMETROS EN PANEL LATERAL ---
with st.sidebar:
    st.header("⚙️ Cotización & Costos")
    tc = st.number_input("T.C. (S/.)", value=3.40, step=0.01)
    kitco_au = st.number_input("Au KITCO (USD/oz)", value=4095.0, step=10.0)
    kitco_ag = st.number_input("Ag KITCO (USD/oz)", value=58.0, step=1.0)
    kitco_cu = st.number_input("Cu METCO (USD/tm)", value=13800.0, step=100.0)
    flete_usd = st.number_input("Flete Logística ($/t)", value=12.57, step=0.5)
    maquila_usd = st.number_input("Deducción Maquila ($/t)", value=70.5, step=1.0)
    
    st.header("🎯 Objetivos Mínimos")
    au_obj = st.number_input("Au Mínimo (g/t)", value=3.0, step=0.1)
    ag_obj = st.number_input("Ag Mínimo (g/t)", value=350.0, step=10.0)
    cu_obj = st.number_input("Cu Mínimo (%)", value=5.0, step=0.1)
    as_max = st.number_input("As Máximo (%)", value=2.5, step=0.1)
    min_ton = st.number_input("Tanda Mínima (t)", value=10.0, step=5.0)

# --- INGRESO DE LOTES ---
st.subheader("📦 Registro de Lotes")

if 'df_lotes' not in st.session_state:
    st.session_state.df_lotes = pd.DataFrame([
        {"Lote": "CARRO 1", "Peso Max (t)": 33.77, "Au (g/t)": 3.43, "Ag (g/t)": 333.0, "Cu (%)": 4.54, "As (%)": 0.01, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 2", "Peso Max (t)": 46.08, "Au (g/t)": 3.19, "Ag (g/t)": 325.0, "Cu (%)": 4.54, "As (%)": 0.01, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 3", "Peso Max (t)": 28.69, "Au (g/t)": 3.07, "Ag (g/t)": 311.0, "Cu (%)": 4.63, "As (%)": 0.01, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 4", "Peso Max (t)": 33.90, "Au (g/t)": 3.60, "Ag (g/t)": 318.0, "Cu (%)": 4.47, "As (%)": 0.01, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 5", "Peso Max (t)": 35.30, "Au (g/t)": 3.13, "Ag (g/t)": 363.0, "Cu (%)": 4.79, "As (%)": 0.01, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 6", "Peso Max (t)": 37.28, "Au (g/t)": 3.37, "Ag (g/t)": 304.0, "Cu (%)": 4.60, "As (%)": 0.01, "Precio ($/t)": 1100.0},
    ])

edited_df = st.data_editor(
    st.session_state.df_lotes,
    num_rows="dynamic",
    use_container_width=True,
    key="editor_lotes"
)

col_b1, col_b2 = st.columns([1, 1])
with col_b1:
    btn_optimizar = st.button("⚡ CALCULAR MEZCLA ÓPTIMA (SOLVER)", type="primary", use_container_width=True)
with col_b2:
    if st.button("🔄 Cargar Lotes Ejemplo", use_container_width=True):
        st.session_state.df_lotes = pd.DataFrame([
            {"Lote": "CARRO 1", "Peso Max (t)": 33.77, "Au (g/t)": 3.43, "Ag (g/t)": 333.0, "Cu (%)": 4.54, "As (%)": 0.01, "Precio ($/t)": 1100.0},
            {"Lote": "CARRO 2", "Peso Max (t)": 46.08, "Au (g/t)": 3.19, "Ag (g/t)": 325.0, "Cu (%)": 4.54, "As (%)": 0.01, "Precio ($/t)": 1100.0},
            {"Lote": "CARRO 3", "Peso Max (t)": 28.69, "Au (g/t)": 3.07, "Ag (g/t)": 311.0, "Cu (%)": 4.63, "As (%)": 0.01, "Precio ($/t)": 1100.0},
        ])
        st.rerun()

# --- EJECUCIÓN DEL SOLVER ---
if btn_optimizar:
    df_use = edited_df.dropna().copy()
    if len(df_use) > 0:
        bounds = [(0, row["Peso Max (t)"]) for _, row in df_use.iterrows()]
        
        def obj_func(weights):
            res = calcular_cotizacion(weights, df_use, kitco_au, kitco_ag, kitco_cu, tc, flete_usd, maquila_usd)
            if res['peso_total'] < min_ton:
                return 1e8 + (min_ton - res['peso_total']) * 1e4
            
            penalty = 0
            if res['au_pond'] < au_obj: penalty += (au_obj - res['au_pond']) * 1e6
            if res['ag_pond'] < ag_obj: penalty += (ag_obj - res['ag_pond']) * 1e5
            if res['cu_pond'] < cu_obj: penalty += (cu_obj - res['cu_pond']) * 1e6
            if res['as_pond'] > as_max: penalty += (res['as_pond'] - as_max) * 1e6
                
            return -res['ganancia'] + penalty

        res_opt = differential_evolution(obj_func, bounds, seed=42)
        opt_weights = res_opt.x
        res_fine = minimize(obj_func, opt_weights, method='SLSQP', bounds=bounds)
        if res_fine.success: opt_weights = res_fine.x
            
        st.session_state.opt_weights = np.clip(opt_weights, 0, [r["Peso Max (t)"] for _, r in df_use.iterrows()])

# --- RESULTADOS ---
if 'opt_weights' in st.session_state and len(st.session_state.opt_weights) == len(edited_df):
    weights = st.session_state.opt_weights
    eval_res = calcular_cotizacion(weights, edited_df, kitco_au, kitco_ag, kitco_cu, tc, flete_usd, maquila_usd)
    
    st.markdown("---")
    st.subheader("💡 Resultado de la Mezcla Recomendada")
    
    c1, c2 = st.columns(2)
    with c1:
        st.metric("Utilidad Neta Total", f"${eval_res['ganancia']:,.2f} USD", f"{eval_res['margen']*100:.2f}% Margen")
    with c2:
        st.metric("Peso Total Mezcla", f"{eval_res['peso_total']:.2f} t", f"Valor Neto: ${eval_res['valor_neto']:,.0f}")
        
    st.write("### 🧪 Leyes Resultantes")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Au (g/t)", f"{eval_res['au_pond']:.2f}", "✅" if eval_res['au_pond']>=au_obj else "❌")
    k2.metric("Ag (g/t)", f"{eval_res['ag_pond']:.1f}", "✅" if eval_res['ag_pond']>=ag_obj else "❌")
    k3.metric("Cu (%)", f"{eval_res['cu_pond']:.2f}%", "✅" if eval_res['cu_pond']>=cu_obj else "❌")
    k4.metric("As (%)", f"{eval_res['as_pond']:.2f}%", "✅" if eval_res['as_pond']<=as_max else "❌")
        
    st.write("### 📋 Detalle de Carga por Lote")
    df_rec = edited_df.copy()
    df_rec["Usar (Toneladas)"] = np.round(weights, 2)
    df_rec["% Lote"] = np.round((weights / df_rec["Peso Max (t)"]) * 100, 1)
    df_rec["Costo ($)"] = np.round(weights * df_rec["Precio ($/t)"], 2)
    
    st.dataframe(
        df_rec[["Lote", "Peso Max (t)", "Usar (Toneladas)", "% Lote", "Au (g/t)", "Ag (g/t)", "Cu (%)", "As (%)", "Costo ($)"]],
        use_container_width=True
    )
