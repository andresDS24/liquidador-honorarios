import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO
from fpdf import FPDF

# --- CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="Liquidador de Honorarios", layout="wide")
VALOR_UVR = 1270
VALOR_UVR_ISS_ANESTESIA = 960

st.title("🩺 Plataforma de Liquidación de Honorarios Médicos")
st.markdown("Carga el archivo de servicios y obtén la liquidación por profesional según especialidad.")

# --- SUBIR ARCHIVO ---
col_up1, col_up2 = st.columns([3, 1])
with col_up1:
    archivo = st.file_uploader("📎 Carga archivo Excel", type=["xlsx"])
with col_up2:
    boton_manual = st.button("➕ Cargar datos manualmente")

# --- CARGAR HOMOLOGACIÓN ---
def cargar_tabla_homologacion():
    try:
        return pd.read_excel("tabla_homologacion.xlsx")
    except:
        return pd.DataFrame(columns=["SOAT", "CUPS"])

homologacion_df = cargar_tabla_homologacion()

# --- FUNCIONES ---
def generar_pdf(df, nombre):
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 10, f"Liquidación de Honorarios - {nombre}", ln=True)
    pdf.ln(5)

    columnas = df.columns.tolist()
    for col in columnas:
        pdf.cell(40, 8, col, border=1)
    pdf.ln()
    for _, row in df.iterrows():
        for item in row:
            pdf.cell(40, 8, str(item), border=1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin1')

if boton_manual:
    st.subheader("📝 Ingreso manual de servicio")
    with st.form("form_ingreso_manual"):
        col1, col2 = st.columns(2)
        with col1:
            especialista = st.text_input("Nombre del especialista")
            especialidad = st.text_input("Especialidad")
            plan = st.text_input("Plan de beneficios")
            descripcion = st.text_input("Descripción del servicio")
        with col2:
            codigo_soat = st.text_input("Código SOAT")
            via = st.text_input("Vía de Liquidación")
            valor_total = st.number_input("Valor Total", min_value=0.0, step=1000.0)
            valor_uvr = st.number_input("Valor UVR", min_value=0.0, step=1.0)

        submitted = st.form_submit_button("Agregar servicio")

        if submitted:
            nuevo_registro = pd.DataFrame([{
                "Especialista": especialista,
                "Especialidad": especialidad,
                "Plan": plan,
                "Descripción": descripcion,
                "CÓDIGO SOAT": codigo_soat,
                "Vía Liquidación": via,
                "Valor Total": valor_total,
                "Valor UVR": valor_uvr
            }])

            if 'df' in st.session_state:
                st.session_state.df = pd.concat([st.session_state.df, nuevo_registro], ignore_index=True)
            else:
                st.session_state.df = nuevo_registro

            st.success("✔️ Servicio agregado correctamente.")
            st.dataframe(st.session_state.df)

if 'df' in st.session_state:
    df = st.session_state.df
    archivo = True

if archivo:
    pass
