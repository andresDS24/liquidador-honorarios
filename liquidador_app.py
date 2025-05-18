import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO
import re
from PyPDF2 import PdfReader

# CONFIGURACIÓN GENERAL
st.set_page_config(page_title="Liquidador de Honorarios", layout="wide")
VALOR_UVR = 1270
VALOR_UVR_ISS_ANESTESIA = 960

# FUNCIONES AUXILIARES
def buscar_uvr_en_texto(codigo, texto):
    codigo = codigo.strip()
    lineas = texto.splitlines()
    for i, linea in enumerate(lineas):
        if codigo in linea:
            match = re.search(r"(\d{2,4})", linea)
            if match:
                return int(match.group(1))
            elif i + 1 < len(lineas):
                siguiente = re.search(r"(\d{2,4})", lineas[i + 1])
                if siguiente:
                    return int(siguiente.group(1))
    return None

def cargar_uvr_desde_pdf(archivo_pdf):
    if archivo_pdf is not None:
        reader = PdfReader(archivo_pdf)
        return "\n".join(page.extract_text() for page in reader.pages)
    return ""

def cargar_base_uvr_excel(archivo_excel):
    try:
        df_tarifas = pd.read_excel(archivo_excel)
        df_tarifas = df_tarifas.dropna(subset=['Código ISS', 'UVR'])
        df_tarifas['Código ISS'] = df_tarifas['Código ISS'].astype(str).str.strip()
        return df_tarifas.set_index('Código ISS')['UVR'].to_dict()
    except Exception as e:
        st.error(f"Error cargando base ISS Excel: {e}")
        return {}

# 1. CARGA DE ARCHIVO
st.title("📊 Plataforma de Liquidación de Honorarios Médicos")
archivo = st.file_uploader("📥 Cargar archivo de servicios", type=["xlsx"])
archivo_excel_uvr = st.file_uploader("📁 Subir archivo de UVR desde Excel (tarifas_iss_completo.xlsx)", type=["xlsx"])
archivo_pdf_uvr = st.file_uploader("📄 Subir archivo PDF de UVR (tarifas-iss-2001.pdf)", type=["pdf"])

if archivo:
    df = pd.read_excel(archivo)
    st.session_state.df = df

