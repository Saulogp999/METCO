import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import minimize

# ==========================================
# CONFIGURACIÓN PÁGINA
# ==========================================
st.set_page_config(
    page_title="Cotizador Minero y Blending - CUNI",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Cotizador Minero, Análisis de Sobreprecio y Blending Óptimo")

# Inicialización de estado para la cartera de lotes
if "lotes_comprados" not in st.session_state:
    st.session_state.lotes_comprados = []

# ==========================================
# FUNCIONES DE PAGABLES SEGÚN TABLA OFICIAL
# ==========================================
def obtener_pagable_cu(ley_cu):
    if ley_cu <= 1.0:
        return 0.0
    elif ley_cu <= 2.0:
        return 60.0
    elif ley_cu <= 3.0:
        return 65.0
    elif ley_cu < 4.0:
        return 70.0
    elif ley_cu <= 5.5:
        return 75.0
    elif ley_cu <= 7.0:
        return 78.0
    else:
        return 81.0

def obtener_pagable_ag(ley_ag_gt):
    if ley_ag_gt <= 100.0:
        return 0.0
    elif ley_ag_gt <= 120.0:
        return 50.0
    elif ley_ag_gt <= 150.0:
        return 60.0
    elif ley_ag_gt <= 199.0:
        return 65.0
    elif ley_ag_gt <= 300.0:
        return 72.0
    else:
        return 75.0

def obtener_pagable_au(ley_au_gt):
    if ley_au_gt <= 1.0:
        return 0.0
    elif ley_au_gt <= 1.5:
        return 60.0
    elif ley_au_gt <= 2.0:
        return 69.0
    else:
        return 75.0

def calcular_valor_por_tm(ley_cu, ley_au_gt, ley_ag_gt, pag_cu, pag_au, pag_ag, p_cu, p_au, p_ag):
    au_oz_tm = ley_au_gt / 31.1035
    ag_oz_tm = ley_ag_gt / 31.1035

    val_cu = (ley_cu / 100.0) * (pag_cu / 100.0) * p_cu
    val_au = au_oz_tm * (pag_au / 100.0) * p_au
    val_ag = ag_oz_tm * (pag_ag / 100.0) * p_ag

    return val_cu + val_au + val_ag

# ==========================================
# SIDEBAR - COTIZACIONES INTERNACIONALES
# ==========================================
st.sidebar.header("🌐 Cotizaciones de Mercado")
precio_cu_tm = st.sidebar.number_input("Precio Cobre ($/TM)", value=9000.0, step=100.0)
precio_au_oz = st.sidebar.number_input("Precio Oro ($/oz)", value=2400.0, step=10.0)
precio_ag_oz = st.sidebar.number_input("Precio Plata ($/oz)", value=28.0, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("📋 Tabla Oficial de Referencia")
st.sidebar.caption("• Cu: 0-1%: 0% | 1-2%: 60% | 2-3%: 65% | 3-4%: 70% | 4-5.5%: 75% | 5.5-7%: 78% | >7%: 81%")
st.sidebar.caption("• Ag (g/t): <100: 0% | 101-120: 50% | 121-150: 60% | 151-199: 65% | 200-300: 72% | >300: 75%")
st.sidebar.caption("• Au (g/t): <1.0: 0% | 1.01-1.5: 60% | 1.51-2.0: 69% | >2.0: 75%")

# ==========================================
# PESTAÑAS PRINCIPALES
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "🎯 Cotizar Lote Individual", 
    "🔄 Blending Óptimo", 
    "📊 Visión General del Negocio"
])

