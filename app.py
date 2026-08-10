import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import minimize

# ==========================================
# CONFIGURACIÓN Y VALORES POR DEFECTO (EDITABLE)
# ==========================================
# Precios estándar de mercado
PRECIO_CU_DEFAULT = 14300   # Precio Cobre en Dólares por Tonelada Métrica ($/TM)
PRECIO_AU_DEFAULT = 4300   # Precio Oro en Dólares por Onza ($/oz)
PRECIO_AG_DEFAULT = 63     # Precio Plata en Dólares por Onza ($/oz)

# Impuestos
IGV_TASA_DEFAULT = 0.025     # Tasa de IGV (2.5%)

# Límites predeterminados para Blending
CU_MIN_DEFAULT = 4.0         # Ley Mínima Cobre Cu (%)
CU_MAX_DEFAULT = 5.5         # Ley Máxima Cobre Cu (%)
AU_MIN_DEFAULT = 3.0         # Ley Mínima Oro Au (g/t)
AU_MAX_DEFAULT = 4.0         # Ley Máxima Oro Au (g/t)
AG_MIN_DEFAULT = 350.0       # Ley Mínima Plata Ag (g/t)
AG_MAX_DEFAULT = 400.0       # Ley Máxima Plata Ag (g/t)

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Cotizador Minero y Blending Óptimo - CUNI",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Cotizador Minero, Precio Recomendado y Blending Óptimo")

# Inicialización del estado global de lotes en cartera
if "lotes_comprados" not in st.session_state:
    st.session_state.lotes_comprados = []

# ==========================================
# FUNCIONES DE TABLA OFICIAL DE PAGABLES
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
# SIDEBAR - PARÁMETROS Y COTIZACIONES
# ==========================================
st.sidebar.header("🌐 Cotizaciones de Mercado")
precio_cu_tm = st.sidebar.number_input("Precio Cobre ($/TM)", value=PRECIO_CU_DEFAULT, step=100.0)
precio_au_oz = st.sidebar.number_input("Precio Oro ($/oz)", value=PRECIO_AU_DEFAULT, step=10.0)
precio_ag_oz = st.sidebar.number_input("Precio Plata ($/oz)", value=PRECIO_AG_DEFAULT, step=0.5)

st.sidebar.markdown("---")
st.sidebar.subheader("📋 Tabla Oficial de Referencia")
st.sidebar.caption("• **Cu**: ≤1%: 0% | 1-2%: 60% | 2-3%: 65% | 3-4%: 70% | 4-5.5%: 75% | 5.5-7%: 78% | >7%: 81%")
st.sidebar.caption("• **Ag (g/t)**: ≤100: 0% | 101-120: 50% | 121-150: 60% | 151-199: 65% | 200-300: 72% | >300: 75%")
st.sidebar.caption("• **Au (g/t)**: ≤1.0: 0% | 1.01-1.5: 60% | 1.51-2.0: 69% | >2.0: 75%")

