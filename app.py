import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import re
import os
import io
from fpdf import FPDF
from tempfile import NamedTemporaryFile

# 1. CONFIGURACIÓN PROFESIONAL
st.set_page_config(page_title="Dashboard Socioeconómico - Municipalidad de Buenos Aires, Costa Rica", layout="wide")

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
    if pd.isna(text): return text
    return re.sub(r'^[a-z]\)\s*', '', str(text)).strip()

def generar_pdf_completo(conteo_sexo, total, pct_ind, lista_graficos, titulos_graficos):
    """Genera un PDF profesional eliminando los títulos internos de los gráficos para evitar duplicidad."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Encabezado
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Reporte Ejecutivo: Datos Socioeconomicos", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(200, 10, txt="Municipalidad de Buenos Aires, Costa Rica - Piloto 2026", ln=True, align='C')
    
    # Métricas principales
    pdf.set_font("Arial", 'B', 12)
    pdf.ln(10)
    pdf.cell(200, 10, txt="Resumen de Indicadores Clave:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.cell(200, 8, txt=f"Total de la Muestra: {total} encuestados", ln=True)
    pdf.cell(200, 8, txt=f"Identificacion Indigena: {pct_ind:.1f}%", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt="Desglose por Sexo:", ln=True)
    pdf.set_font("Arial", size=11)
    for label, value in conteo_sexo.items():
        pdf.cell(200, 7, txt=f"- {label}: {value}", ln=True)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Visualizaciones Detalladas:", ln=True)
    
    # Insertar Gráficos con Títulos de PDF
    for i, fig in enumerate(lista_graficos):
        pdf.ln(8)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt=f"{titulos_graficos[i]}", ln=True) 
        
        # ELIMINACIÓN DE TÍTULO INTERNO PARA EL PDF
        # Obtenemos el eje actual y borramos su título antes de guardar la imagen
        ax = fig.gca()
        ax.set_title("") 
        
        with NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            # bbox_inches='tight' asegura que los ejes se vean bien sin márgenes blancos excesivos
            fig.savefig(tmpfile.name, format='png', bbox_inches='tight', dpi=150)
            pdf.image(tmpfile.name, x=20, w=160)
        os.unlink(tmpfile.name)
        
        # Salto de página cada 2 gráficos
        if (i + 1) % 2 == 0 and (i + 1) < len(lista_graficos):
            pdf.add_page()

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- LÓGICA DE DATOS ---
df = cargar_datos()

if df is not None:
    column_mapping = {
        df.columns[3]: 'Sexo', df.columns[4]: 'Edad',
        df.columns[5]: 'Nivel_Estudios', df.columns[6]: 'Ocupacion',
        df.columns[7]: 'Ingreso_Mensual', df.columns[9]: 'Identificacion_Indigena'
    }
    df_eda = df.rename(columns=column_mapping).copy()
    for col in ['Sexo', 'Edad', 'Nivel_Estudios', 'Ocupacion', 'Ingreso_Mensual', 'Identificacion_Indigena']:
        df_eda[col] = df_eda[col].apply(clean_labels)

    # Sidebar
    if os.path.exists("sidebar_desarrollo_territorial.png"):
        st.sidebar.image("sidebar_desarrollo_territorial.png", use_container_width=True)
    st.sidebar.header("⚙️ Panel de Control")
    btn_analisis = st.sidebar.button("▶️ Ejecutar Análisis Descriptivo", use_container_width=True)

    # Métricas Dashboard
    st.title("📊 Perfil Socioeconómico: Municipalidad de Buenos Aires, Costa Rica.")
    st.markdown("Alfredo Ibrahim Flores Sarria ©2026")
    
    total_n = len(df_eda)
    pct_ind = (df_eda['Identificacion_Indigena'].str.lower() == 'sí').mean() * 100
    conteo_sexo = df_eda['Sexo'].value_counts()
    detalle_sexo = " | ".join([f"{k}: {v}" for k, v in conteo_sexo.items()])

    col_m1, col_m2 = st.columns([2, 1])
    with col_m1:
        st.metric("Total Muestra", total_n)
        st.caption(f"**Desglose:** {detalle_sexo}")
    with col_m2:
        st.metric("% Identificación Indígena", f"{pct_ind:.1f}%")
    
    st.divider()

    if btn_analisis:
        with st.spinner('Procesando reporte completo...'):
            sns.set(style="whitegrid")
            figuras = []
            titulos = []
            
            # FILA 1
            c1, c2 = st.columns(2)
            with c1:
                t1 = "Distribución por Género"
                st.subheader(t1)
                fig1, ax1 = plt.subplots()
                sns.countplot(x='Sexo', data=df_eda, palette='pastel', ax=ax1)
                ax1.set_ylabel("Frecuencia (n)")
                st.pyplot(fig1)
                figuras.append(fig1); titulos.append(t1)

            with c2:
                t2 = "Rangos de Edad"
                st.subheader(t2)
                fig2, ax2 = plt.subplots()
                edad_order = sorted(df_eda['Edad'].unique(), key=lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else 0)
                sns.countplot(x='Edad', data=df_eda, order=edad_order, ax=ax2)
                plt.xticks(rotation=45, ha='right')
                ax2.set_ylabel("Frecuencia (n)")
                st.pyplot(fig2)
                figuras.append(fig2); titulos.append(t2)

            # FILA 2
            c3, c4 = st.columns(2)
            with c3:
                t3 = "Nivel Académico Alcanzado"
                st.subheader(t3)
                fig3, ax3 = plt.subplots()
                sns.countplot(y='Nivel_Estudios', data=df_eda, palette='magma', ax=ax3)
                ax3.set_xlabel("Frecuencia (n)")
                st.pyplot(fig3)
                figuras.append(fig3); titulos.append(t3)

            with c4:
                t4 = "Ocupación Principal (Top 10)"
                st.subheader(t4)
                fig4, ax4 = plt.subplots()
                ocup_top = df_eda['Ocupacion'].value_counts().head(10).index
                sns.countplot(y='Ocupacion', data=df_eda[df_eda['Ocupacion'].isin(ocup_top)], order=ocup_top, ax=ax4)
                ax4.set_xlabel("Frecuencia (n)")
                st.pyplot(fig4)
                figuras.append(fig4); titulos.append(t4)

            # FILA 3
            c5, c6 = st.columns(2)
            with c5:
                t5 = "Nivel de Ingresos Mensuales"
                st.subheader(t5)
                fig5, ax5 = plt.subplots()
                ing_map = {'Menos de ₡200,000': 1, 'Entre ₡250,000 y ₡350,000': 2, 'Entre ₡360,000 y ₡450,000': 3, 'Entre ₡450,000 y ₡600,000': 4, 'Más de ₡600,000': 5}
                ing_order = sorted([l for l in df_eda['Ingreso_Mensual'].unique() if l in ing_map], key=lambda x: ing_map[x])
                sns.countplot(y='Ingreso_Mensual', data=df_eda, order=ing_order, ax=ax5)
                ax5.set_xlabel("Frecuencia (n)")
                st.pyplot(fig5)
                figuras.append(fig5); titulos.append(t5)

            with c6:
                t6 = "Identificación Indígena (Proporción)"
                st.subheader(t6)
                fig6, ax6 = plt.subplots()
                sns.histplot(x='Identificacion_Indigena', data=df_eda, stat="proportion", ax=ax6)
                ax6.set_ylabel("Frecuencia Relativa")
                st.pyplot(fig6)
                figuras.append(fig6); titulos.append(t6)

            st.divider()
            # Pasamos las figuras para que el PDF las procese
            pdf_bytes = generar_pdf_completo(conteo_sexo, total_n, pct_ind, figuras, titulos)
            st.download_button(
                label="📥 Descargar Reporte PDF Completo",
                data=pdf_bytes,
                file_name="reporte_buenos_aires_final.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.success("✅ Reporte PDF generado sin títulos duplicados.")
else:
    st.error("Archivo no encontrado.")
