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

st.title("⚖️ Cotizador y Valorizador Minero CUNI")
st.markdown("Herramienta para cotización de lotes mineros, liquidación comercial y cálculo de factura con IGV (2.5%).")

# ==========================================
# LÓGICA DE TABLA DE PAGABLES OFICIALES
# ==========================================
def obtener_pagable_oficial(elemento, ley):
    """
    Retorna el % de pagable según la escala oficial de la empresa.
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

st.sidebar.info("💡 **Nota:** El precio del cobre se ingresa y calcula directamente en **Dólares por Tonelada ($/TM)**.")

# ==========================================
# PESTAÑAS PRINCIPALES
# ==========================================
tab1, tab2, tab3 = st.tabs([
    "🎯 Cotizar Lote Nuevo / Individual", 
    "📊 Gestión Múltiple de Lotes", 
    "📜 Tabla de Pagables Oficial"
])

# ------------------------------------------
# PESTAÑA 1: COTIZADOR INDIVIDUAL (PAGABLES PERSONALIZADOS)
# ------------------------------------------
with tab1:
    st.subheader("🎯 Cotización de Lote Específico")
    st.markdown("Usa esta pestaña para evaluar lotes individuales con pagables estándar o **pagables personalizados** si requieres ofrecer mejores condiciones para captar el mineral.")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📝 Datos del Lote")
        nombre_lote = st.text_input("Nombre / Código del Lote", value="Lote Especial 01")
        tms = st.number_input("Toneladas Métricas Secas (TMS)", value=50.0, min_value=0.1, step=5.0)
        
        ley_cu = st.number_input("Ley de Cobre - Cu (%)", value=4.50, min_value=0.0, step=0.1)
        ley_au = st.number_input("Ley de Oro - Au (oz/TC)", value=1.80, min_value=0.0, step=0.05)
        ley_ag = st.number_input("Ley de Plata - Ag (oz/TC)", value=210.0, min_value=0.0, step=5.0)

        precio_compra_tms = st.number_input("Precio de Compra al Proveedor ($/TMS)", value=320.0, step=10.0)

    with col2:
        st.markdown("### ⚙️ Configuración de Pagables")
        usar_manual = st.checkbox("Modificar Pagables Manualmente (Lote Nuevo / Compra Especial)", value=False)

        pagable_cu_auto = obtener_pagable_oficial("Cu", ley_cu)
        pagable_au_auto = obtener_pagable_oficial("Au", ley_au)
        pagable_ag_auto = obtener_pagable_oficial("Ag", ley_ag)

        if usar_manual:
            st.warning("⚠️ Modo Manual Activo: Puedes ajustar porcentajes pagables superiores para comprar el lote.")
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

    # Cálculos de Valorización
    val_cu_tms = (ley_cu / 100.0) * precio_cu_tm * (pagable_cu / 100.0)
    val_au_tms = ley_au * precio_au_oz * (pagable_au / 100.0)
    val_ag_tms = ley_ag * precio_ag_oz * (pagable_ag / 100.0)

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

# ------------------------------------------
# PESTAÑA 2: GESTIÓN MÚLTIPLE DE LOTES
# ------------------------------------------
with tab2:
    st.subheader("📊 Tabla Editable de Lotes Múltiples")
    st.markdown("Ingresa varios lotes para calcular automáticamente el costo total, valorización según tabla oficial, ganancias e IGV (2.5%).")

    if "lotes_df" not in st.session_state:
        st.session_state.lotes_df = pd.DataFrame([
            {"Lote": "Lote Alpha", "TMS": 100.0, "Cu (%)": 4.20, "Au (oz/TC)": 1.20, "Ag (oz/TC)": 130.0, "Precio Compra ($/TMS)": 280.0},
            {"Lote": "Lote Beta", "TMS": 150.0, "Cu (%)": 2.50, "Au (oz/TC)": 0.80, "Ag (oz/TC)": 90.0, "Precio Compra ($/TMS)": 190.0},
        ])

    df_editor = st.data_editor(
        st.session_state.lotes_df,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_tabla_lotes"
    )

    if not df_editor.empty:
        # Procesar Liquidación para cada lote en el DataFrame
        def procesar_fila(row):
            t = row["TMS"]
            cu = row["Cu (%)"]
            au = row["Au (oz/TC)"]
            ag = row["Ag (oz/TC)"]
            p_compra = row["Precio Compra ($/TMS)"]

            pag_cu = obtener_pagable_oficial("Cu", cu)
            pag_au = obtener_pagable_oficial("Au", au)
            pag_ag = obtener_pagable_oficial("Ag", ag)

            v_cu = (cu / 100.0) * precio_cu_tm * (pag_cu / 100.0)
            v_au = au * precio_au_oz * (pag_au / 100.0)
            v_ag = ag * precio_ag_oz * (pag_ag / 100.0)

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

        st.subheader("📋 Resultados de Liquidación")
        st.dataframe(df_completo, use_container_width=True)

        # Totales Consolidados
        tms_totales = df_completo["TMS"].sum()
        costo_total_acum = df_completo["Costo Compra Total ($)"].sum()
        venta_total_acum = df_completo["Valor Venta Total ($)"].sum()
        ganancia_acum = df_completo["Ganancia Total ($)"].sum()
        igv_acum = df_completo["IGV 2.5% ($)"].sum()
        factura_acum = df_completo["Factura Total ($)"].sum()

        st.markdown("### 📈 Totales Acumulados")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total TMS", f"{tms_totales:,.2f}")
        c2.metric("Costo Compra Total", f"${costo_total_acum:,.2f}")
        c3.metric("Ganancia Neta Total", f"${ganancia_acum:,.2f}")
        c4.metric("Factura Total (+2.5% IGV)", f"${factura_acum:,.2f}")

# ------------------------------------------
# PESTAÑA 3: TABLA DE PAGABLES OFICIAL
# ------------------------------------------
with tab3:
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
        {"Elemento": "Ag", "Contenido Desde": "0", "Contenido Hasta": "100", "Pagable (%)": "0.0%"},
        {"Elemento": "Ag", "Contenido Desde": "101", "Contenido Hasta": "120", "Pagable (%)": "50.0%"},
        {"Elemento": "Ag", "Contenido Desde": "121", "Contenido Hasta": "150", "Pagable (%)": "60.0%"},
        {"Elemento": "Ag", "Contenido Desde": "151", "Contenido Hasta": "199", "Pagable (%)": "65.0%"},
        {"Elemento": "Ag", "Contenido Desde": "200", "Contenido Hasta": "300", "Pagable (%)": "72.0%"},
        {"Elemento": "Ag", "Contenido Desde": "301", "Contenido Hasta": "500", "Pagable (%)": "75.0%"},
        {"Elemento": "Au", "Contenido Desde": "0", "Contenido Hasta": "1", "Pagable (%)": "0.0%"},
        {"Elemento": "Au", "Contenido Desde": "1.01", "Contenido Hasta": "1.5", "Pagable (%)": "60.0%"},
        {"Elemento": "Au", "Contenido Desde": "1.51", "Contenido Hasta": "2", "Pagable (%)": "69.0%"},
        {"Elemento": "Au", "Contenido Desde": "2.01", "Contenido Hasta": "3", "Pagable (%)": "75.0%"},
        {"Elemento": "Au", "Contenido Desde": "3.01", "Contenido Hasta": "8", "Pagable (%)": "75.0%"},
    ]

    st.table(pd.DataFrame(datos_tabla_oficial))
