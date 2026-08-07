import streamlit as st
import pandas as pd
import numpy as np

# ==========================================
# CONFIGURACIÓN DE PÁGINA
# ==========================================
st.set_page_config(
    page_title="Cotizador y Valorizador Minero CUNI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚖️ Cotizador, Valorizador y Blending Minero CUNI")
st.markdown("Herramienta para cotización de lotes, liquidación comercial con IGV (2.5%) y cálculo de mezclas (Blending).")

# Factor de conversión constante: Gramos a Onza Troy
GRAMOS_POR_ONZA = 31.1035

# ==========================================
# LÓGICA DE TABLA DE PAGABLES OFICIALES
# ==========================================
def obtener_pagable_oficial(elemento, ley):
    """
    Retorna el % de pagable según la escala oficial de la empresa.
    - Cu en Ley %
    - Ag en Ley g/t
    - Au en Ley g/t
    """
    if elemento == "Cu":
        if ley <= 1.0:
            return 0.0
        elif ley <= 2.0:
            return 60.0
        elif ley <= 3.0:
            return 65.0
        elif ley <= 3.99:
            return 70.0
        elif ley <= 5.50:
            return 75.0
        elif ley <= 7.00:
            return 78.0
        else:
            return 81.0

    elif elemento == "Ag":
        if ley <= 100.0:
            return 0.0
        elif ley <= 120.0:
            return 50.0
        elif ley <= 150.0:
            return 60.0
        elif ley <= 199.0:
            return 65.0
        elif ley <= 300.0:
            return 72.0
        else:
            return 75.0

    elif elemento == "Au":
        if ley <= 1.0:
            return 0.0
        elif ley <= 1.50:
            return 60.0
        elif ley <= 2.00:
            return 69.0
        elif ley <= 3.00:
            return 75.0
        else:
            return 75.0

    return 0.0

# ==========================================
# PARÁMETROS DE MERCADO (SIDEBAR)
# ==========================================
st.sidebar.header("🌐 Precios Internacionales de Mercado")

# Precio Cobre en Dólares por Tonelada Métrica ($/TM)
precio_cu_tm = st.sidebar.number_input("Precio Cobre ($/TM)", value=9200.0, step=50.0)
precio_au_oz = st.sidebar.number_input("Precio Oro ($/oz)", value=2400.0, step=10.0)
precio_ag_oz = st.sidebar.number_input("Precio Plata ($/oz)", value=28.5, step=0.5)

st.sidebar.info("💡 **Unidades:**\n- Cobre: Ley en **%**, Precio en **$/TM**\n- Oro / Plata: Ley en **g/t**, Precio en **$/oz**")

# ==========================================
# INICIALIZACIÓN DEL SESSION STATE DE LOTES
# ==========================================
if "lotes_df" not in st.session_state:
    st.session_state.lotes_df = pd.DataFrame([
        {"Lote": "Lote Alpha", "TMS": 100.0, "Cu (%)": 4.20, "Au (g/t)": 1.80, "Ag (g/t)": 130.0, "Precio Compra ($/TMS)": 280.0},
        {"Lote": "Lote Beta", "TMS": 150.0, "Cu (%)": 2.50, "Au (g/t)": 1.10, "Ag (g/t)": 90.0, "Precio Compra ($/TMS)": 190.0},
    ])

# ==========================================
# PESTAÑAS PRINCIPALES
# ==========================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🎯 Cotizar Lote Nuevo / Individual", 
    "📊 Gestión Múltiple de Lotes", 
    "🔄 Blending / Mezcla de Lotes",
    "📜 Tabla de Pagables Oficial"
])