# ==========================================
# PESTAÑAS DE LA APLICACIÓN
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
    st.subheader("Cotización de Lote y Análisis de Precio Sugerido")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nombre_lote = st.text_input("Nombre / Código del Lote", value=f"Lote {len(st.session_state.lotes_comprados) + 1}")
        tms = st.number_input("Toneladas Métricas Secas (TMS)", value=100.0, step=10.0)
        precio_ofrecido = st.number_input("Precio que Vas a Ofrecer / Comprar ($/TM)", value=430.0, step=10.0)

    with col2:
        ley_cu = st.number_input("Ley Cobre Cu (%)", value=3.8, step=0.1)
        ley_au_gt = st.number_input("Ley Oro Au (g/t)", value=2.2, step=0.1)
        ley_ag_gt = st.number_input("Ley Plata Ag (g/t)", value=180.0, step=5.0)

    pag_cu_tabla = obtener_pagable_cu(ley_cu)
    pag_au_tabla = obtener_pagable_au(ley_au_gt)
    pag_ag_tabla = obtener_pagable_ag(ley_ag_gt)

    precio_recomendado_tm = calcular_valor_por_tm(
        ley_cu, ley_au_gt, ley_ag_gt, 
        pag_cu_tabla, pag_au_tabla, pag_ag_tabla, 
        precio_cu_tm, precio_au_oz, precio_ag_oz
    )

    with col3:
        st.markdown("### Configuración de Pagables")
        modificar_pagables = st.checkbox("Ajustar pagables pactados manualmente")
        
        if modificar_pagables:
            pag_cu_pactado = st.number_input("Pagable Cu Pactado (%)", value=75.0, step=1.0)
            pag_au_pactado = st.number_input("Pagable Au Pactado (%)", value=69.0, step=1.0)
            pag_ag_pactado = st.number_input("Pagable Ag Pactado (%)", value=65.0, step=1.0)
        else:
            pag_cu_pactado = pag_cu_tabla
            pag_au_pactado = pag_au_tabla
            pag_ag_pactado = pag_ag_tabla
            st.info(f"Pagables Tabla -> Cu: {pag_cu_tabla}% | Au: {pag_au_tabla}% | Ag: {pag_ag_tabla}%")

    valor_venta_pactada_tm = calcular_valor_por_tm(
        ley_cu, ley_au_gt, ley_ag_gt, 
        pag_cu_pactado, pag_au_pactado, pag_ag_pactado, 
        precio_cu_tm, precio_au_oz, precio_ag_oz
    )

    costo_total_compra = precio_ofrecido * tms
    valor_total_venta = valor_venta_pactada_tm * tms
    ganancia_neta_lote = valor_total_venta - costo_total_compra

    diferencia_tm = precio_ofrecido - precio_recomendado_tm
    impacto_sobreprecio_total = diferencia_tm * tms

    st.markdown("---")
    st.subheader("💡 Comparativa de Precios y Sugerencia Comercial")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Precio Recomendado Tabla", f"${precio_recomendado_tm:,.2f} / TM")
    m2.metric("Precio que Ofreces", f"${precio_ofrecido:,.2f} / TM")
    
    if diferencia_tm <= 0:
        m3.metric("Margen a Favor vs Tabla", f"${abs(diferencia_tm):,.2f} / TM", "Compra dentro de norma", delta_color="normal")
    else:
        m3.metric("Sobreprecio / Re-pago", f"+${diferencia_tm:,.2f} / TM", "Por encima de tabla", delta_color="inverse")

    m4.metric("Ganancia Neta Proyectada", f"${ganancia_neta_lote:,.2f}")

    if precio_ofrecido <= precio_recomendado_tm:
        st.success(f"🟢 **EXCELENTE OFERTA**: Tu precio de compra (${precio_ofrecido:,.2f}/TM) no supera el sugerido por Tabla Oficial (${precio_recomendado_tm:,.2f}/TM). Garantizas margen comercial directo.")
    elif ganancia_neta_lote > 0:
        st.warning(f"🟡 **RE-PAGO DETECTADO**: Estás ofreciendo **${diferencia_tm:,.2f}/TM de sobreprecio** sobre la tabla oficial (Costo extra total: **${impacto_sobreprecio_total:,.2f}**). Se aprueba porque deja ganancia neta, pero se recomienda compensar con Blending.")
    else:
        st.error(f"🔴 **LOTE DEFICITARIO**: Tu precio ofrecido (${precio_ofrecido:,.2f}/TM) supera el valor de venta total. Genera una pérdida de **${abs(ganancia_neta_lote):,.2f}** si no se mezcla.")

    igv_monto = valor_total_venta * IGV_TASA_DEFAULT
    factura_total = valor_total_venta + igv_monto

    st.markdown(f"📄 **Facturación Estimada (IGV {IGV_TASA_DEFAULT*100:.1f}%)**: Base Imponible: **${valor_total_venta:,.2f}** | IGV: **${igv_monto:,.2f}** | **Total Factura: ${factura_total:,.2f}**")

    if st.button("➕ Confirmar y Guardar Lote para Blending"):
        lote_guardado = {
            "Lote": nombre_lote,
            "TMS": tms,
            "Ley Cu (%)": ley_cu,
            "Ley Au (g/t)": ley_au_gt,
            "Ley Ag (g/t)": ley_ag_gt,
            "Precio Compra ($/TM)": precio_ofrecido,
            "Precio Recomendado ($/TM)": precio_recomendado_tm,
            "Costo Total ($)": costo_total_compra,
            "Pagable Cu Pactado (%)": pag_cu_pactado,
            "Pagable Au Pactado (%)": pag_au_pactado,
            "Pagable Ag Pactado (%)": pag_ag_pactado,
            "Valor Venta ($)": valor_total_venta,
            "Ganancia Directa ($)": ganancia_neta_lote,
            "Sobreprecio Total ($)": impacto_sobreprecio_total
        }
        st.session_state.lotes_comprados.append(lote_guardado)
        st.success(f"¡{nombre_lote} añadido exitosamente a la lista de Blending!")

