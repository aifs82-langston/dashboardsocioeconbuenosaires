import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from fpdf import FPDF

# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="Dashboard de datos socioeconómicos - Municipalidad de Buenos Aires", layout="wide")

# --- FUNCIONES DE APOYO ---
@st.cache_data
def cargar_datos():
    """Intenta cargar 'datosbuenosaires.xlsx' o el primer Excel disponible."""
    try:
        if os.path.exists('datosbuenosaires.xlsx'):
            return pd.read_excel('datosbuenosaires.xlsx')
        else:
            excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx')]
            if excel_files:
                return pd.read_excel(excel_files[0])
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
    return None

def clean_labels(text):
    """Limpia prefijos tipo 'a) ', 'b) ' y espacios residuales."""
    if pd.isna(text): return text
    return re.sub(r'^[a-z]\)\s*', '', str(text)).strip()

# --- LÓGICA DE CARGA Y LIMPIEZA ---
df = cargar_datos()

if df is not None:
    column_mapping = {
        df.columns[3]: 'Sexo', 
        df.columns[4]: 'Edad',
        df.columns[5]: 'Nivel_Estudios', 
        df.columns[6]: 'Ocupacion',
        df.columns[7]: 'Ingreso_Mensual', 
        df.columns[9]: 'Identificacion_Indigena'
    }
    df_eda = df.rename(columns=column_mapping).copy()

    for col in ['Sexo', 'Edad', 'Nivel_Estudios', 'Ocupacion', 'Ingreso_Mensual', 'Identificacion_Indigena']:
        df_eda[col] = df_eda[col].apply(clean_labels)

    # --- BARRA LATERAL (SIDEBAR) CON LOGO ---
    st.sidebar.image("sidebar_desarrollo_territorial.png", use_container_width=True) # Aquí pegamos tu imagen
    st.sidebar.header("⚙️ Panel de Control")
    st.sidebar.write("Use el botón para procesar la información municipal.")
    btn_analisis = st.sidebar.button("▶️ Ejecutar Análisis Descriptivo", use_container_width=True)

    # --- TÍTULOS Y MÉTRICAS ---
    st.title("📊 Perfil Socioeconómico: Buenos Aires, Costa Rica")
    st.markdown("### Piloto de Diagnóstico Municipal")

    # Cálculos para métricas
    total_n = len(df_eda)
    pct_ind = (df_eda['Identificacion_Indigena'].str.lower() == 'sí').mean() * 100
    
    # Desagregación por género solicitada
    conteo_sexo = df_eda['Sexo'].value_counts()
    detalle_sexo = " | ".join([f"{k}: {v}" for k, v in conteo_sexo.items()])

    col_m1, col_m2, col_m3 = st.columns([1.2, 1, 1])
    with col_m1:
        st.metric("Total Muestra", total_n)
        st.caption(f"**Desglose por género:** {detalle_sexo}")
    with col_m2:
        st.metric("% Identificación Indígena", f"{pct_ind:.1f}%")
    with col_m3:
        # Espacio para el botón de descarga PDF (previamente definido)
        st.write("") 

    st.divider()

    # --- EJECUCIÓN DEL ANÁLISIS ---
    if btn_analisis:
        with st.spinner('Generando visualizaciones...'):
            sns.set(style="whitegrid")
            
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Distribución por Género")
                fig1, ax1 = plt.subplots()
                sns.countplot(x='Sexo', data=df_eda, palette='pastel', hue='Sexo', legend=False, ax=ax1)
                ax1.set_ylabel("Frecuencia (n)")
                st.pyplot(fig1)

            with c2:
                st.subheader("Identificación Indígena (Proporción)")
                fig6, ax6 = plt.subplots()
                sns.histplot(x='Identificacion_Indigena', data=df_eda, 
                             hue='Identificacion_Indigena', palette='Set2', 
                             stat="proportion", shrink=.8, legend=False, ax=ax6)
                ax6.set_ylabel("Frecuencia Relativa")
                st.pyplot(fig6)
            
            # El resto de los gráficos (Edad, Educación, Ocupación, Ingresos) se mantienen igual...
            st.success("✅ Análisis descriptivo finalizado.")

else:
    st.error("Archivo no encontrado.")