# ------------------------------------------
# TAB 1: COTIZAR LOTE INDIVIDUAL
# ------------------------------------------
with tab1:
    st.subheader("Cotización de Lote y Análisis de Sobreprecio")
    
    col_in1, col_in2, col_in3 = st.columns(3)
    
    with col_in1:
        nombre_lote = st.text_input("Nombre / Código del Lote", value=f"Lote {len(st.session_state.lotes_comprados) + 1}")
        tms = st.number_input("Toneladas Métricas Secas (TMS)", value=100.0, step=10.0)
        precio_compra_pactado = st.number_input("Precio Compra Pactado ($/TM)", value=420.0, step=10.0)

    with col_in2:
        ley_cu = st.number_input("Ley Cobre Cu (%)", value=3.8, step=0.1)
        ley_au_gt = st.number_input("Ley Oro Au (g/t)", value=1.4, step=0.1)
        ley_ag_gt = st.number_input("Ley Plata Ag (g/t)", value=115.0, step=5.0)

    # Cálculo automático de pagables por Tabla
    pag_cu_tabla = obtener_pagable_cu(ley_cu)
    pag_au_tabla = obtener_pagable_au(ley_au_gt)
    pag_ag_tabla = obtener_pagable_ag(ley_ag_gt)

    with col_in3:
        st.markdown("### Configuración de Pagables")
        modificar_pagables = st.checkbox("Ingresar pagables especiales (Compra Acordada)")
        
        if modificar_pagables:
            pag_cu_pactado = st.number_input("Pagable Cu Pactado (%)", value=75.0, step=1.0)
            pag_au_pactado = st.number_input("Pagable Au Pactado (%)", value=60.0, step=1.0)
            pag_ag_pactado = st.number_input("Pagable Ag Pactado (%)", value=50.0, step=1.0)
        else:
            pag_cu_pactado = pag_cu_tabla
            pag_au_pactado = pag_au_tabla
            pag_ag_pactado = pag_ag_tabla

    # Valores comerciales por TM
    valor_tm_tabla = calcular_valor_por_tm(
        ley_cu, ley_au_gt, ley_ag_gt, 
        pag_cu_tabla, pag_au_tabla, pag_ag_tabla, 
        precio_cu_tm, precio_au_oz, precio_ag_oz
    )

    valor_tm_pactado = calcular_valor_por_tm(
        ley_cu, ley_au_gt, ley_ag_gt, 
        pag_cu_pactado, pag_au_pactado, pag_ag_pactado, 
        precio_cu_tm, precio_au_oz, precio_ag_oz
    )

    costo_total_compra = precio_compra_pactado * tms
    valor_total_venta_pactada = valor_tm_pactado * tms
    valor_total_venta_tabla = valor_tm_tabla * tms
    ganancia_neta_lote = valor_total_venta_pactada - costo_total_compra

    # Cálculo de Sobreprecio / Re-pago sobre Tabla Oficial
    diferencia_tm = precio_compra_pactado - valor_tm_tabla
    sobreprecio_total = diferencia_tm * tms

    # Lógica de Semáforo
    if precio_compra_pactado <= valor_tm_tabla:
        semaforo = "🟢 COMPRA EXCELENTE (En o bajo Tabla Oficial)"
        estado_color = "success"
    elif precio_compra_pactado <= valor_tm_pactado and ganancia_neta_lote > 0:
        semaforo = "🟡 SOBREPRECIO CONTROLADO (Se paga sobre tabla pero hay margen positivo)"
        estado_color = "warning"
    else:
        semaforo = "🔴 LOTE SOBREPAGADO (Pérdida Directa frente a Venta)"
        estado_color = "error"

    st.markdown("---")
    st.subheader("🔍 Comparativa con Tabla Oficial y Evaluación de Re-pago")

    # Tabla Comparativa de Pagables
    df_comparativa = pd.DataFrame({
        "Elemento": ["Cobre (Cu)", "Oro (Au)", "Plata (Ag)"],
        "Ley Ingresada": [f"{ley_cu:.2f} %", f"{ley_au_gt:.2f} g/t", f"{ley_ag_gt:.2f} g/t"],
        "Pagable Tabla Oficial": [f"{pag_cu_tabla}%", f"{pag_au_tabla}%", f"{pag_ag_tabla}%"],
        "Pagable Pactado (Compra)": [f"{pag_cu_pactado}%", f"{pag_au_pactado}%", f"{pag_ag_pactado}%"],
        "Diferencia Pagable": [
            f"{pag_cu_pactado - pag_cu_tabla:+.1f}%",
            f"{pag_au_pactado - pag_au_tabla:+.1f}%",
            f"{pag_ag_pactado - pag_ag_tabla:+.1f}%"
        ]
    })
    st.table(df_comparativa)

    # Tarjeta de Estado / Semáforo
    if estado_color == "success":
        st.success(f"**Semáforo de Compra**: {semaforo}")
    elif estado_color == "warning":
        st.warning(f"**Semáforo de Compra**: {semaforo}")
    else:
        st.error(f"**Semáforo de Compra**: {semaforo}")

    # Métricas de Costo y Sobreprecio
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Costo Total del Lote", f"${costo_total_compra:,.2f}", f"${precio_compra_pactado:,.2f} / TM")
    c2.metric("Valor Tabla Oficial", f"${valor_total_venta_tabla:,.2f}", f"${valor_tm_tabla:,.2f} / TM")
    
    if diferencia_tm > 0:
        c3.metric("Sobreprecio / Re-pago ($)", f"${sobreprecio_total:,.2f}", f"+${diferencia_tm:,.2f} / TM por encima de tabla", delta_color="inverse")
    else:
        c3.metric("Ahorro vs Tabla ($)", f"${abs(sobreprecio_total):,.2f}", f"{diferencia_tm:,.2f} / TM bajo tabla", delta_color="normal")
    
    c4.metric("Ganancia Neta Lote", f"${ganancia_neta_lote:,.2f}", f"Margen: {(ganancia_neta_lote/costo_total_compra)*100:.1f}%" if costo_total_compra > 0 else "0%")

    # Detalle Factura IGV 2.5%
    igv_monto = valor_total_venta_pactada * 0.025
    factura_total = valor_total_venta_pactada + igv_monto

    st.markdown(f"📄 **Facturación Estimada con IGV (2.5%)**: Base Imponible: **${valor_total_venta_pactada:,.2f}** | IGV: **${igv_monto:,.2f}** | **Total Facturado: ${factura_total:,.2f}**")

    if st.button("➕ Confirmar y Guardar Lote para Blending"):
        lote_guardado = {
            "Lote": nombre_lote,
            "TMS": tms,
            "Ley Cu (%)": ley_cu,
            "Ley Au (g/t)": ley_au_gt,
            "Ley Ag (g/t)": ley_ag_gt,
            "Precio Compra ($/TM)": precio_compra_pactado,
            "Costo Total ($)": costo_total_compra,
            "Pagable Cu Tabla (%)": pag_cu_tabla,
            "Pagable Au Tabla (%)": pag_au_tabla,
            "Pagable Ag Tabla (%)": pag_ag_tabla,
            "Pagable Cu Pactado (%)": pag_cu_pactado,
            "Pagable Au Pactado (%)": pag_au_pactado,
            "Pagable Ag Pactado (%)": pag_ag_pactado,
            "Valor Venta Tabla ($)": valor_total_venta_tabla,
            "Valor Venta Pactado ($)": valor_total_venta_pactada,
            "Ganancia Directa ($)": ganancia_neta_lote,
            "Sobreprecio ($)": sobreprecio_total
        }
        st.session_state.lotes_comprados.append(lote_guardado)
        st.success(f"¡{nombre_lote} guardado exitosamente en la lista de blending!")