# ------------------------------------------
# TAB 2: BLENDING ÓPTIMO
# ------------------------------------------
with tab2:
    st.subheader("🔄 Optimizador de Blending con Rangos de Leyes (Mínimas y Máximas)")

    if len(st.session_state.lotes_comprados) == 0:
        st.warning("No hay lotes en cartera. Registra nuevos lotes en la pestaña 'Cotizar Lote Individual' para activar el optimizador.")
    else:
        df_lotes = pd.DataFrame(st.session_state.lotes_comprados)
        st.markdown("### 📦 Cartera Actual de Lotes Disponible")
        st.dataframe(
            df_lotes[[
                "Lote", "TMS", "Ley Cu (%)", "Ley Au (g/t)", "Ley Ag (g/t)",
                "Precio Compra ($/TM)", "Precio Recomendado ($/TM)", "Costo Total ($)", "Valor Venta ($)", "Ganancia Directa ($)"
            ]],
            use_container_width=True
        )

        if st.button("🗑️ Vaciar Cartera de Lotes"):
            st.session_state.lotes_comprados = []
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎯 Definición de Rangos de Leyes para la Mezcla")
        
        st.caption("Ajusta los límites inferiores y superiores. El optimizador mezclará lotes de alta y baja ley sin exceder los techos.")
        col_min1, col_min2, col_min3 = st.columns(3)
        min_cu_target = col_min1.number_input("Ley Mínima Cobre Cu (%)", value=CU_MIN_DEFAULT, step=0.1)
        min_au_target = col_min2.number_input("Ley Mínima Oro Au (g/t)", value=AU_MIN_DEFAULT, step=0.1)
        min_ag_target = col_min3.number_input("Ley Mínima Plata Ag (g/t)", value=AG_MIN_DEFAULT, step=10.0)

        col_max1, col_max2, col_max3 = st.columns(3)
        max_cu_target = col_max1.number_input("Ley Máxima Cobre Cu (%)", value=CU_MAX_DEFAULT, step=0.1)
        max_au_target = col_max2.number_input("Ley Máxima Oro Au (g/t)", value=AU_MAX_DEFAULT, step=0.1)
        max_ag_target = col_max3.number_input("Ley Máxima Plata Ag (g/t)", value=AG_MAX_DEFAULT, step=10.0)

        lotes_lista = st.session_state.lotes_comprados

        def funcion_ganancia_blend(weights):
            tms_totales_b = np.sum(weights)
            if tms_totales_b <= 1e-5:
                return 0.0
            
            cu_b = np.sum(weights * [l["Ley Cu (%)"] for l in lotes_lista]) / tms_totales_b
            au_b = np.sum(weights * [l["Ley Au (g/t)"] for l in lotes_lista]) / tms_totales_b
            ag_b = np.sum(weights * [l["Ley Ag (g/t)"] for l in lotes_lista]) / tms_totales_b
            
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
            
            return -(venta_b - costo_b)

        constraints = [
            {'type': 'ineq', 'fun': lambda w: np.sum(w * [l["Ley Cu (%)"] - min_cu_target for l in lotes_lista])},
            {'type': 'ineq', 'fun': lambda w: np.sum(w * [l["Ley Au (g/t)"] - min_au_target for l in lotes_lista])},
            {'type': 'ineq', 'fun': lambda w: np.sum(w * [l["Ley Ag (g/t)"] - min_ag_target for l in lotes_lista])},
            {'type': 'ineq', 'fun': lambda w: np.sum(w * [max_cu_target - l["Ley Cu (%)"] for l in lotes_lista])},
            {'type': 'ineq', 'fun': lambda w: np.sum(w * [max_au_target - l["Ley Au (g/t)"] for l in lotes_lista])},
            {'type': 'ineq', 'fun': lambda w: np.sum(w * [max_ag_target - l["Ley Ag (g/t)"] for l in lotes_lista])},
            {'type': 'ineq', 'fun': lambda w: np.sum(w) - 0.01}
        ]

        bounds = [(0, l["TMS"]) for l in lotes_lista]
        x0 = [l["TMS"] for l in lotes_lista]

        res = minimize(funcion_ganancia_blend, x0, method='SLSQP', bounds=bounds, constraints=constraints)

        tms_optimas = np.round(res.x, 2) if res.success else np.zeros(len(lotes_lista))
        tms_total_mezcla = np.sum(tms_optimas)

        if res.success and tms_total_mezcla > 0.01:
            df_resultado_opt = df_lotes.copy()
            df_resultado_opt["TMS a Colocar"] = tms_optimas
            df_resultado_opt["% Utilizado del Lote"] = np.round((tms_optimas / df_resultado_opt["TMS"]) * 100, 1)
            df_resultado_opt["Costo Subtotal ($)"] = np.round(tms_optimas * df_resultado_opt["Precio Compra ($/TM)"], 2)

            cu_blend = np.sum(tms_optimas * df_resultado_opt["Ley Cu (%)"]) / tms_total_mezcla
            au_blend = np.sum(tms_optimas * df_resultado_opt["Ley Au (g/t)"]) / tms_total_mezcla
            ag_blend = np.sum(tms_optimas * df_resultado_opt["Ley Ag (g/t)"]) / tms_total_mezcla

            pag_cu_opt = obtener_pagable_cu(cu_blend)
            pag_au_opt = obtener_pagable_au(au_blend)
            pag_ag_opt = obtener_pagable_ag(ag_blend)

            val_tm_mezcla = calcular_valor_por_tm(
                cu_blend, au_blend, ag_blend,
                pag_cu_opt, pag_au_opt, pag_ag_opt,
                precio_cu_tm, precio_au_oz, precio_ag_oz
            )

            costo_total_mezcla = np.sum(df_resultado_opt["Costo Subtotal ($)"])
            venta_total_mezcla = val_tm_mezcla * tms_total_mezcla
            ganancia_total_mezcla = venta_total_mezcla - costo_total_mezcla

            st.success("✅ **Composición Óptima de Blending Calculada Exitosamente**")
            st.markdown("#### 📋 Toneladas Exactas a Mezclar por Lote")
            st.dataframe(
                df_resultado_opt[["Lote", "TMS", "TMS a Colocar", "% Utilizado del Lote", "Precio Compra ($/TM)", "Costo Subtotal ($)"]],
                use_container_width=True
            )

            st.markdown("#### 🧪 Leyes Resultantes de la Mezcla vs. Rangos Permitidos")
            l1, l2, l3 = st.columns(3)
            l1.metric("Ley Cobre Cu (%)", f"{cu_blend:.2f}%", f"Rango: {min_cu_target}% - {max_cu_target}% | Pagable: {pag_cu_opt}%")
            l2.metric("Ley Oro Au (g/t)", f"{au_blend:.2f} g/t", f"Rango: {min_au_target}g - {max_au_target}g | Pagable: {pag_au_opt}%")
            l3.metric("Ley Plata Ag (g/t)", f"{ag_blend:.2f} g/t", f"Rango: {min_ag_target}g - {max_ag_target}g | Pagable: {pag_ag_opt}%")

            st.markdown("---")
            st.markdown("#### 💰 Balance Financiero Total de la Mezcla")
            b1, b2, b3, b4 = st.columns(4)
            b1.metric("Total TMS Mezcladas", f"{tms_total_mezcla:,.2f} TMS")
            b2.metric("Costo Total de la Compra", f"${costo_total_mezcla:,.2f}")
            b3.metric("Venta Total Proyectada", f"${venta_total_mezcla:,.2f}")
            b4.metric("Ganancia Máxima Proyectada", f"${ganancia_total_mezcla:,.2f}", f"ROI: {(ganancia_total_mezcla/costo_total_mezcla)*100:.1f}%")

        else:
            st.error(f"⚠️ **Incapaz de cumplir con los rangos definidos**: Con los lotes actualmente registrados no es posible lograr una mezcla que esté simultáneamente dentro de los rangos de Cobre ({min_cu_target}% - {max_cu_target}%), Oro ({min_au_target}g - {max_au_target}g) y Plata ({min_ag_target}g - {max_ag_target}g). Revisa las leyes de tus lotes o amplía los rangos.")

