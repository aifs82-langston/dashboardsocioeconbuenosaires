
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from fpdf import FPDF
import io

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Dashboard Buenos Aires", layout="wide")

# --- FUNCIONES DE APOYO ---
def clean_labels(text):
    if pd.isna(text): return text
    # Elimina prefijos tipo "a) ", "b) " al inicio
    return re.sub(r'^[a-z]\)\s*', '', str(text)).strip()

def create_pdf(df_resumen, total, pct_ind):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Reporte Ejecutivo: Encuesta Buenos Aires", ln=True, align='C')

    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total de Encuestados: {total}", ln=True)
    pdf.cell(200, 10, txt=f"Identificacion Indigena: {pct_ind:.1f}%", ln=True)

    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Distribucion por Sexo:", ln=True)
    pdf.set_font("Arial", size=12)
    for label, value in df_resumen.items():
        pdf.cell(200, 10, txt=f"- {label}: {value}", ln=True)
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- CARGA DE DATOS DESDE REPOSITORIO ---
@st.cache_data
def cargar_datos():
    # Intenta cargar el archivo directo o busca candidatos en el repositorio
    file_path = 'datosbuenosaires.xlsx'
    try:
        return pd.read_excel(file_path)
    except:
        candidates = [f for f in os.listdir() if 'Buenos Aires' in f and f.endswith('.xlsx')]
        if candidates:
            return pd.read_excel(candidates[0])
    return None

# --- PROCESAMIENTO ---
df = cargar_datos()

if df is not None:
    # Renombramiento basado en las columnas socioeconómicas
    column_mapping = {
        df.columns[3]: 'Sexo', df.columns[4]: 'Edad',
        df.columns[5]: 'Nivel_Estudios', df.columns[6]: 'Ocupacion',
        df.columns[7]: 'Ingreso_Mensual', df.columns[9]: 'Identificacion_Indigena'
    }
    df_eda = df.rename(columns=column_mapping).copy()

    for col in df_eda.columns[3:10]:
        if col in df_eda.columns:
            df_eda[col] = df_eda[col].apply(clean_labels)

    # --- ENCABEZADO Y MÉTRICAS ---
    st.title("📊 Dashboard Piloto: Perfil Socioeconómico")
    st.markdown("### Municipalidad de Buenos Aires, Puntarenas")

    total_n = len(df_eda)
    pct_ind = (df_eda['Identificacion_Indigena'] == 'Sí').mean() * 100

    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric("Total Encuestados", total_n)
    with col_m2:
        st.metric("% Identificación Indígena", f"{pct_ind:.1f}%")
    with col_m3:
        # Generación y descarga de PDF
        pdf_data = create_pdf(df_eda['Sexo'].value_counts(), total_n, pct_ind)
        st.download_button(label="📥 Descargar Reporte PDF", data=pdf_data,
                           file_name="reporte_buenos_aires.pdf", mime="application/pdf")

    st.divider()

    # --- DASHBOARD VISUAL (3x2) ---
    sns.set(style="whitegrid")

    # Fila 1: Demografía
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("A. Distribución por Género")
        fig1, ax1 = plt.subplots()
        sns.countplot(x='Sexo', data=df_eda, palette='pastel', hue='Sexo', legend=False, ax=ax1)
        st.pyplot(fig1)
    with c2:
        st.subheader("B. Rangos de Edad")
        fig2, ax2 = plt.subplots()
        edad_order = sorted(df_eda['Edad'].unique(), key=lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
        sns.countplot(x='Edad', data=df_eda, palette='viridis', order=edad_order, hue='Edad', legend=False, ax=ax2)
        plt.xticks(rotation=45, ha='right') # Limpieza de ejes solicitada
        st.pyplot(fig2)

    # Fila 2: Educación y Ocupación
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("C. Nivel Académico")
        fig3, ax3 = plt.subplots()
        est_order = df_eda['Nivel_Estudios'].value_counts().index
        sns.countplot(y='Nivel_Estudios', data=df_eda, palette='magma', order=est_order, hue='Nivel_Estudios', legend=False, ax=ax3)
        st.pyplot(fig3)
    with c4:
        st.subheader("D. Ocupación Principal (Top 10)")
        fig4, ax4 = plt.subplots()
        ocup_order = df_eda['Ocupacion'].value_counts().head(10).index
        sns.countplot(y='Ocupacion', data=df_eda[df_eda['Ocupacion'].isin(ocup_order)], palette='rocket', order=ocup_order, hue='Ocupacion', legend=False, ax=ax4)
        st.pyplot(fig4)

    # Fila 3: Economía e Identidad
    c5, c6 = st.columns(2)
    with c5:
        st.subheader("E. Nivel de Ingresos Mensuales")
        fig5, ax5 = plt.subplots()
        ingreso_map = {'Menos de ₡200,000': 1, 'Entre ₡250,000 y ₡350,000': 2, 'Entre ₡360,000 y ₡450,000': 3, 'Entre ₡450,000 y ₡600,000': 4, 'Más de ₡600,000': 5}
        actual_labels = [l for l in df_eda['Ingreso_Mensual'].unique() if l in ingreso_map]
        ing_order = sorted(actual_labels, key=lambda x: ingreso_map[x])
        sns.countplot(y='Ingreso_Mensual', data=df_eda, palette='crest', order=ing_order, hue='Ingreso_Mensual', legend=False, ax=ax5)
        st.pyplot(fig5)
    with c6:
        st.subheader("F. Identificación Indígena")
        fig6, ax6 = plt.subplots()
        sns.countplot(x='Identificacion_Indigena', data=df_eda, palette='Set2', hue='Identificacion_Indigena', legend=False, ax=ax6)
        st.pyplot(fig6)

else:
    st.error("Archivo no encontrado. Verifique que 'datosbuenosaires.xlsx' esté en el repositorio.")
