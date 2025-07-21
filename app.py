import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Liquidador Honorarios", layout="wide")

st.title("💼 Liquidador de Honorarios Médicos")

# Cargar archivo
uploaded_file = st.file_uploader("Cargar archivo de servicios (.xlsx)", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("Archivo cargado correctamente.")

    # Mostrar contenido
    st.dataframe(df)

    # Homologar códigos SOAT a CUPS
    if "Codigo Homologo" not in df.columns:
        df["Codigo Homologo"] = df["CUPS"]  # Simplificado

    # Buscar UVR (cargar automáticamente si existe)
    if "Valor UVR" not in df.columns:
        df["Valor UVR"] = 0

    # Identificar códigos sin UVR
    codigos_sin_uvr = df[df["Valor UVR"] == 0]["Codigo Homologo"].unique()
    if len(codigos_sin_uvr) > 0:
        st.warning("Algunos códigos no tienen UVR asignado. Por favor ingréselos manualmente.")

        codigo_seleccionado = st.selectbox("Selecciona un código sin UVR", codigos_sin_uvr)
        nueva_uvr = st.number_input("Ingresa el valor UVR para el código seleccionado", min_value=0.0, step=0.1)
        if st.button("Aplicar UVR"):
            df.loc[df["Codigo Homologo"] == codigo_seleccionado, "Valor UVR"] = nueva_uvr
            st.success("UVR asignado correctamente.")
            codigos_sin_uvr = df[df["Valor UVR"] == 0]["Codigo Homologo"].unique()

    # Seleccionar especialista
    especialistas = df["Especialista"].unique()
    seleccionado = st.selectbox("Seleccionar especialista a liquidar", especialistas)
    df_esp = df[df["Especialista"] == seleccionado]

    # Lógica de liquidación base (demo)
    df_esp["Valor Liquidado"] = df_esp["Valor UVR"] * 1270
    if "Tipo Procedimiento" in df_esp.columns:
        df_esp.loc[df_esp["Tipo Procedimiento"] == "Proced Qx", "Valor Liquidado"] *= 1.30

    st.subheader("Resumen de liquidación")
    st.dataframe(df_esp)

    # Exportar
    st.download_button("📥 Descargar Excel", df_esp.to_excel(index=False), file_name="liquidacion.xlsx")