# ------------------------------------------
# TAB 3: VISIÓN GENERAL DEL NEGOCIO
# ------------------------------------------
with tab3:
    st.subheader("📊 Resumen Ejecutivo y Dashboard del Negocio")

    if len(st.session_state.lotes_comprados) == 0:
        st.info("Sin información acumulada. Inicia cotizando lotes para visualizar el panel de control.")
    else:
        df_dash = pd.DataFrame(st.session_state.lotes_comprados)
        
        tms_totales_dash = df_dash["TMS"].sum()
        inversion_total_dash = df_dash["Costo Total ($)"].sum()
        venta_total_dash = df_dash["Valor Venta ($)"].sum()
        ganancia_total_dash = df_dash["Ganancia Directa ($)"].sum()
        sobreprecio_acumulado = df_dash["Sobreprecio Total ($)"].sum()

        st.markdown("### 📈 Indicadores Clave de Desempeño (KPIs)")
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Volumen Comprado", f"{tms_totales_dash:,.2f} TMS")
        k2.metric("Inversión en Mineral", f"${inversion_total_dash:,.2f}")
        k3.metric("Venta Total Estimada", f"${venta_total_dash:,.2f}")
        k4.metric("Ganancia Neta Total", f"${ganancia_total_dash:,.2f}", f"Margen: {(ganancia_total_dash/inversion_total_dash)*100:.1f}%")

        st.markdown("---")
        c_left, c_right = st.columns(2)

        with c_left:
            st.markdown("### 🔍 Evaluación de Re-pagos por Lote")
            if sobreprecio_acumulado > 0:
                st.warning(f"Se ha pagado un acumulado de **${sobreprecio_acumulado:,.2f}** por encima de las tablas de referencia oficial para asegurar el mineral.")
            else:
                st.success(f"Las compras se mantienen alineadas o por debajo de la Tabla Oficial (Ahorro de **${abs(sobreprecio_acumulado):,.2f}**).")

            st.dataframe(
                df_dash[["Lote", "TMS", "Precio Compra ($/TM)", "Precio Recomendado ($/TM)", "Sobreprecio Total ($)"]],
                use_container_width=True
            )

        with c_right:
            st.markdown("### 💡 Recomendaciones Gerenciales")
            st.markdown("""
            * **Estrategia de Blending con Rango Techo**: Limitar la mezcla a **5.5% Cu**, **4.0 g/t Au** y **400 g/t Ag** evita 'regalar' ley en la venta al cliente final y fuerza al algoritmo a diluir y digerir los lotes de baja ley que tienes comprados.
            * **Control de Compras Especiales**: Cuando compres minerales con sobreprecio, verifica en la pestaña de Blending cuántas toneladas de lote de alta ley necesitas para amortizar dicho re-pago.
            * **Facturación**: La emisión de comprobantes se calcula considerando la **tasa de IGV del 2.5%** sobre la base imponible del concentrado comercializado.
            """)