# ------------------------------------------
# PESTAÑA 1: COTIZADOR INDIVIDUAL
# ------------------------------------------
with tab1:
    st.subheader("🎯 Cotización de Lote Específico")
    st.markdown("Usa esta pestaña para evaluar un lote individual con pagables estándar o **personalizados**. Al finalizar, puedes guardarlo directamente para incluirlo en el Blending.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📝 Datos del Lote")
        nombre_lote = st.text_input("Nombre / Código del Lote", value=f"Lote Especial {len(st.session_state.lotes_df)+1:02d}")
        tms = st.number_input("Toneladas Métricas Secas (TMS)", value=50.0, min_value=0.1, step=5.0)
        
        ley_cu = st.number_input("Ley de Cobre - Cu (%)", value=4.50, min_value=0.0, step=0.1)
        ley_au = st.number_input("Ley de Oro - Au (g/t)", value=2.20, min_value=0.0, step=0.1)
        ley_ag = st.number_input("Ley de Plata - Ag (g/t)", value=140.0, min_value=0.0, step=5.0)

        precio_compra_tms = st.number_input("Precio de Compra al Proveedor ($/TMS)", value=320.0, step=10.0)

    with col2:
        st.markdown("### ⚙️ Configuración de Pagables")
        usar_manual = st.checkbox("Modificar Pagables Manualmente (Especial / Captar Mineral)", value=False)

        pagable_cu_auto = obtener_pagable_oficial("Cu", ley_cu)
        pagable_au_auto = obtener_pagable_oficial("Au", ley_au)
        pagable_ag_auto = obtener_pagable_oficial("Ag", ley_ag)

        if usar_manual:
            st.warning("⚠️ Modo Manual Activo: Ajusta los porcentajes pagables ofrecidos al cliente.")
            pagable_cu = st.number_input("Pagable Cobre (%)", value=float(pagable_cu_auto), min_value=0.0, max_value=100.0, step=1.0)
            pagable_au = st.number_input("Pagable Oro (%)", value=float(pagable_au_auto), min_value=0.0, max_value=100.0, step=1.0)
            pagable_ag = st.number_input("Pagable Plata (%)", value=float(pagable_ag_auto), min_value=0.0, max_value=100.0, step=1.0)
        else:
            st.info("ℹ️ Usando pagables según la **Tabla Oficial** de la empresa.")
            pagable_cu = pagable_cu_auto
            pagable_au = pagable_au_auto
            pagable_ag = pagable_ag_auto

            st.write(f"• **Pagable Cu:** {pagable_cu:.1f}%")
            st.write(f"• **Pagable Au:** {pagable_au:.1f}%")
            st.write(f"• **Pagable Ag:** {pagable_ag:.1f}%")

    # Cálculos de Valorización (Au y Ag convertidos de g/t a oz/t)
    val_cu_tms = (ley_cu / 100.0) * precio_cu_tm * (pagable_cu / 100.0)
    val_au_tms = (ley_au / GRAMOS_POR_ONZA) * precio_au_oz * (pagable_au / 100.0)
    val_ag_tms = (ley_ag / GRAMOS_POR_ONZA) * precio_ag_oz * (pagable_ag / 100.0)

    valor_venta_tms = val_cu_tms + val_au_tms + val_ag_tms
    valor_venta_total = valor_venta_tms * tms

    costo_compra_total = precio_compra_tms * tms
    ganancia_total = valor_venta_total - costo_compra_total
    ganancia_tms = ganancia_total / tms if tms > 0 else 0

    # Facturación e IGV al 2.5%
    igv_rate = 0.025
    igv_monto = valor_venta_total * igv_rate
    total_facturado_igv = valor_venta_total + igv_monto

    st.markdown("---")
    st.subheader("💰 Resumen Económico y Facturación")

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    col_m1.metric("Costo Total Compra Lote", f"${costo_compra_total:,.2f}")
    col_m2.metric("Valor Venta Total (Liquidación)", f"${valor_venta_total:,.2f}")
    col_m3.metric("Ganancia Total Lote", f"${ganancia_total:,.2f}", delta=f"${ganancia_tms:,.2f} / TMS")
    col_m4.metric("Factura Total (+2.5% IGV)", f"${total_facturado_igv:,.2f}")

    # Desglose de Facturación
    with st.expander("📄 Ver Desglose de Facturación e IGV (2.5%)", expanded=True):
        st.table(pd.DataFrame([
            {"Concepto": "Valor Venta del Lote (Subtotal / Base Imponible)", "Monto ($)": f"${valor_venta_total:,.2f}"},
            {"Concepto": "IGV Minero (2.5%)", "Monto ($)": f"${igv_monto:,.2f}"},
            {"Concepto": "TOTAL FACTURADO CON IGV", "Monto ($)": f"${total_facturado_igv:,.2f}"},
            {"Concepto": "Costo de Compra del Lote", "Monto ($)": f"${costo_compra_total:,.2f}"},
            {"Concepto": "GANANCIA NETA ESTIMADA", "Monto ($)": f"${ganancia_total:,.2f}"}
        ]))

    # Botón para añadir a los lotes comprados para Blending
    st.markdown("---")
    if st.button("➕ Confirmar y Agregar este Lote a la Lista General (Blending)", type="primary"):
        nuevo_lote = {
            "Lote": nombre_lote,
            "TMS": float(tms),
            "Cu (%)": float(ley_cu),
            "Au (g/t)": float(ley_au),
            "Ag (g/t)": float(ley_ag),
            "Precio Compra ($/TMS)": float(precio_compra_tms)
        }
        st.session_state.lotes_df = pd.concat([
            st.session_state.lotes_df,
            pd.DataFrame([nuevo_lote])
        ], ignore_index=True)
        st.success(f"✅ ¡El lote **{nombre_lote}** ha sido guardado exitosamente! Ahora está disponible en 'Gestión Múltiple' y 'Blending'.")

