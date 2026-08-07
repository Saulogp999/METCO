import streamlit as st
import numpy as np
import pandas as pd
from scipy.optimize import differential_evolution, minimize

# --- CONFIGURACIÓN DE PÁGINA MÓVIL ---
st.set_page_config(
    page_title="Cotizador & Blend - CUNI",
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
    .status-good { color: #16A34A; font-weight: bold; }
    .status-bad { color: #DC2626; font-weight: bold; }
    div[data-testid="stMetricValue"] { font-size: 20px !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">⚒️ Cotizador & Blend de Minerales (CUNI)</div>', unsafe_allow_html=True)

# --- TABLA DE PAGABLES DE CUNI (ACTUALIZADA: Cu Mínimo 4% -> 75% Pagable) ---
def get_pagables(au_pond, ag_pond, cu_pond):
    # Au (g/t)
    if au_pond < 1.01: p_au = 0.0
    elif au_pond <= 1.50: p_au = 0.60
    elif au_pond <= 2.00: p_au = 0.69
    else: p_au = 0.75
    
    # Ag (g/t)
    if ag_pond <= 100: p_ag = 0.0
    elif ag_pond <= 120: p_ag = 0.50
    elif ag_pond <= 150: p_ag = 0.60
    elif ag_pond <= 199: p_ag = 0.65
    elif ag_pond <= 300: p_ag = 0.72
    else: p_ag = 0.75
    
    # Cu (%) - Límite mínimo 4% (0.04 decimal) para obtener pagable (75%)
    cu_dec = cu_pond / 100.0 if cu_pond > 1.0 else cu_pond
    if cu_dec < 0.040: p_cu = 0.0
    elif cu_dec <= 0.0550: p_cu = 0.75
    elif cu_dec <= 0.0700: p_cu = 0.78
    else: p_cu = 0.81
    
    return p_au, p_ag, p_cu

# --- VALORIZACIÓN INDIVIDUAL DE UN LOTE (COTIZACIÓN INTERNA) ---
def calcular_valor_interno_lote(au, ag, cu, as_pct, kitco_au, kitco_ag, kitco_cu, flete_usd, maquila_usd):
    p_au, p_ag, p_cu = get_pagables(au, ag, cu)
    
    cu_dec = cu / 100.0 if cu > 1.0 else cu
    
    parcial_au = au * min(p_au, 0.75) * kitco_au / 31.1035
    parcial_ag = ag * min(p_ag, 0.75) * kitco_ag / 31.1035
    parcial_cu = cu_dec * min(p_cu, 0.75) * kitco_cu
    
    # Penalizaciones por Arsénico (%)
    as_val = as_pct
    if as_val < 3.0:
        pen_as1 = 0
    elif as_val > 3.5:
        pen_as1 = 25
    else:
        pen_as1 = (as_val - 3.0) / 0.1 * 5
        
    pen_as2 = (as_val - 3.5) / 0.1 * 8 if (as_val - 3.5) / 0.1 * 8 > 0 else 0
    pen_as = pen_as1 + pen_as2
    
    t11 = parcial_au + parcial_ag + parcial_cu - pen_as
    
    # Valor Neto / Ton comercial
    valor_neto = (t11 - maquila_usd) * 0.99 # 1% merma
    cuni = 15.0 * 1.18 # 17.70 USD/t
    
    valor_interno = valor_neto - flete_usd - cuni
    return valor_interno

# --- MOTOR DE CÁLCULO MEZCLA TOTAL ---
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
    
    # Cu (%)
    cu_arr = df_lotes['Cu (%)'].values
    cu_dec = np.where(cu_arr > 1.0, cu_arr / 100.0, cu_arr)
    cu_pond_dec = np.sum(weights * cu_dec) / peso_total
    cu_pond_pct = cu_pond_dec * 100.0
    
    # As (%) - Porcentaje directo
    as_arr = df_lotes['As (%)'].values
    as_pond_pct = np.sum(weights * as_arr) / peso_total
    
    p_au, p_ag, p_cu = get_pagables(au_pond, ag_pond, cu_pond_pct)
    
    parcial_au = au_pond * min(p_au, 0.75) * kitco_au / 31.1035
    parcial_ag = ag_pond * min(p_ag, 0.75) * kitco_ag / 31.1035
    parcial_cu = cu_pond_dec * min(p_cu, 0.75) * kitco_cu
    
    # Penalizaciones As
    if as_pond_pct < 3.0: pen_as1 = 0
    elif as_pond_pct > 3.5: pen_as1 = 25
    else: pen_as1 = (as_pond_pct - 3.0) / 0.1 * 5
    pen_as2 = (as_pond_pct - 3.5) / 0.1 * 8 if (as_pond_pct - 3.5) / 0.1 * 8 > 0 else 0
    pen_as = pen_as1 + pen_as2
    
    t11 = parcial_au + parcial_ag + parcial_cu - pen_as
    
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
        'cu_pond': cu_pond_pct,
        'as_pond': as_pond_pct,
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
    cu_obj = st.number_input("Cu Mínimo (%)", value=4.0, step=0.1)
    as_max = st.number_input("As Máximo (%)", value=2.5, step=0.1)
    min_ton = st.number_input("Tanda Mínima (t)", value=10.0, step=5.0)

# --- INICIALIZACIÓN DE DATOS DE LOTES EN SESSION STATE ---
if 'df_lotes' not in st.session_state:
    st.session_state.df_lotes = pd.DataFrame([
        {"Lote": "CARRO 1", "Peso Max (t)": 33.77, "Au (g/t)": 3.43, "Ag (g/t)": 333.0, "Cu (%)": 4.54, "As (%)": 0.010, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 2", "Peso Max (t)": 46.08, "Au (g/t)": 3.19, "Ag (g/t)": 325.0, "Cu (%)": 4.54, "As (%)": 0.010, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 3", "Peso Max (t)": 28.69, "Au (g/t)": 3.07, "Ag (g/t)": 311.0, "Cu (%)": 4.63, "As (%)": 0.010, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 4", "Peso Max (t)": 33.90, "Au (g/t)": 3.60, "Ag (g/t)": 318.0, "Cu (%)": 4.47, "As (%)": 0.010, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 5", "Peso Max (t)": 35.30, "Au (g/t)": 3.13, "Ag (g/t)": 363.0, "Cu (%)": 4.79, "As (%)": 0.010, "Precio ($/t)": 1100.0},
        {"Lote": "CARRO 6", "Peso Max (t)": 37.28, "Au (g/t)": 3.37, "Ag (g/t)": 304.0, "Cu (%)": 4.60, "As (%)": 0.010, "Precio ($/t)": 1100.0},
    ])

# --- INGRESO DE LOTES ---
st.subheader("📦 Registro de Lotes")
st.caption("ℹ️ *Edita directamente los valores en la tabla. Para añadir o quitar lotes usa las opciones explícitas abajo.*")

# Editor con num_rows="fixed" para prevenir filas vacías involuntarias
edited_df = st.data_editor(
    st.session_state.df_lotes,
    num_rows="fixed",
    use_container_width=True,
    key="editor_lotes"
)
st.session_state.df_lotes = edited_df

# --- SECCIÓN EXPANDIBLE CON CONFIRMACIÓN PARA AÑADIR O ELIMINAR FILAS ---
with st.expander("➕ / 🗑️ Añadir o Eliminar Lotes (Gestión de Filas)", expanded=False):
    tab_add, col_del = st.tabs(["➕ Agregar Nuevo Lote", "🗑️ Eliminar Lote"])
    
    with tab_add:
        st.write("**Ingresa los datos del nuevo lote y confirma:**")
        ca1, ca2, ca3 = st.columns(3)
        num_lotes = len(st.session_state.df_lotes) + 1
        nuevo_nombre = ca1.text_input("Nombre del Lote", value=f"CARRO {num_lotes}")
        nuevo_peso = ca2.number_input("Peso Max (t)", value=20.0, step=1.0)
        nuevo_au = ca3.number_input("Au (g/t)", value=3.20, step=0.1)
        
        ca4, ca5, ca6, ca7 = st.columns(4)
        nuevo_ag = ca4.number_input("Ag (g/t)", value=320.0, step=10.0)
        nuevo_cu = ca5.number_input("Cu (%)", value=4.50, step=0.1)
        nuevo_as = ca6.number_input("As (%)", value=0.01, step=0.005, format="%.3f")
        nuevo_precio = ca7.number_input("Precio ($/t)", value=1100.0, step=50.0)
        
        if st.button("✅ Confirmar y Agregar Lote", type="primary"):
            nueva_fila = pd.DataFrame([{
                "Lote": nuevo_nombre,
                "Peso Max (t)": nuevo_peso,
                "Au (g/t)": nuevo_au,
                "Ag (g/t)": nuevo_ag,
                "Cu (%)": nuevo_cu,
                "As (%)": nuevo_as,
                "Precio ($/t)": nuevo_precio
            }])
            st.session_state.df_lotes = pd.concat([st.session_state.df_lotes, nueva_fila], ignore_index=True)
            if 'opt_weights' in st.session_state:
                del st.session_state.opt_weights
            st.success(f"¡Lote '{nuevo_nombre}' agregado correctamente!")
            st.rerun()

    with col_del:
        if len(st.session_state.df_lotes) > 1:
            lote_a_eliminar = st.selectbox("Selecciona el lote a eliminar", st.session_state.df_lotes["Lote"].tolist())
            if st.button("🔴 Confirmar Eliminación de Lote"):
                st.session_state.df_lotes = st.session_state.df_lotes[st.session_state.df_lotes["Lote"] != lote_a_eliminar].reset_index(drop=True)
                if 'opt_weights' in st.session_state:
                    del st.session_state.opt_weights
                st.warning(f"Lote '{lote_a_eliminar}' eliminado.")
                st.rerun()
        else:
            st.info("Debe haber al menos 1 lote en la lista.")

# --- EVALUACIÓN DE COTIZACIONES INTERNAS INDIVIDUALES ---
st.write("### 📊 Evaluación de Precios de Compra vs. Cotización Interna")

df_eval_precios = edited_df.dropna().copy()
if len(df_eval_precios) > 0:
    cotiz_internas = []
    dif_precios = []
    estados = []
    
    for _, row in df_eval_precios.iterrows():
        val_int = calcular_valor_interno_lote(
            row["Au (g/t)"], row["Ag (g/t)"], row["Cu (%)"], row["As (%)"],
            kitco_au, kitco_ag, kitco_cu, flete_usd, maquila_usd
        )
        cotiz_internas.append(np.round(val_int, 2))
        
        p_compra = row["Precio ($/t)"]
        dif = val_int - p_compra
        dif_precios.append(np.round(dif, 2))
        
        if dif >= 0:
            estados.append(f"🟢 Por debajo (-${abs(dif):.2f}/t favorable)")
        else:
            estados.append(f"🔴 Por encima (+${abs(dif):.2f}/t sobreprecio)")
            
    df_eval_precios["Cotiz. Interna ($/t)"] = cotiz_internas
    df_eval_precios["Diferencia ($/t)"] = dif_precios
    df_eval_precios["Evaluación de Compra"] = estados
    
    st.dataframe(
        df_eval_precios[["Lote", "Precio ($/t)", "Cotiz. Interna ($/t)", "Diferencia ($/t)", "Evaluación de Compra"]],
        use_container_width=True
    )

# --- BOTÓN OPTIMIZAR SOLVER ---
col_b1, col_b2 = st.columns([1, 1])
with col_b1:
    btn_optimizar = st.button("⚡ CALCULAR MEZCLA ÓPTIMA (SOLVER)", type="primary", use_container_width=True)
with col_b2:
    if st.button("🔄 Cargar Lotes Ejemplo", use_container_width=True):
        st.session_state.df_lotes = pd.DataFrame([
            {"Lote": "CARRO 1", "Peso Max (t)": 33.77, "Au (g/t)": 3.43, "Ag (g/t)": 333.0, "Cu (%)": 4.54, "As (%)": 0.010, "Precio ($/t)": 1100.0},
            {"Lote": "CARRO 2", "Peso Max (t)": 46.08, "Au (g/t)": 3.19, "Ag (g/t)": 325.0, "Cu (%)": 4.54, "As (%)": 0.010, "Precio ($/t)": 1100.0},
            {"Lote": "CARRO 3", "Peso Max (t)": 28.69, "Au (g/t)": 3.07, "Ag (g/t)": 311.0, "Cu (%)": 4.63, "As (%)": 0.010, "Precio ($/t)": 1100.0},
        ])
        if 'opt_weights' in st.session_state:
            del st.session_state.opt_weights
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

# --- RESULTADOS MEZCLA ---
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
        
    st.write("### 🧪 Leyes Resultantes de la Carga")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Au (g/t)", f"{eval_res['au_pond']:.2f}", "✅" if eval_res['au_pond']>=au_obj else "❌")
    k2.metric("Ag (g/t)", f"{eval_res['ag_pond']:.1f}", "✅" if eval_res['ag_pond']>=ag_obj else "❌")
    k3.metric("Cu (%)", f"{eval_res['cu_pond']:.2f}%", "✅" if eval_res['cu_pond']>=cu_obj else "❌")
    k4.metric("As (%)", f"{eval_res['as_pond']:.3f}%", "✅" if eval_res['as_pond']<=as_max else "❌")
        
    st.write("### 📋 Detalle de Carga por Lote")
    df_rec = edited_df.copy()
    df_rec["Usar (Toneladas)"] = np.round(weights, 2)
    df_rec["% Lote"] = np.round((weights / df_rec["Peso Max (t)"]) * 100, 1)
    df_rec["Costo ($)"] = np.round(weights * df_rec["Precio ($/t)"], 2)
    
    st.dataframe(
        df_rec[["Lote", "Peso Max (t)", "Usar (Toneladas)", "% Lote", "Au (g/t)", "Ag (g/t)", "Cu (%)", "As (%)", "Costo ($)"]],
        use_container_width=True
    )

import pandas as pd
import streamlit as st

# ==========================================
# 1. CONTROLES DE PRECIOS DE MINERALES
# ==========================================
st.sidebar.header("Cotización de Minerales")
precio_au = st.sidebar.number_input("Oro (Au) - US$/oz", value=2400.00, step=10.0, format="%.2f")
precio_ag = st.sidebar.number_input("Plata (Ag) - US$/oz", value=28.50, step=0.5, format="%.2f")
precio_cu = st.sidebar.number_input("Cobre (Cu) - US$/MT", value=9000.00, step=50.0, format="%.2f")

st.title("Evaluación y Liquidación de Lotes")

# ==========================================
# 3. REGISTRO DE LOTES (REACTIVIDAD Y EDITABLE)
# ==========================================
st.subheader("Registro de Lotes")

# Estructura inicial de la tabla si no existe en sesión
if "df_lotes" not in st.session_state:
    st.session_state.df_lotes = pd.DataFrame({
        "Lote": ["Lote-01"],
        "Peso_TMS": [10.00],
        "Ley_Au_oz_TC": [0.45],
        "Ley_Ag_oz_TC": [2.50],
        "Ley_Cu_pct": [0.80],
        "Ensayo_As_pct": [1.50],  # 5. Arsénico en Porcentaje
        "Precio_Ofrecido_USD": [1200.00]
    })

# Editor interactivo de datos
df_editado = st.data_editor(
    st.session_state.df_lotes,
    num_rows="dynamic",
    key="editor_registro_lotes",
    use_container_width=True
)

# Reconversión estricta de tipos numéricos para garantizar reactividad
columnas_numericas = ["Peso_TMS", "Ley_Au_oz_TC", "Ley_Ag_oz_TC", "Ley_Cu_pct", "Ensayo_As_pct", "Precio_Ofrecido_USD"]
for col in columnas_numericas:
    df_editado[col] = pd.to_numeric(df_editado[col], errors="coerce").fillna(0.0)

# Guardar cambios en el estado
st.session_state.df_lotes = df_editado.copy()

# ==========================================
# 2. CÁLCULO Y EVALUACIÓN DE COMPRA (SEMÁFORO)
# ==========================================
def calcular_evaluacion(row):
    # Cálculo simulado del Valor Neto / Precio Máximo a Pagar por el Lote
    val_au = row["Peso_TMS"] * row["Ley_Au_oz_TC"] * (precio_au * 0.85)
    val_ag = row["Peso_TMS"] * row["Ley_Ag_oz_TC"] * (precio_ag * 0.80)
    
    precio_maximo_compra = val_au + val_ag
    
    # Margen a favor = Techo Máximo - Precio Acordado/Ofrecido
    margen_favor = precio_maximo_compra - row["Precio_Ofrecido_USD"]
    
    if margen_favor >= 0:
        estado_semaforo = "Por debajo del techo"
        color = "🟢"
    else:
        estado_semaforo = "Por encima del techo"
        color = "🔴"
        
    return pd.Series([precio_maximo_compra, margen_favor, f"{color} {estado_semaforo}"])

# Ejecución de evaluaciones si hay lotes registrados
if not df_editado.empty:
    evaluaciones = df_editado.apply(calcular_evaluacion, axis=1)
    evaluaciones.columns = ["Precio_Maximo_Compra_USD", "Margen_A_Favor_USD", "Semaforo"]
    
    # Combinar resultados
    df_resultados = pd.concat([df_editado, evaluaciones], axis=1)

    # ==========================================
    # 5. FORMATO DE VISUALIZACIÓN Y ARSÉNICO (%)
    # ==========================================
    st.subheader("Evaluación de Compra")
    
    df_mostrar = df_resultados.copy()
    
    # Formateo visual
    df_mostrar["Ensayo_As_pct"] = df_mostrar["Ensayo_As_pct"].map("{:.2f}%".format)
    df_mostrar["Precio_Maximo_Compra_USD"] = df_mostrar["Precio_Maximo_Compra_USD"].map("$ {:.2f}".format)
    df_mostrar["Margen_A_Favor_USD"] = df_mostrar["Margen_A_Favor_USD"].map("$ {:.2f}".format)
    df_mostrar["Precio_Ofrecido_USD"] = df_mostrar["Precio_Ofrecido_USD"].map("$ {:.2f}".format)

    st.dataframe(
        df_mostrar[[
            "Lote", "Peso_TMS", "Ensayo_As_pct", 
            "Precio_Ofrecido_USD", "Precio_Maximo_Compra_USD", 
            "Margen_A_Favor_USD", "Semaforo"
        ]],
        use_container_width=True
    )

