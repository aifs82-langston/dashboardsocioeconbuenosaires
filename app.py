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

def generar_pdf_completo(conteo_sexo, total, pct_ind, lista_graficos):
    """Genera un PDF que incluye el resumen y los gráficos del dashboard."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Título
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Reporte Ejecutivo: Datos Socioeconomicos - Buenos Aires", ln=True, align='C')
    
    # Métricas
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total de la Muestra: {total}", ln=True)
    pdf.cell(200, 10, txt=f"Identificacion Indigena: {pct_ind:.1f}%", ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Resumen por Sexo:", ln=True)
    pdf.set_font("Arial", size=12)
    for label, value in conteo_sexo.items():
        pdf.cell(200, 8, txt=f"- {label}: {value}", ln=True)
    
    # Agregar Gráficos
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Visualizaciones del Dashboard:", ln=True)
    
    for fig in lista_graficos:
        # Guardar gráfico temporalmente
        with NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
            fig.savefig(tmpfile.name, format='png', bbox_inches='tight')
            pdf.image(tmpfile.name, x=10, w=180)
            pdf.ln(5)
        os.unlink(tmpfile.name) # Borrar archivo temporal

    return pdf.output(dest='S').encode('latin-1', 'replace')

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

    # --- BARRA LATERAL (SIDEBAR) ---
    # Asegúrate de tener esta imagen en tu GitHub
    if os.path.exists("sidebar_desarrollo_territorial.png"):
        st.sidebar.image("sidebar_desarrollo_territorial.png", use_container_width=True)
    
    st.sidebar.header("⚙️ Panel de Control")
    st.sidebar.write("Use el botón para procesar la información municipal.")
    btn_analisis = st.sidebar.button("▶️ Ejecutar Análisis Descriptivo", use_container_width=True)

    # --- TÍTULOS Y MÉTRICAS ---
    st.title("📊 Perfil Socioeconómico: Buenos Aires, Costa Rica")
    st.markdown("### Piloto de Diagnóstico Municipal")

    total_n = len(df_eda)
    pct_ind = (df_eda['Identificacion_Indigena'].str.lower() == 'sí').mean() * 100
    conteo_sexo = df_eda['Sexo'].value_counts()
    detalle_sexo = " | ".join([f"{k}: {v}" for k, v in conteo_sexo.items()])

    col_m1, col_m2, col_m3 = st.columns([1.2, 1, 1])
    with col_m1:
        st.metric("Total Muestra", total_n)
        st.caption(f"**Desglose:** {detalle_sexo}")
    with col_m2:
        st.metric("% Identificación Indígena", f"{pct_ind:.1f}%")
    
    st.divider()

    # --- EJECUCIÓN DEL ANÁLISIS ---
    if btn_analisis:
        with st.spinner('Generando visualizaciones...'):
            sns.set(style="whitegrid")
            lista_de_figuras = [] # Aquí guardaremos los gráficos para el PDF
            
            # FILA 1
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Distribución por Género")
                fig1, ax1 = plt.subplots()
                sns.countplot(x='Sexo', data=df_eda, palette='pastel', hue='Sexo', legend=False, ax=ax1)
                ax1.set_xlabel(""); ax1.set_ylabel("Frecuencia (n)")
                st.pyplot(fig1)
                lista_de_figuras.append(fig1)

            with c2:
                st.subheader("Rangos de Edad")
                fig2, ax2 = plt.subplots()
                edad_order = sorted(df_eda['Edad'].unique(), key=lambda x: int(re.search(r'\d+', str(x)).group()) if re.search(r'\d+', str(x)) else 0)
                sns.countplot(x='Edad', data=df_eda, palette='viridis', order=edad_order, hue='Edad', legend=False, ax=ax2)
                plt.xticks(rotation=45, ha='right')
                ax2.set_xlabel(""); ax2.set_ylabel("Frecuencia (n)")
                st.pyplot(fig2)
                lista_de_figuras.append(fig2)

            # FILA 2
            c3, c4 = st.columns(2)
            with c3:
                st.subheader("Nivel Académico Alcanzado")
                fig3, ax3 = plt.subplots()
                est_order = df_eda['Nivel_Estudios'].value_counts().index
                sns.countplot(y='Nivel_Estudios', data=df_eda, palette='magma', order=est_order, hue='Nivel_Estudios', legend=False, ax=ax3)
                ax3.set_xlabel("Frecuencia (n)"); ax3.set_ylabel("")
                st.pyplot(fig3)
                lista_de_figuras.append(fig3)

            with c4:
                st.subheader("Ocupación Principal (Top 10)")
                fig4, ax4 = plt.subplots()
                ocup_order = df_eda['Ocupacion'].value_counts().head(10).index
                sns.countplot(y='Ocupacion', data=df_eda[df_eda['Ocupacion'].isin(ocup_order)], palette='rocket', order=ocup_order, hue='Ocupacion', legend=False, ax=ax4)
                ax4.set_xlabel("Frecuencia (n)"); ax4.set_ylabel("")
                st.pyplot(fig4)
                lista_de_figuras.append(fig4)

            # FILA 3
            c5, c6 = st.columns(2)
            with c5:
                st.subheader("Nivel de Ingresos Mensuales")
                fig5, ax5 = plt.subplots()
                ing_map = {'Menos de ₡200,000': 1, 'Entre ₡250,000 y ₡350,000': 2, 'Entre ₡360,000 y ₡450,000': 3, 'Entre ₡450,000 y ₡600,000': 4, 'Más de ₡600,000': 5}
                label_list = [l for l in df_eda['Ingreso_Mensual'].unique() if l in ing_map]
                ing_order = sorted(label_list, key=lambda x: ing_map[x])
                sns.countplot(y='Ingreso_Mensual', data=df_eda, palette='crest', order=ing_order, hue='Ingreso_Mensual', legend=False, ax=ax5)
                ax5.set_xlabel("Frecuencia (n)"); ax5.set_ylabel("")
                st.pyplot(fig5)
                lista_de_figuras.append(fig5)

            with c6:
                st.subheader("Identificación Indígena (Proporción)")
                fig6, ax6 = plt.subplots()
                sns.histplot(x='Identificacion_Indigena', data=df_eda, hue='Identificacion_Indigena', palette='Set2', stat="proportion", shrink=.8, legend=False, ax=ax6)
                ax6.set_xlabel(""); ax6.set_ylabel("Frecuencia Relativa")
                st.pyplot(fig6)
                lista_de_figuras.append(fig6)

            # BOTÓN DE DESCARGA (Se genera dentro del análisis para tener acceso a lista_de_figuras)
            st.divider()
            pdf_bytes = generar_pdf_completo(conteo_sexo, total_n, pct_ind, lista_de_figuras)
            st.download_button(
                label="📥 Descargar Reporte PDF Completo (con Gráficos)",
                data=pdf_bytes,
                file_name="reporte_buenos_aires_completo.pdf",
                mime="application/pdf",
                use_container_width=True
            )
            st.success("✅ Análisis descriptivo finalizado. El reporte PDF con gráficos ya está disponible para descarga.")
    else:
        st.info("💡 Haga clic en el botón 'Ejecutar Análisis' para generar las visualizaciones y el reporte PDF.")

else:
    st.error("No se encontró el archivo de datos en el repositorio de GitHub.")
