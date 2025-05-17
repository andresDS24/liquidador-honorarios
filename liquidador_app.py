
import pandas as pd
import streamlit as st
from io import BytesIO

# --- CONFIGURACIONES INICIALES ---
VALOR_UVR = 107
VALORES_FIJOS = {
    "ANESTESIOLOGIA": 28000,
    "MEDICINA GENERAL": 27000,
    "MEDICINA FISICA Y REHABILITACION": 59000
}
PORCENTAJES_POR_ESPECIALIDAD = {
    "ANESTESIOLOGIA": 60,
    "MEDICINA GENERAL": 60,
    "MEDICINA FISICA Y REHABILITACION": 70,
    "ORTOPEDIA Y TRAUMATOLOGIA": 70
}

# --- INTERFAZ STREAMLIT ---
st.title("Liquidador de Honorarios Médicos")

archivo = st.file_uploader("Carga el archivo de servicios a liquidar (.xlsx)", type=["xlsx"])

if archivo:
    df = pd.read_excel(archivo)
    df['Valor Total'] = pd.to_numeric(df['Valor Total'], errors='coerce').fillna(0)

    # Opción para eliminar filas duplicadas
    if st.checkbox("Eliminar filas duplicadas", value=True):
        df = df.drop_duplicates()

    # Agregar nuevo especialista copiando reglas de otro
    st.subheader("Agregar nuevo especialista")
    nuevo_nombre = st.text_input("Nombre del nuevo especialista")
    copiar_de = st.selectbox("Copiar configuración de:", sorted(df['Especialista'].dropna().unique()))

    if st.button("Agregar especialista"):
        if nuevo_nombre and copiar_de:
            filas_referencia = df[df['Especialista'] == copiar_de].copy()
            filas_referencia['Especialista'] = nuevo_nombre
            df = pd.concat([df, filas_referencia], ignore_index=True)
            st.success(f"Se agregó {nuevo_nombre} copiando la configuración de {copiar_de}.")

    # Seleccionar profesional
    profesional = st.selectbox("Selecciona el profesional a liquidar", sorted(df['Especialista'].dropna().unique()))
    df_prof = df[df['Especialista'] == profesional].copy()

    # Campo para conversión
    modo_conversion = st.radio("Modo de conversión de tarifas:", ["Sin conversión", "SOAT → ISS", "ISS → SOAT"])

    # Funciones de cálculo
    def calcular_liquidacion(row):
        esp = str(row['Especialidad']).strip().upper()
        total = row['Valor Total']
        uvrs = row.get('Valor UVR', 0)

        if esp in VALORES_FIJOS:
            return VALORES_FIJOS[esp], "Valor fijo"
        elif esp in PORCENTAJES_POR_ESPECIALIDAD:
            return total * PORCENTAJES_POR_ESPECIALIDAD[esp] / 100, "Porcentaje sobre facturado"
        elif uvrs > 0:
            base = uvrs * VALOR_UVR
            return base, "UVR sin porcentaje"
        else:
            return 0, "Sin regla"

    df_prof['Valor Liquidado'], df_prof['Método de Cálculo'] = zip(*df_prof.apply(calcular_liquidacion, axis=1))

    # Mostrar resumen
    st.subheader("Resumen del Profesional")
    total_facturado = df_prof['Valor Total'].sum()
    total_liquidado = df_prof['Valor Liquidado'].sum()
    porcentaje = (total_liquidado / total_facturado) * 100 if total_facturado else 0

    st.metric("Total Servicios Facturados", f"${total_facturado:,.0f}")
    st.metric("Total Liquidado al Profesional", f"${total_liquidado:,.0f}")
    st.metric("% Participación", f"{porcentaje:.2f}%")

    # Opciones de columnas visibles
    st.subheader("Mostrar / Ocultar Columnas")
    all_columns = list(df_prof.columns)
    selected_cols = st.multiselect("Selecciona las columnas a mostrar", all_columns, default=all_columns)
    st.dataframe(df_prof[selected_cols])

    # Edición manual opcional
    st.subheader("Modificar valores manualmente")
    edited_df = st.data_editor(df_prof[selected_cols], num_rows="dynamic")

    # Botones de exportación
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='LIQUIDACION')
        output.seek(0)
        return output

    st.download_button(
        label="📄 Descargar en Excel",
        data=to_excel(edited_df),
        file_name=f"Liquidacion_{profesional}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