# ------------------------------------------
# PESTAÑA 2: GESTIÓN MÚLTIPLE DE LOTES
# ------------------------------------------
with tab2:
    st.subheader("📊 Tabla Editable de Lotes Múltiples")
    st.markdown("Aquí puedes editar, agregar o eliminar lotes. Todos los cambios se reflejarán automáticamente en los cálculos acumulados y en la pestaña de Blending.")

    df_editor = st.data_editor(
        st.session_state.lotes_df,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_tabla_lotes"
    )

    # Actualizar Session State
    st.session_state.lotes_df = df_editor

    if not df_editor.empty:
        def procesar_fila(row):
            t = row["TMS"]
            cu = row["Cu (%)"]
            au = row["Au (g/t)"]
            ag = row["Ag (g/t)"]
            p_compra = row["Precio Compra ($/TMS)"]

            pag_cu = obtener_pagable_oficial("Cu", cu)
            pag_au = obtener_pagable_oficial("Au", au)
            pag_ag = obtener_pagable_oficial("Ag", ag)

            v_cu = (cu / 100.0) * precio_cu_tm * (pag_cu / 100.0)
            v_au = (au / GRAMOS_POR_ONZA) * precio_au_oz * (pag_au / 100.0)
            v_ag = (ag / GRAMOS_POR_ONZA) * precio_ag_oz * (pag_ag / 100.0)

            v_venta_tms = v_cu + v_au + v_ag
            v_venta_tot = v_venta_tms * t
            c_compra_tot = p_compra * t
            ganancia = v_venta_tot - c_compra_tot
            igv = v_venta_tot * 0.025
            factura = v_venta_tot + igv

            return pd.Series({
                "Pag. Cu (%)": pag_cu,
                "Pag. Au (%)": pag_au,
                "Pag. Ag (%)": pag_ag,
                "Valor Venta ($/TMS)": round(v_venta_tms, 2),
                "Costo Compra Total ($)": round(c_compra_tot, 2),
                "Valor Venta Total ($)": round(v_venta_tot, 2),
                "Ganancia Total ($)": round(ganancia, 2),
                "IGV 2.5% ($)": round(igv, 2),
                "Factura Total ($)": round(factura, 2)
            })

        resultados = df_editor.apply(procesar_fila, axis=1)
        df_completo = pd.concat([df_editor, resultados], axis=1)

        st.subheader("📋 Liquidación Individual de Lotes")
        st.dataframe(df_completo, use_container_width=True)

        # Totales Consolidados
        tms_totales = df_completo["TMS"].sum()
        costo_total_acum = df_completo["Costo Compra Total ($)"].sum()
        venta_total_acum = df_completo["Valor Venta Total ($)"].sum()
        ganancia_acum = df_completo["Ganancia Total ($)"].sum()
        factura_acum = df_completo["Factura Total ($)"].sum()

        st.markdown("### 📈 Totales Acumulados de Lotes Comprados")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total TMS Compradas", f"{tms_totales:,.2f}")
        c2.metric("Costo Compra Acumulado", f"${costo_total_acum:,.2f}")
        c3.metric("Ganancia Neta Sin Blending", f"${ganancia_acum:,.2f}")
        c4.metric("Factura Total (+2.5% IGV)", f"${factura_acum:,.2f}")