# ------------------------------------------
# TAB 2: BLENDING ÓPTIMO
# ------------------------------------------
with tab2:
    st.subheader("🔄 optimización de Mezclas (Blending) para Ganancia Máxima")

    if len(st.session_state.lotes_comprados) == 0:
        st.warning("Aún no has agregado lotes. Ve a la pestaña 'Cotizar Lote Individual' para añadir lotes a la lista.")
    else:
        df_lotes = pd.DataFrame(st.session_state.lotes_comprados)
        st.markdown("### 📦 Lotes Disponibles en Cartera")
        st.dataframe(
            df_lotes[[
                "Lote", "TMS", "Ley Cu (%)", "Ley Au (g/t)", "Ley Ag (g/t)",
                "Precio Compra ($/TM)", "Costo Total ($)", "Valor Venta Pactado ($)", "Ganancia Directa ($)"
            ]],
            use_container_width=True
        )

        if st.button("🗑️ Vaciar Cartera de Lotes"):
            st.session_state.lotes_comprados = []
            st.rerun()

        st.markdown("---")
        st.markdown("### 🧪 Algoritmo de Blending Óptimo")

        lotes_lista = st.session_state.lotes_comprados
        n_lotes = len(lotes_lista)

        # Función de ganancia a maximizar para el mezclado
        def funcion_ganancia_blend(weights):
            tms_totales_b = np.sum(weights)
            if tms_totales_b <= 1e-6:
                return 0.0
            
            # Leyes Ponderadas
            cu_b = np.sum(weights * [l["Ley Cu (%)"] for l in lotes_lista]) / tms_totales_b
            au_b = np.sum(weights * [l["Ley Au (g/t)"] for l in lotes_lista]) / tms_totales_b
            ag_b = np.sum(weights * [l["Ley Ag (g/t)"] for l in lotes_lista]) / tms_totales_b
            
            # Pagables por escala alcanzada en la mezcla
            pag_cu_b = obtener_pagable_cu(cu_b)
            pag_au_b = obtener_pagable_au(au_b)
            pag_ag_b = obtener_pagable_ag(ag_b)
            
            val_tm_b = calcular_valor_por_tm(
                cu_b, au_b, ag_b, 
                pag_cu_b, pag_au_b, pag_ag_b, 
                precio_cu_tm, precio_au_oz, precio_ag_oz
            )
            
            venta_b = val_tm_b * tms_totales_b
            costo_b = np.sum(weights * [l["Precio Compra ($/TM)"] for l in lotes_lista])
            
            ganancia = venta_b - costo_b
            return -ganancia  # Negativo para minimizar en scipy

        bounds_b = [(0, l["TMS"]) for l in lotes_lista]
        x0_b = [l["TMS"] for l in lotes_lista]

        res_b = minimize(funcion_ganancia_blend, x0_b, bounds=bounds_b, method='Nelder-Mead')

        if res_b.success or True:
            tms_optimas = np.round(res_b.x, 2)
            
            # Construir tabla de resultado blending
            df_opt = df_lotes.copy()
            df_opt["TMS a Colocar"] = tms_optimas
            df_opt["% Utilizado del Lote"] = np.round((tms_optimas / df_opt["TMS"]) * 100, 1)
            df_opt["Costo Subtotal ($)"] = np.round(tms_optimas * df_opt["Precio Compra ($/TM)"], 2)

            tms_blend_total = np.sum(tms_optimas)
            
            if tms_blend_total > 0:
                cu_blend_pond = np.sum(tms_optimas * df_opt["Ley Cu (%)"]) / tms_blend_total
                au_blend_pond = np.sum(tms_optimas * df_opt["Ley Au (g/t)"]) / tms_blend_total
                ag_blend_pond = np.sum(tms_optimas * df_opt["Ley Ag (g/t)"]) / tms_blend_total

                pag_cu_opt = obtener_pagable_cu(cu_blend_pond)
                pag_au_opt = obtener_pagable_au(au_blend_pond)
                pag_ag_opt = obtener_pagable_ag(ag_blend_pond)

                val_tm_blend_opt = calcular_valor_por_tm(
                    cu_blend_pond, au_blend_pond, ag_blend_pond,
                    pag_cu_opt, pag_au_opt, pag_ag_opt,
                    precio_cu_tm, precio_au_oz, precio_ag_oz
                )

                costo_total_blend = np.sum(df_opt["Costo Subtotal ($)"])
                venta_total_blend = val_tm_blend_opt * tms_blend_total
                ganancia_total_blend = venta_total_blend - costo_total_blend
                venta_separada_lotes = df_lotes["Valor Venta Pactado ($)"].sum()
                beneficio_extra_blending = venta_total_blend - venta_separada_lotes

                st.success("✅ **Composición Óptima Calculada:**")
                st.dataframe(
                    df_opt[["Lote", "TMS", "TMS a Colocar", "% Utilizado del Lote", "Precio Compra ($/TM)", "Costo Subtotal ($)"]],
                    use_container_width=True
                )

                st.markdown("#### 🧪 Leyes y Pagables Alcanzados en Mezcla")
                lp1, lp2, lp3 = st.columns(3)
                lp1.metric("Ley Cobre Cu (%)", f"{cu_blend_pond:.2f}%", f"Pagable Mezcla: {pag_cu_opt}%")
                lp2.metric("Ley Oro Au (g/t)", f"{au_blend_pond:.2f} g/t", f"Pagable Mezcla: {pag_au_opt}%")
                lp3.metric("Ley Plata Ag (g/t)", f"{ag_blend_pond:.2f} g/t", f"Pagable Mezcla: {pag_ag_opt}%")

                st.markdown("---")
                st.markdown("#### 💰 Balances Financieros del Blending")
                fb1, fb2, fb3, fb4 = st.columns(4)
                fb1.metric("TMS Totales Mezcladas", f"{tms_blend_total:,.2f} TMS")
                fb2.metric("Costo Total Compra Lote", f"${costo_total_blend:,.2f}")
                fb3.metric("Venta Total Mezcla", f"${venta_total_blend:,.2f}")
                fb4.metric("Ganancia Neta Máxima", f"${ganancia_total_blend:,.2f}", f"Beneficio Extra Blending: +${beneficio_extra_blending:,.2f}")

