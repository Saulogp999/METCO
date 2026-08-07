import streamlit as st
import pandas as pd

# Configuración de la página
st.set_page_config(
    page_title="Cotizador Minero y Blending - CUNI",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Cotizador Minero y Optimizador de Blending")

# Inicialización de estado para la lista de lotes
if "lotes_comprados" not in st.session_state:
    st.session_state.lotes_comprados = []

# Funciones de pagables según la tabla oficial
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

# Sidebar - Cotizaciones Internacionales
st.sidebar.header("🌐 Cotizaciones Internacionales")
precio_cu_tm = st.sidebar.number_input("Precio Cobre ($/TM)", value=9000.0, step=100.0)
precio_au_oz = st.sidebar.number_input("Precio Oro ($/oz)", value=2400.0, step=10.0)
precio_ag_oz = st.sidebar.number_input("Precio Plata ($/oz)", value=28.0, step=0.5)

# Pestañas principales
tab1, tab2 = st.tabs(["🎯 Cotizar Lote Individual", "🔄 Blending / Mezcla de Lotes"])

with tab1:
    st.subheader("Cotización de Lote Nuevo")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        nombre_lote = st.text_input("Nombre del Lote", value=f"Lote {len(st.session_state.lotes_comprados) + 1}")
        tms = st.number_input("Toneladas Métricas Secas (TMS)", value=100.0, step=10.0)
        precio_compra_tms = st.number_input("Precio de Compra Pactado ($/TM)", value=400.0, step=10.0)
    
    with col2:
        ley_cu = st.number_input("Ley Cobre Cu (%)", value=4.5, step=0.1)
        ley_au_gt = st.number_input("Ley Oro Au (g/t)", value=2.2, step=0.1)
        ley_ag_gt = st.number_input("Ley Plata Ag (g/t)", value=210.0, step=5.0)

    with col3:
        st.markdown("### Configuración de Pagables")
        usar_pagables_manuales = st.checkbox("Modificar pagables manualmente (Compra Especial)")
        
        pagable_cu_auto = obtener_pagable_cu(ley_cu)
        pagable_au_auto = obtener_pagable_au(ley_au_gt)
        pagable_ag_auto = obtener_pagable_ag(ley_ag_gt)
        
        if usar_pagables_manuales:
            pagable_cu = st.number_input("Pagable Cu (%)", value=float(pagable_cu_auto), step=1.0)
            pagable_au = st.number_input("Pagable Au (%)", value=float(pagable_au_auto), step=1.0)
            pagable_ag = st.number_input("Pagable Ag (%)", value=float(pagable_ag_auto), step=1.0)
        else:
            pagable_cu = pagable_cu_auto
            pagable_au = pagable_au_auto
            pagable_ag = pagable_ag_auto
            st.info(f"Pagables Tabla -> Cu: {pagable_cu}% | Au: {pagable_au}% | Ag: {pagable_ag}%")

    # Conversión g/t a oz/TM (1 oz = 31.1035 g)
    au_oz_tm = ley_au_gt / 31.1035
    ag_oz_tm = ley_ag_gt / 31.1035

    # Valorización de Venta
    val_cu_tm = (ley_cu / 100.0) * (pagable_cu / 100.0) * precio_cu_tm
    val_au_tm = au_oz_tm * (pagable_au / 100.0) * precio_au_oz
    val_ag_tm = ag_oz_tm * (pagable_ag / 100.0) * precio_ag_oz

    valor_venta_tm = val_cu_tm + val_au_tm + val_ag_tm
    valor_venta_total = valor_venta_tm * tms

    costo_compra_total = precio_compra_tms * tms
    ganancia_neta = valor_venta_total - costo_compra_total

    # Cálculo de IGV al 2.5%
    igv_monto = valor_venta_total * 0.025
    factura_total = valor_venta_total + igv_monto

    st.markdown("---")
    st.subheader("💵 Resultados Financieros del Lote")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Costo Total Compra", f"${costo_compra_total:,.2f}")
    m2.metric("Valor Venta Total", f"${valor_venta_total:,.2f}")
    m3.metric("Ganancia Neta", f"${ganancia_neta:,.2f}")
    m4.metric("Total Facturado (IGV 2.5%)", f"${factura_total:,.2f}")

    st.markdown(f"**Detalle Factura:** Subtotal Base: **${valor_venta_total:,.2f}** | IGV (2.5%): **${igv_monto:,.2f}** | Total Factura: **${factura_total:,.2f}**")

    if st.button("➕ Confirmar y Agregar este Lote a la Lista General"):
        nuevo_lote = {
            "Lote": nombre_lote,
            "TMS": tms,
            "Ley Cu (%)": ley_cu,
            "Ley Au (g/t)": ley_au_gt,
            "Ley Ag (g/t)": ley_ag_gt,
            "Precio Compra ($/TM)": precio_compra_tms,
            "Pagable Cu (%)": pagable_cu,
            "Pagable Au (%)": pagable_au,
            "Pagable Ag (%)": pagable_ag,
            "Costo Total ($)": costo_compra_total,
            "Venta Total ($)": valor_venta_total,
            "Ganancia ($)": ganancia_neta
        }
        st.session_state.lotes_comprados.append(nuevo_lote)
        st.success(f"¡{nombre_lote} agregado con éxito para el cálculo de Blending!")

with tab2:
    st.subheader("📊 Lista de Lotes Comprados y Mezcla Ponderada (Blending)")
    
    if len(st.session_state.lotes_comprados) == 0:
        st.warning("No hay lotes agregados aún. Cotiza un lote en la pestaña anterior y haz clic en 'Confirmar y Agregar'.")
    else:
        df_lotes = pd.DataFrame(st.session_state.lotes_comprados)
        st.dataframe(df_lotes, use_container_width=True)

        if st.button("🗑️ Limpiar Lista de Lotes"):
            st.session_state.lotes_comprados = []
            st.rerun()

        # Cálculos de Blending
        tms_totales = df_lotes["TMS"].sum()
        
        # Leyes Ponderadas por Toneladas
        cu_ponderado = (df_lotes["TMS"] * df_lotes["Ley Cu (%)"]).sum() / tms_totales
        au_ponderado = (df_lotes["TMS"] * df_lotes["Ley Au (g/t)"]).sum() / tms_totales
        ag_ponderado = (df_lotes["TMS"] * df_lotes["Ley Ag (g/t)"]).sum() / tms_totales
        
        costo_compra_mezcla = df_lotes["Costo Total ($)"].sum()
        venta_lotes_individuales = df_lotes["Venta Total ($)"].sum()

        # Recálculo de Pagables según escala de la mezcla
        pagable_cu_blend = obtener_pagable_cu(cu_ponderado)
        pagable_au_blend = obtener_pagable_au(au_ponderado)
        pagable_ag_blend = obtener_pagable_ag(ag_ponderado)

        # Re-valorización del concentrado mezclado
        au_blend_oz_tm = au_ponderado / 31.1035
        ag_blend_oz_tm = ag_ponderado / 31.1035

        v_cu_blend = (cu_ponderado / 100.0) * (pagable_cu_blend / 100.0) * precio_cu_tm
        v_au_blend = au_blend_oz_tm * (pagable_au_blend / 100.0) * precio_au_oz
        v_ag_blend = ag_blend_oz_tm * (pagable_ag_blend / 100.0) * precio_ag_oz

        venta_mezcla_tm = v_cu_blend + v_au_blend + v_ag_blend
        venta_mezcla_total = venta_mezcla_tm * tms_totales
        ganancia_mezcla_total = venta_mezcla_total - costo_compra_mezcla

        beneficio_extra_blending = venta_mezcla_total - venta_lotes_individuales

        st.markdown("---")
        st.subheader("🧪 Resultado del Blending Ponderado")
        
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("TMS Totales", f"{tms_totales:,.2f}")
        b2.metric("Ley Mezcla Cu (%)", f"{cu_ponderado:.2f}%", f"Pagable: {pagable_cu_blend}%")
        b3.metric("Ley Mezcla Au (g/t)", f"{au_ponderado:.2f} g/t", f"Pagable: {pagable_au_blend}%")
        b4.metric("Ley Mezcla Ag (g/t)", f"{ag_ponderado:.2f} g/t", f"Pagable: {pagable_ag_blend}%")

        st.markdown("---")
        g1, g2, g3 = st.columns(3)
        g1.metric("Venta Total por Mezcla", f"${venta_mezcla_total:,.2f}")
        g2.metric("Ganancia Total Mezclada", f"${ganancia_mezcla_total:,.2f}")
        g3.metric("Beneficio Extra por Blending", f"${beneficio_extra_blending:,.2f}")
