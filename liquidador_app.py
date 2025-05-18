import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO

# --- CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="Liquidador de Honorarios", layout="wide")
VALOR_UVR = 1270
VALOR_UVR_ISS_ANESTESIA = 960

st.title("🩺 Plataforma de Liquidación de Honorarios Médicos")
st.markdown("Carga el archivo de servicios y obtén la liquidación por profesional según especialidad.")

# --- SUBIR ARCHIVO ---
archivo = st.file_uploader("📎 Carga archivo Excel", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    df['Valor Total'] = pd.to_numeric(df['Valor Total'], errors='coerce').fillna(0)
    df['Valor UVR'] = pd.to_numeric(df.get('Valor UVR', 0), errors='coerce').fillna(0)

    if 'CUPS' in df.columns:
        st.subheader("🔍 Revisión de homologación")
        if st.checkbox("🧹 Eliminar duplicados", value=True):
            df = df.drop_duplicates()

        homologados = df[df['Valor UVR'] > 0][['CUPS', 'Valor UVR']].drop_duplicates()
        sin_uvr = df[df['Valor UVR'] == 0][['CUPS']].drop_duplicates()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### ✅ CUPS homologados")
            st.dataframe(homologados)
        with col2:
            st.markdown("### ⚠️ Códigos sin UVR")
            st.dataframe(sin_uvr)
    else:
        st.warning("⚠️ El archivo no contiene la columna 'CUPS'. Verifica el formato del archivo.")

    # --- CONTROLES ESPECIALES ---
    st.subheader("⚙️ Configuración adicional")
    es_socio = st.checkbox("¿El profesional es ortopedista socio?")
    es_pie_tobillo = st.checkbox("¿El profesional es cirujano de pie y tobillo?")
    es_reconstructivo = st.checkbox("¿El profesional es cirujano reconstructivo?")
    anestesiologia_diferencial = st.checkbox("¿Aplicar incremento diferencial del 60% en Anestesiología?")

    # --- FUNCIÓN DE LIQUIDACIÓN ---
    def calcular_liquidacion(row):
        esp = str(row.get('Especialidad', '')).upper()
        total = row.get('Valor Total', 0)
        uvr = row.get('Valor UVR', 0)
        via = str(row.get('Vía Liquidación', '')).lower()
        plan = str(row.get('Plan', '')).upper()
        desc = str(row.get('Descripción', '')).lower()

        if "ANESTESIO" in esp:
            base = uvr * VALOR_UVR_ISS_ANESTESIA * 1.3
            if "misma" in via:
                factor = 0.6 + (0.6 if anestesiologia_diferencial else 0)
            elif "diferente" in via:
                factor = 0.75 + (0.6 if anestesiologia_diferencial else 0)
            else:
                factor = 1
            return base * factor

        if es_reconstructivo:
            if "consulta" in desc:
                return 28000
            elif "reconstructiva" in desc:
                return 2700000 if "EPS" in plan else 3000000
            elif uvr > 0:
                return uvr * VALOR_UVR * 1.2

        if es_pie_tobillo:
            if "consulta" in desc:
                return 30000
            elif "junta" in desc or "especial" in desc:
                return total * 0.7
            elif uvr >= 600 or "grupo especial" in desc:
                return 600 * VALOR_UVR * 1.3
            elif uvr > 0:
                return uvr * VALOR_UVR * 1.3

        if es_socio and "ORTOPEDIA" in esp:
            return total * (0.7 if "SOAT" in plan else 0.85)

        if "ORTOPEDIA Y TRAUMATOLOGIA" in esp and "consulta" in desc:
            return 27000

        if "ORTOPEDIA Y TRAUMATOLOGIA" in esp and "quirurgico" in desc:
            return uvr * VALOR_UVR * 1.2

        if "ORTOPEDIA Y TRAUMATOLOGIA" in esp and "no quirurgico" in desc:
            return total * 0.7

        return total * 0.7 if uvr == 0 else uvr * VALOR_UVR

    df['Valor Liquidado'] = df.apply(calcular_liquidacion, axis=1)

    # --- EXPORTAR ZIP ---
    st.subheader("📦 Exportación individual por profesional")
    if st.button("⬇️ Descargar archivo consolidado"):
        output = BytesIO()
        with zipfile.ZipFile(output, "w") as zipf:
            for prof in df['Especialista'].dropna().unique():
                df_prof = df[df['Especialista'] == prof]
                bio = BytesIO()
                with pd.ExcelWriter(bio, engine='xlsxwriter') as writer:
                    df_prof.to_excel(writer, index=False, sheet_name='Liquidacion')
                bio.seek(0)
                zipf.writestr(f"{prof}.xlsx", bio.read())
        output.seek(0)
        st.download_button("📁 Descargar ZIP", data=output, file_name="Liquidacion_profesionales.zip", mime="application/zip")
