import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
from fpdf import FPDF
import io
from PIL import Image

# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="Dashboard Socioeconómico - Buenos Aires", layout="wide")

# --- FUNCIONES DE APOYO ---
@st.cache_data
def cargar_datos():
    try:
        if os.path.exists('datosbuenosaires.xlsx'):
            return pd.read_excel('datosbuenosaires.xlsx')
        else:
            excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx')]
            return pd.read_excel(excel_files[0]) if excel_files else None
    except Exception as e:
        st.error(f"Error al leer el archivo: {e}")
    return None

def clean_labels(text):
    if pd.isna(text): return text
    return re.sub(r'^[a-z]\)\s*', '', str(text)).strip()

# --- NUEVA FUNCIÓN DE PDF CON GRÁFICOS ---
def generar_reporte_completo_pdf(df_eda, total, pct_ind, figuras):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Portada
    pdf.add_page()
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(200, 20, txt="Reporte Socioeconómico Completo", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 10, txt="Municipalidad de Buenos Aires, Costa Rica", ln=True, align='C')
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Indicadores Clave:", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(200, 8, txt=f"- Muestra Total: {total} encuestados", ln=True)
    pdf.cell(200, 8, txt=f"- Identificacion Indigena: {pct_ind:.1f}%", ln=True)
    
    # Insertar Gráficos
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Analisis Visual de Datos:", ln=True)
    
    for i, fig in enumerate(figuras):
        # Guardar cada figura en un buffer de memoria
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        buf.seek(0)
        
        # Guardar temporalmente para que FPDF lo lea
        temp_img_path = f"temp_fig_{i}.png"
        img = Image.open(buf)
        img.save(temp_img_path)
        
        # Añadir al PDF (2 gráficos por página para que se vean bien)
        if i % 2 == 0 and i > 0:
            pdf.add_page()
            
        pdf.image(temp_img_path, x=10, w=180)
        os.remove(temp_img_path) # Limpiar archivo temporal

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- LÓGICA DE CARGA ---
df = cargar_datos()

if df is not None:
    # Procesamiento igual que antes...
    column_mapping = {
        df.columns[3]: 'Sexo', df.columns[4]: 'Edad',
        df.columns[5]: 'Nivel_Estudios', df.columns[6]: 'Ocupacion',
        df.columns[7]: 'Ingreso_Mensual', df.columns[9]: 'Identificacion_Indigena'
    }
    df_eda = df.rename(columns=column_mapping).copy()
    for col in df_eda.columns[3:10]:
        if col in df_eda.columns: df_eda[col] = df_eda[col].apply(clean_labels)

    # Sidebar con logo
    st.sidebar.image("sidebar_desarrollo_territorial.png", use_container_width=True)
    st.sidebar.header("⚙️ Panel de Control")
    btn_analisis = st.sidebar.button("▶️ Ejecutar Análisis Descriptivo", use_container_width=True)

    # Métricas principales
    st.title("📊 Perfil Socioeconómico: Buenos Aires")
    total_n = len(df_eda)
    pct_ind = (df_eda['Identificacion_Indigena'].str.lower() == 'sí').mean() * 100

    if btn_analisis:
        # Generamos los gráficos y los guardamos en una lista
        figuras_para_pdf = []
        sns.set(style="whitegrid")
        
        c1, c2 = st.columns(2)
        
        # Gráfico 1
        fig1, ax1 = plt.subplots()
        sns.countplot(x='Sexo', data=df_eda, ax=ax1)
        ax1.set_title("Distribucion por Genero")
        st.pyplot(fig1)
        figuras_para_pdf.append(fig1)

        # Gráfico 2
        fig2, ax2 = plt.subplots()
        sns.histplot(x='Identificacion_Indigena', data=df_eda, stat="proportion", ax=ax2)
        ax2.set_title("Identificacion Indigena")
        st.pyplot(fig2)
        figuras_para_pdf.append(fig2)

        # Botón de Descarga que ahora sí usa los gráficos
        st.divider()
        pdf_bytes = generar_reporte_completo_pdf(df_eda, total_n, pct_ind, figuras_para_pdf)
        st.download_button(
            label="📥 Descargar Reporte PDF con Gráficos",
            data=pdf_bytes,
            file_name="reporte_completo_buenos_aires.pdf",
            mime="application/pdf"
        )






