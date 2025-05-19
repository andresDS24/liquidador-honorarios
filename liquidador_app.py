import streamlit as st
import pandas as pd
import zipfile
from io import BytesIO
import re

# CONFIGURACIÓN GENERAL
st.set_page_config(page_title="Liquidador de Honorarios", layout="wide")
VALOR_UVR = 1270
VALOR_UVR_ISS_ANESTESIA = 960

# 1. CARGA DE ARCHIVO
st.title("📊 Plataforma de Liquidación de Honorarios Médicos")
archivo = st.file_uploader("📅 Cargar archivo de servicios", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    st.session_state.df = df

if 'df' in st.session_state:
    df = st.session_state.df

    for col in ['CUPS', 'Valor UVR', 'Especialidad', 'Tipo Procedimiento', 'Plan Beneficios']:
        if col not in df.columns:
            df[col] = '' if col in ['CUPS', 'Especialidad', 'Tipo Procedimiento', 'Plan Beneficios'] else 0

    eliminar_duplicados = st.checkbox("🧹 Eliminar filas duplicadas", value=False)
    if eliminar_duplicados:
        df = df.drop_duplicates()
        st.session_state.df = df
        st.success("Filas duplicadas eliminadas")

    st.subheader("✏️ Ingreso manual de UVR para códigos no encontrados")
    codigos_faltantes = sorted(df.loc[(df['Valor UVR'].isna()) | (df['Valor UVR'] == 0), 'CUPS'].dropna().astype(str).unique().tolist())

    if not codigos_faltantes:
        st.warning("✅ Todos los códigos ya tienen UVR asignada. No hay códigos pendientes.")
    else:
        with st.form("form_uvr"):
            st.write("Selecciona uno o varios códigos para asignar UVR manualmente:")
            seleccionados = st.multiselect("Códigos sin UVR", options=codigos_faltantes)
            uvr_manual = st.number_input("Ingrese el valor UVR a asignar", min_value=0, step=1, key="uvr_manual_multiple")
            submitted = st.form_submit_button("Asignar UVR")
            if submitted and seleccionados:
                df.loc[df['CUPS'].astype(str).isin(seleccionados), 'Valor UVR'] = uvr_manual
                st.success(f"UVR {uvr_manual} asignada a los códigos seleccionados")

    sin_uvr = df[(df['Valor UVR'] == 0) | (df['Valor UVR'].isna())]
    if not sin_uvr.empty:
        st.warning("⚠️ Aún hay registros sin UVR. Puedes completar manualmente o continuar sin aplicar.")
        st.dataframe(sin_uvr)
        if not st.button("✅ Continuar sin completar todo"):
            st.stop()

    # Unificación de especialidades
    st.subheader("🔀 Unificación de Especialidades por Profesional")
    profesionales = df['Especialista'].dropna().unique()
    for prof in profesionales:
        especialidades = df[df['Especialista'] == prof]['Especialidad'].dropna().unique()
        if len(especialidades) > 1:
            st.markdown(f"**{prof}** tiene múltiples especialidades: {', '.join(especialidades)}")
            seleccion = st.selectbox(f"Selecciona especialidad a conservar para {prof}", options=especialidades, key=f"esp_{prof}")
            df.loc[df['Especialista'] == prof, 'Especialidad'] = seleccion

    st.subheader("⚙️ Parámetros de liquidación por especialidad")
    if 'profesional' not in st.session_state:
        st.session_state.profesional = df['Especialista'].dropna().unique()[0]

    profesional = st.selectbox(
        "Selecciona el profesional a liquidar",
        df['Especialista'].dropna().unique(),
        index=list(df['Especialista'].dropna().unique()).index(st.session_state.profesional)
    )

    st.session_state.profesional = profesional
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
            base = uvr * VALOR_UVR_ISS_ANESTESIA
            incremento = base * 0.3
            total = base + incremento
            factor = 0.6 if "misma" in via else 0.75
            if check_anestesia_diff:
                factor += 0.6
            return total * factor

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
            base = uvr * VALOR_UVR
            incremento = base * 0.2
            return base + incremento

        if check_pie:
            if "CONSULTA" in tipo: return 30000
            elif "JUNTA" in tipo or "ESPECIAL" in tipo: return 0.7 * valor
            elif "QUIR" in tipo:
                base = uvr * VALOR_UVR
                incremento = base * 0.3
                return base + incremento

        if "MANO" in esp:
            if "CONSULTA" in tipo: return 30000
            elif "JUNTA" in tipo or "ESPECIAL" in tipo: return 0.7 * valor
            elif "QUIR" in tipo:
                base = uvr * VALOR_UVR
                incremento = base * 0.3
                return base + incremento

        if "ORTOPEDIA" in esp:
            if check_socio: return 0.85 * valor if "SOAT" not in plan else 0.7 * valor
            elif "CONSULTA" in tipo: return 27000
            elif "QUIR" in tipo:
                base = uvr * VALOR_UVR
                incremento = base * 0.2
                return base + incremento
            elif "NO QUIR" in tipo: return 0.7 * valor

        return uvr * VALOR_UVR

    df['Valor Total'] = pd.to_numeric(df.get('Valor Total', 0), errors='coerce')
    df['Valor Liquidado'] = df.apply(liquidar, axis=1)

    df_final = df[df['Especialista'] == profesional]

    st.subheader("📌 Vista previa de liquidación")
    st.dataframe(df_final[['CUPS', 'Valor UVR', 'Valor Liquidado']])

    st.metric("Total liquidado", f"${df_final['Valor Liquidado'].sum():,.0f}")
    st.metric("% Liquidado", f"{(df_final['Valor Liquidado'].sum() / df_final['Valor Total'].sum()) * 100:.2f}%")

    import io
    from openpyxl import Workbook

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_final.to_excel(writer, index=False, sheet_name="Liquidación")
    output.seek(0)
    st.download_button("📅 Descargar resultados Excel", data=output.read(), file_name="liquidacion_profesional.xlsx")

    st.subheader("📈 Informe resumen por Especialista")
    resumen = df.groupby("Especialista")["Valor Liquidado"].sum().reset_index().sort_values(by="Valor Liquidado", ascending=False)
    st.dataframe(resumen)

    output2 = BytesIO()
    with pd.ExcelWriter(output2, engine='openpyxl') as writer:
        resumen.to_excel(writer, index=False, sheet_name="Resumen")
    output2.seek(0)
    st.download_button("📅 Descargar informe resumen", data=output2.read(), file_name="resumen_liquidacion.xlsx")
