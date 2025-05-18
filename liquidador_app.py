import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO
import re

# --- CONFIGURACIÓN GENERAL ---
st.set_page_config(page_title="Liquidador de Honorarios", layout="wide")
VALOR_UVR = 1270
VALOR_UVR_ISS_ANESTESIA = 960

st.title("📊 Plataforma de Liquidación de Honorarios Médicos")
st.markdown("Carga el archivo de servicios y obtén la liquidación por profesional según especialidad.")

# --- FUNCIONES AUXILIARES ---
def buscar_uvr_en_texto(codigo, texto):
    patron = re.compile(rf"\b{codigo}\b.*?UVR\s*(\d+)", re.IGNORECASE)
    coincidencias = patron.findall(texto)
    if coincidencias:
        return int(coincidencias[0])
    return None

def cargar_uvr_desde_pdf(ruta_pdf):
    from PyPDF2 import PdfReader
    reader = PdfReader(ruta_pdf)
    texto_completo = ""
    for page in reader.pages:
        texto_completo += page.extract_text() + "\n"
    return texto_completo

ruta_pdf = "/mnt/data/tarifas-iss-2001.pdf"
texto_uvr = cargar_uvr_desde_pdf(ruta_pdf) if ruta_pdf else ""

# --- SUBIR ARCHIVO ---
archivo = st.file_uploader("📌 Carga archivo Excel", type=["xlsx"])
if archivo:
    df = pd.read_excel(archivo)
    st.session_state.df = df

if 'df' in st.session_state:
    df = st.session_state.df

    for col in ['CUPS', 'Valor UVR']:
        if col not in df.columns:
            df[col] = '' if col == 'CUPS' else 0

    # Asignar UVR automáticamente si se tiene CUPS y valor UVR = 0
    for i, row in df.iterrows():
        if row['Valor UVR'] == 0 and isinstance(row['CUPS'], str) and row['CUPS']:
            uvr_pdf = buscar_uvr_en_texto(row['CUPS'], texto_uvr)
            if uvr_pdf:
                df.at[i, 'Valor UVR'] = uvr_pdf

    sin_uvr = df[df['Valor UVR'] == 0]
    sin_cups = df[df['CUPS'].isna() | (df['CUPS'] == '')]

    if not sin_uvr.empty or not sin_cups.empty:
        st.warning("⚠️ Existen registros con UVR o CUPS faltantes.")
        st.dataframe(pd.concat([sin_uvr, sin_cups]).drop_duplicates())
        if not st.button("✅ No aplica, continuar"):
            st.stop()

    st.data_editor(df, use_container_width=True, num_rows="dynamic")

    # --- PROFESIONALES ---
    st.subheader("👨‍⚕️ Gestión de profesionales")
    if 'profesionales' not in st.session_state:
        st.session_state.profesionales = list(df['Especialista'].dropna().unique())

    nuevo_prof = st.text_input("➕ Agregar nuevo profesional")
    copiar_de = st.selectbox("Copiar configuración de:", ["(Ninguno)"] + st.session_state.profesionales)
    if st.button("Agregar profesional") and nuevo_prof:
        st.session_state.profesionales.append(nuevo_prof)
        st.success(f"Agregado: {nuevo_prof}")

    profesional = st.selectbox("Seleccionar profesional", st.session_state.profesionales)
    conversion = st.selectbox("Conversión tarifaria", ["Ninguna", "SOAT a ISS", "ISS a SOAT"])
    check_anestesia_diff = st.checkbox("☑️ Anestesiología diferencial (60%)")
    check_socio = st.checkbox("🧾 Es socio ortopedista")
    check_reconstruc = st.checkbox("🔧 Cirujano reconstructivo")
    check_pie = st.checkbox("🦶 Cirujano de pie y tobillo")

    df_prof = df[df['Especialista'] == profesional].copy()

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

        if conversion == "SOAT a ISS": return uvr * VALOR_UVR
        if conversion == "ISS a SOAT": return uvr * 950
        return uvr * VALOR_UVR

    df_prof['Valor Liquidado'] = df_prof.apply(liquidar, axis=1)
    df_prof['Valor Total'] = pd.to_numeric(df_prof.get('Valor Total', 0), errors='coerce')

    st.data_editor(df_prof, use_container_width=True, num_rows="dynamic")
    st.metric("Total facturado", f"${df_prof['Valor Total'].sum():,.0f}")
    st.metric("Total liquidado", f"${df_prof['Valor Liquidado'].sum():,.0f}")
    st.metric("% Liquidado", f"{(df_prof['Valor Liquidado'].sum() / df_prof['Valor Total'].sum()) * 100:.2f}%")

    if st.button("📥 Exportar ZIP"):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            excel_io = BytesIO()
            with pd.ExcelWriter(excel_io, engine='xlsxwriter') as writer:
                df_prof.to_excel(writer, index=False)
            excel_io.seek(0)
            z.writestr(f"{profesional}_liquidacion.xlsx", excel_io.read())
        buffer.seek(0)
        st.download_button("Descargar ZIP", buffer, f"Liquidacion_{profesional}.zip")
        