# ------------------------------------------
# TAB 3: VISIÓN GENERAL DEL NEGOCIO
# ------------------------------------------
with tab3:
    st.subheader("📊 Resumen Gerencial y Dashboard Amigable")

    if len(st.session_state.lotes_comprados) == 0:
        st.info("Sin datos para mostrar. Agrega lotes a la cartera para ver el análisis comercial global.")
    else:
        df_gen = pd.DataFrame(st.session_state.lotes_comprados)
        
        tms_totales_gen = df_gen["TMS"].sum()
        inversion_total = df_gen["Costo Total ($)"].sum()
        venta_directa_total = df_gen["Valor Venta Pactado ($)"].sum()
        ganancia_directa_total = df_gen["Ganancia Directa ($)"].sum()
        sobreprecio_total_acum = df_gen["Sobreprecio ($)"].sum()

        st.markdown("### 📈 KPIs Principales de la Cartera")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Total Toneladas Compradas", f"{tms_totales_gen:,.2f} TMS")
        k2.metric("Inversión Total en Compras", f"${inversion_total:,.2f}")
        k3.metric("Venta Proyectada Cartera", f"${venta_directa_total:,.2f}")
        k4.metric("Ganancia Directa Acumulada", f"${ganancia_directa_total:,.2f}", f"ROI: {(ganancia_directa_total/inversion_total)*100:.1f}%")

        st.markdown("---")
        
        col_res1, col_res2 = st.columns(2)
        
        with col_res1:
            st.markdown("### 🔎 Estado de Re-pagos sobre Tabla Oficial")
            if sobreprecio_total_acum > 0:
                st.warning(f"⚠️ **Atención Comercial**: Estás pagando **${sobreprecio_total_acum:,.2f}** por encima de la Tabla Oficial de Pagables en el total de tu cartera.")
            else:
                st.success(f"🎉 **Gestión Óptima**: Compras dentro o por debajo de la Tabla Oficial con un ahorro de **${abs(sobreprecio_total_acum):,.2f}**.")
            
            st.dataframe(
                df_gen[["Lote", "TMS", "Precio Compra ($/TM)", "Valor Venta Tabla ($)", "Sobreprecio ($)"]],
                use_container_width=True
            )

        with col_res2:
            st.markdown("### 💡 Recomendaciones Comerciales")
            st.markdown("""
            * **Estrategia de Blending**: Junta los lotes con leyes de Cobre cercanas a bordes de escala (ej. 3.8% Cu) con lotes de mayor ley (ej. 5.5% Cu) para saltar del **70% al 75% o 78% de pagable**.
            * **Negociación de Sobreprecios**: Monitorea de cerca los lotes donde la columna `Sobreprecio ($)` sea alta. Asegúrate de compensar ese costo extra con volumen o con la subida de pagable en la mezcla final.
            * **Facturación e IGV**: Recuerda que las proyecciones muestran el **IGV al 2.5%** para la emisión de facturas oficiales sobre la base imponible del valor de venta.
            """)