if 'df' in st.session_state:
    df = st.session_state.df

    for col in ['CUPS', 'Valor UVR', 'Especialidad', 'Tipo Procedimiento', 'Plan Beneficios']:
        if col not in df.columns:
            df[col] = '' if col in ['CUPS', 'Especialidad', 'Tipo Procedimiento', 'Plan Beneficios'] else 0

    base_uvr_excel = cargar_base_uvr_excel(archivo_excel_uvr) if archivo_excel_uvr else {}
    texto_uvr_pdf = cargar_uvr_desde_pdf(archivo_pdf_uvr) if archivo_pdf_uvr else ""

    for i, row in df.iterrows():
        if row['Valor UVR'] == 0 and isinstance(row['CUPS'], str) and row['CUPS'].strip():
            cod = row['CUPS'].strip()
            uvr = base_uvr_excel.get(cod) or buscar_uvr_en_texto(cod, texto_uvr_pdf)
            if uvr:
                df.loc[df['CUPS'] == cod, 'Valor UVR'] = uvr

    st.subheader("✏️ Ingreso manual de UVR para códigos no encontrados")
    codigos_faltantes = df[df['Valor UVR'] == 0]['CUPS'].dropna().unique()
    for cod in codigos_faltantes:
        nueva_uvr = st.number_input(f"UVR para código {cod}", min_value=0, step=1, key=f"uvr_{cod}")
        if nueva_uvr > 0:
            df.loc[df['CUPS'] == cod, 'Valor UVR'] = nueva_uvr

    sin_uvr = df[df['Valor UVR'] == 0]
    if not sin_uvr.empty:
        st.warning("⚠️ Aún hay registros sin UVR. Puedes completar manualmente o continuar sin aplicar.")
        st.dataframe(sin_uvr)
        if not st.button("✅ Continuar sin completar todo"):
            st.stop()

    st.subheader("⚙️ Parámetros de liquidación por especialidad")
    profesional = st.selectbox("Selecciona el profesional a liquidar", df['Especialista'].dropna().unique())
    check_anestesia_diff = st.checkbox("Anestesiología diferencial (60%)")
    check_socio = st.checkbox("Es socio ortopedista")
    check_reconstruc = st.checkbox("Cirujano reconstructivo")
    check_pie = st.checkbox("Cirujano de pie y tobillo")

    def liquidar(row):
        esp = str(row.get("Especialidad", "")).upper()
        tipo = str(row.get("Tipo Procedimiento", "")).upper()
        plan = str(row.get("Plan Beneficios", "")).upper()
        via = str(row.get("Vía Liquidación", "")).lower()
        uvr = float(row.get("Valor UVR", 0))
        valor = float(row.get("Valor Total", 0))

        if "ANESTESIO" in esp:
            base = uvr * VALOR_UVR_ISS_ANESTESIA * 1.3
            factor = 0.6 if "misma" in via else 0.75
            if check_anestesia_diff:
                factor += 0.6
            return base * factor

        if "MAXILOFACIAL" in esp:
            if "INTERCONSULTA" in tipo: return 35000
            elif "CONSULTA" in tipo: return 29000
            return 0.7 * valor

        if "FISIATRIA" in esp:
            if "PRIMERA" in tipo: return 59000
            elif "CONTROL" in tipo: return 51000
            elif "ARL" in tipo and "JUNTA" in tipo: return 73000
            elif "JUNTA" in tipo: return 70000
            elif "TOXINA" in tipo: return 155000
            elif "INFILTRACION" in tipo: return 76000
            elif "NO QUIR" in tipo: return 0.7 * valor

        if "DOLOR" in esp:
            if "INTERCONSULTA" in tipo: return 58400
            elif "MIOFASCIAL" in tipo: return 64500
            elif "PAQUETE" in tipo: return 350000
            return 0.7 * valor

        if "LABORAL" in esp:
            if "JUNTA" in tipo: return 0.8 * valor
            return 0.85 * valor

        if "NEUROCIRU" in esp:
            return 0.7 * valor if "SOAT" in plan else 0.8 * valor

        if "PEDIATRICA" in esp:
            if "EPS" in plan: return 70000
            elif "SOAT" in plan or "POLIZA" in plan: return 0.7 * valor
            elif "YESO" in tipo: return 260000
            elif "MALFORMACION" in tipo: return 980000

        if check_reconstruc:
            if "RECONSTRUCTIVA" in tipo: return 2700000 if "EPS" in plan else 3000000
            return uvr * VALOR_UVR * 1.2

        if check_pie:
            if "CONSULTA" in tipo: return 30000
            elif "JUNTA" in tipo or "ESPECIAL" in tipo: return 0.7 * valor
            elif "QUIR" in tipo: return uvr * VALOR_UVR * 1.3

        if "MANO" in esp:
            if "CONSULTA" in tipo: return 30000
            elif "JUNTA" in tipo or "ESPECIAL" in tipo: return 0.7 * valor
            elif "QUIR" in tipo: return uvr * VALOR_UVR * 1.3

        if "ORTOPEDIA" in esp:
            if check_socio: return 0.85 * valor if "SOAT" not in plan else 0.7 * valor
            elif "CONSULTA" in tipo: return 27000
            elif "QUIR" in tipo: return uvr * VALOR_UVR * 1.2
            elif "NO QUIR" in tipo: return 0.7 * valor

        return uvr * VALOR_UVR

    df['Valor Total'] = pd.to_numeric(df.get('Valor Total', 0), errors='coerce')
    df['Valor Liquidado'] = df.apply(liquidar, axis=1)

    df_final = df[df['Especialista'] == profesional]

    st.subheader("📌 Vista previa de liquidación")
    st.dataframe(df_final[['CUPS', 'Valor UVR', 'Valor Liquidado']])

    st.metric("Total liquidado", f"${df_final['Valor Liquidado'].sum():,.0f}")
    st.metric("% Liquidado", f"{(df_final['Valor Liquidado'].sum() / df_final['Valor Total'].sum()) * 100:.2f}%")

    if st.download_button("📥 Descargar resultados Excel", df_final.to_csv(index=False).encode('utf-8'), file_name="liquidacion_profesional.csv"):
        st.success("Archivo descargado correctamente")

    st.subheader("📈 Informe resumen por Especialista")
    resumen = df.groupby("Especialista")["Valor Liquidado"].sum().reset_index().sort_values(by="Valor Liquidado", ascending=False)
    st.dataframe(resumen)

    if st.download_button("📥 Descargar informe resumen", resumen.to_csv(index=False).encode('utf-8'), file_name="resumen_liquidacion.csv"):
        st.success("Informe generado exitosamente")