# ------------------------------------------
# PESTAÑA 3: BLENDING / MEZCLA DE LOTES
# ------------------------------------------
with tab3:
    st.subheader("🔄 Blending y Optimización de Mezclas")
    st.markdown("Calcula el resultado comercial de **mezclar todos o algunos de tus lotes comprados** para elevar leyes promedio y acceder a un porcentaje de pagable superior.")

    if st.session_state.lotes_df.empty:
        st.warning("⚠️ No hay lotes registrados para realizar el Blending. Cotiza o añade lotes en las pestañas anteriores.")
    else:
        st.markdown("### 🎛️ Selección de Toneladas a Mezclar por Lote")
        df_blend_input = st.session_state.lotes_df.copy()
        
        # Selector interactivo de toneladas a incluir en la mezcla
        tms_usadas = []
        col_list = st.columns(min(len(df_blend_input), 4))
        
        for idx, row in df_blend_input.iterrows():
            col_idx = idx % 4
            with col_list[col_idx]:
                cant = st.number_input(
                    f"TMS a usar: {row['Lote']}", 
                    min_value=0.0, 
                    max_value=float(row["TMS"]), 
                    value=float(row["TMS"]),
                    step=5.0,
                    key=f"blend_tms_{idx}"
                )
                tms_usadas.append(cant)

        df_blend_input["TMS Usadas"] = tms_usadas
        df_activos = df_blend_input[df_blend_input["TMS Usadas"] > 0].copy()

        if df_activos.empty or df_activos["TMS Usadas"].sum() == 0:
            st.error("Selecciona al menos un lote con TMS mayor a 0 para calcular la mezcla.")
        else:
            # Ponderación de Leyes
            tms_mezcla_total = df_activos["TMS Usadas"].sum()
            ley_cu_blend = (df_activos["TMS Usadas"] * df_activos["Cu (%)"]).sum() / tms_mezcla_total
            ley_au_blend = (df_activos["TMS Usadas"] * df_activos["Au (g/t)"]).sum() / tms_mezcla_total
            ley_ag_blend = (df_activos["TMS Usadas"] * df_activos["Ag (g/t)"]).sum() / tms_mezcla_total

            # Costo de Compra Ponderado
            costo_compra_blend_total = (df_activos["TMS Usadas"] * df_activos["Precio Compra ($/TMS)"]).sum()
            precio_compra_promedio_tms = costo_compra_blend_total / tms_mezcla_total

            # Pagables correspondientes a la Ley Resultante del Blending
            pagable_cu_blend = obtener_pagable_oficial("Cu", ley_cu_blend)
            pagable_au_blend = obtener_pagable_oficial("Au", ley_au_blend)
            pagable_ag_blend = obtener_pagable_oficial("Ag", ley_ag_blend)

            # Valorización de la Mezcla (por TMS)
            val_cu_blend_tms = (ley_cu_blend / 100.0) * precio_cu_tm * (pagable_cu_blend / 100.0)
            val_au_blend_tms = (ley_au_blend / GRAMOS_POR_ONZA) * precio_au_oz * (pagable_au_blend / 100.0)
            val_ag_blend_tms = (ley_ag_blend / GRAMOS_POR_ONZA) * precio_ag_oz * (pagable_ag_blend / 100.0)

            valor_venta_blend_tms = val_cu_blend_tms + val_au_blend_tms + val_ag_blend_tms
            valor_venta_blend_total = valor_venta_blend_tms * tms_mezcla_total

            ganancia_blend_total = valor_venta_blend_total - costo_compra_blend_total
            ganancia_blend_tms = ganancia_blend_total / tms_mezcla_total

            igv_blend_monto = valor_venta_blend_total * 0.025
            total_facturado_blend = valor_venta_blend_total + igv_blend_monto

            st.markdown("---")
            st.subheader("🧪 Resultados de Leyes y Pagables de la Mezcla (Blending)")

            c_b1, c_b2, c_b3, c_b4 = st.columns(4)
            c_b1.metric("Total TMS Mezcladas", f"{tms_mezcla_total:,.2f} TMS")
            c_b2.metric("Ley Cobre (Cu)", f"{ley_cu_blend:.2f}%", delta=f"Pagable: {pagable_cu_blend:.1f}%")
            c_b3.metric("Ley Oro (Au)", f"{ley_au_blend:.2f} g/t", delta=f"Pagable: {pagable_au_blend:.1f}%")
            c_b4.metric("Ley Plata (Ag)", f"{ley_ag_blend:.2f} g/t", delta=f"Pagable: {pagable_ag_blend:.1f}%")

            st.markdown("### 💵 Liquidación Económica del Blending")
            m_b1, m_b2, m_b3, m_b4 = st.columns(4)
            m_b1.metric("Costo Compra Mezcla", f"${costo_compra_blend_total:,.2f}")
            m_b2.metric("Valor Venta Mezcla", f"${valor_venta_blend_total:,.2f}")
            m_b3.metric("Ganancia Neta Blending", f"${ganancia_blend_total:,.2f}", delta=f"${ganancia_blend_tms:,.2f} / TMS")
            m_b4.metric("Factura Total (+2.5% IGV)", f"${total_facturado_blend:,.2f}")

            # Desglose de Facturación
            with st.expander("📄 Ver Desglose de Facturación de la Mezcla (2.5% IGV)", expanded=True):
                st.table(pd.DataFrame([
                    {"Concepto": "Valor Venta de la Mezcla (Base Imponible)", "Monto ($)": f"${valor_venta_blend_total:,.2f}"},
                    {"Concepto": "IGV Minero (2.5%)", "Monto ($)": f"${igv_blend_monto:,.2f}"},
                    {"Concepto": "TOTAL FACTURADO CON IGV", "Monto ($)": f"${total_facturado_blend:,.2f}"},
                    {"Concepto": "Costo Total de Compra de Minerales", "Monto ($)": f"${costo_compra_blend_total:,.2f}"},
                    {"Concepto": "GANANCIA NETA FINAL POR BLENDING", "Monto ($)": f"${ganancia_blend_total:,.2f}"}
                ]))

