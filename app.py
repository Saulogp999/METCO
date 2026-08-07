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
