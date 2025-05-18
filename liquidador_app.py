import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO

st.set_page_config(page_title="Liquidador de Honorarios", layout="wide")
VALOR_UVR = 1270
VALOR_UVR_ISS_ANESTESIA = 960

st.title("🩺 Plataforma de Liquidación de Honorarios Médicos")

archivo = st.file_uploader("📎 Carga archivo Excel", type=["xlsx"])
if archivo:
    df = pd.read_excel(archivo)
    st.session_state.df = df

if 'df' in st.session_state:
    df = st.session_state.df
    for col in ['CUPS', 'Valor UVR']:
        if col not in df.columns:
            df[col] = '' if col == 'CUPS' else 0

    st.subheader("🔍 Revisión de homologación")
    sin_uvr = df[df['Valor UVR'] == 0]
    sin_cups = df[df['CUPS'].isna() | (df['CUPS'] == '')]

    if not sin_uvr.empty or not sin_cups.empty:
        st.warning("⚠️ Existen registros con UVR o CUPS faltantes. Corrígelos o presiona 'No aplica'")
        if not sin_uvr.empty:
            st.markdown("**Registros sin UVR:**")
            st.dataframe(sin_uvr)
        if not sin_cups.empty:
            st.markdown("**Registros sin CUPS:**")
            st.dataframe(sin_cups)
        if st.button("✅ No aplica, continuar sin corregir"):
            st.session_state.continuar = True
            st.rerun()
        st.stop()

    profesional = st.selectbox("Selecciona el profesional", options=df['Especialista'].unique())
    conversion = st.selectbox("Conversión tarifaria", ["Ninguna", "SOAT a ISS", "ISS a SOAT"])
    check_anestesia_diff = st.checkbox("Anestesiología diferencial (60%)")

    df_prof = df[df['Especialista'] == profesional].copy()

    def liquidar_fila(row):
        especialidad = str(row.get("Especialidad", "")).upper()
        uvr = float(row.get("Valor UVR", 0))
        if "ANESTESIO" in especialidad:
            base = uvr * VALOR_UVR_ISS_ANESTESIA * 1.3
            via = row.get("Vía Liquidación", "").lower()
            factor = 0.6 if "misma" in via else 0.75
            if check_anestesia_diff:
                factor += 0.6
            return base * factor
        if conversion == "SOAT a ISS":
            return uvr * VALOR_UVR
        elif conversion == "ISS a SOAT":
            return uvr * 950
        return uvr * VALOR_UVR

    df_prof["Valor Liquidado"] = df_prof.apply(liquidar_fila, axis=1)
    df_prof["Valor Total"] = pd.to_numeric(df_prof.get("Valor Total", 0), errors="coerce")
    st.dataframe(df_prof)

    st.metric("Total facturado", f"${df_prof['Valor Total'].sum():,.0f}")
    st.metric("Total liquidado", f"${df_prof['Valor Liquidado'].sum():,.0f}")
    st.metric("% Liquidado", f"{(df_prof['Valor Liquidado'].sum() / df_prof['Valor Total'].sum()) * 100:.2f}%")

    if st.button("📦 Descargar archivo ZIP"):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            excel_bytes = BytesIO()
            with pd.ExcelWriter(excel_bytes, engine="xlsxwriter") as writer:
                df_prof.to_excel(writer, index=False)
            excel_bytes.seek(0)
            z.writestr(f"{profesional}_liquidacion.xlsx", excel_bytes.read())
        buffer.seek(0)
        st.download_button("Descargar ZIP", data=buffer, file_name=f"Liquidacion_{profesional}.zip")