# ------------------------------------------
# PESTAÑA 4: TABLA DE PAGABLES OFICIAL
# ------------------------------------------
with tab4:
    st.subheader("📜 Escala Oficial de Pagables (Referencia)")
    st.markdown("Esta es la tabla base de pagables utilizada para las valorizaciones automáticas.")

    datos_tabla_oficial = [
        {"Elemento": "Cu", "Contenido Desde": "0%", "Contenido Hasta": "1%", "Pagable (%)": "0.0%"},
        {"Elemento": "Cu", "Contenido Desde": "1.01%", "Contenido Hasta": "2%", "Pagable (%)": "60.0%"},
        {"Elemento": "Cu", "Contenido Desde": "2.01%", "Contenido Hasta": "3%", "Pagable (%)": "65.0%"},
        {"Elemento": "Cu", "Contenido Desde": "3.00%", "Contenido Hasta": "3.99%", "Pagable (%)": "70.0%"},
        {"Elemento": "Cu", "Contenido Desde": "4.00%", "Contenido Hasta": "5.5%", "Pagable (%)": "75.0%"},
        {"Elemento": "Cu", "Contenido Desde": "5.51%", "Contenido Hasta": "7%", "Pagable (%)": "78.0%"},
        {"Elemento": "Cu", "Contenido Desde": "7.01%", "Contenido Hasta": "10%", "Pagable (%)": "81.0%"},
        {"Elemento": "Ag", "Contenido Desde": "0 g/t", "Contenido Hasta": "100 g/t", "Pagable (%)": "0.0%"},
        {"Elemento": "Ag", "Contenido Desde": "101 g/t", "Contenido Hasta": "120 g/t", "Pagable (%)": "50.0%"},
        {"Elemento": "Ag", "Contenido Desde": "121 g/t", "Contenido Hasta": "150 g/t", "Pagable (%)": "60.0%"},
        {"Elemento": "Ag", "Contenido Desde": "151 g/t", "Contenido Hasta": "199 g/t", "Pagable (%)": "65.0%"},
        {"Elemento": "Ag", "Contenido Desde": "200 g/t", "Contenido Hasta": "300 g/t", "Pagable (%)": "72.0%"},
        {"Elemento": "Ag", "Contenido Desde": "301 g/t", "Contenido Hasta": "500 g/t", "Pagable (%)": "75.0%"},
        {"Elemento": "Au", "Contenido Desde": "0 g/t", "Contenido Hasta": "1 g/t", "Pagable (%)": "0.0%"},
        {"Elemento": "Au", "Contenido Desde": "1.01 g/t", "Contenido Hasta": "1.5 g/t", "Pagable (%)": "60.0%"},
        {"Elemento": "Au", "Contenido Desde": "1.51 g/t", "Contenido Hasta": "2 g/t", "Pagable (%)": "69.0%"},
        {"Elemento": "Au", "Contenido Desde": "2.01 g/t", "Contenido Hasta": "3 g/t", "Pagable (%)": "75.0%"},
        {"Elemento": "Au", "Contenido Desde": "3.01 g/t", "Contenido Hasta": "8 g/t", "Pagable (%)": "75.0%"},
    ]

    st.table(pd.DataFrame(datos_tabla_oficial))
```
