
import pandas as pd
import streamlit as st
from io import BytesIO
from fpdf import FPDF
import smtplib
from email.message import EmailMessage

# --- CONFIGURACIONES INICIALES ---
VALOR_UVR = 107
VALOR_UVR_ISS_ANESTESIA = 960
VALORES_FIJOS = {
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

    if st.checkbox("Eliminar filas duplicadas", value=True):
        df = df.drop_duplicates()

    st.subheader("Agregar nuevo especialista")
    nuevo_nombre = st.text_input("Nombre del nuevo especialista")
    copiar_de = st.selectbox("Copiar configuración de:", sorted(df['Especialista'].dropna().unique()))

    if st.button("Agregar especialista"):
        if nuevo_nombre and copiar_de:
            filas_referencia = df[df['Especialista'] == copiar_de].copy()
            filas_referencia['Especialista'] = nuevo_nombre
            df = pd.concat([df, filas_referencia], ignore_index=True)
            st.success(f"Se agregó {nuevo_nombre} copiando la configuración de {copiar_de}.")

    profesional = st.selectbox("Selecciona el profesional a liquidar", sorted(df['Especialista'].dropna().unique()))
    df_prof = df[df['Especialista'] == profesional].copy()

    modo_conversion = st.radio("Modo de conversión de tarifas:", ["Sin conversión", "SOAT → ISS", "ISS → SOAT"])

    def calcular_liquidacion(row):
        esp = str(row['Especialidad']).strip().upper()
        total = row['Valor Total']
        uvrs = row.get('Valor UVR', 0)

        if esp == "ANESTESIOLOGIA" and uvrs > 0:
            base = uvrs * VALOR_UVR_ISS_ANESTESIA
            return base * (1 + PORCENTAJES_POR_ESPECIALIDAD.get("ANESTESIOLOGIA", 0) / 100), "ISS + 60%"
        elif esp in VALORES_FIJOS:
            return VALORES_FIJOS[esp], "Valor fijo"
        elif esp in PORCENTAJES_POR_ESPECIALIDAD:
            return total * PORCENTAJES_POR_ESPECIALIDAD[esp] / 100, "Porcentaje sobre facturado"
        elif uvrs > 0:
            base = uvrs * VALOR_UVR
            return base, "UVR sin porcentaje"
        else:
            return 0, "Sin regla"

    df_prof['Valor Liquidado'], df_prof['Método de Cálculo'] = zip(*df_prof.apply(calcular_liquidacion, axis=1))

    st.subheader("Resumen del Profesional")
    total_facturado = df_prof['Valor Total'].sum()
    total_liquidado = df_prof['Valor Liquidado'].sum()
    porcentaje = (total_liquidado / total_facturado) * 100 if total_facturado else 0

    st.metric("Total Servicios Facturados", f"${total_facturado:,.0f}")
    st.metric("Total Liquidado al Profesional", f"${total_liquidado:,.0f}")
    st.metric("% Participación", f"{porcentaje:.2f}%")

    st.subheader("Mostrar / Ocultar Columnas")
    all_columns = list(df_prof.columns)
    selected_cols = st.multiselect("Selecciona las columnas a mostrar", all_columns, default=all_columns)
    st.dataframe(df_prof[selected_cols])

    st.subheader("Modificar valores manualmente")
    edited_df = st.data_editor(df_prof[selected_cols], num_rows="dynamic")

    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='LIQUIDACION')
        output.seek(0)
        return output

    def to_pdf(df):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=10)
        pdf.cell(200, 10, txt=f"Liquidación de Honorarios - {profesional}", ln=True, align='C')
        pdf.ln(10)
        for col in df.columns:
            pdf.cell(45, 10, col, border=1)
        pdf.ln()
        for index, row in df.iterrows():
            for item in row:
                pdf.cell(45, 10, str(item)[:15], border=1)
            pdf.ln()
        pdf_data = pdf.output(dest='S').encode('latin1')
        return BytesIO(pdf_data)

    st.download_button(
        label="📄 Descargar en Excel",
        data=to_excel(edited_df),
        file_name=f"Liquidacion_{profesional}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.download_button(
        label="📝 Descargar en PDF",
        data=to_pdf(edited_df),
        file_name=f"Liquidacion_{profesional}.pdf",
        mime="application/pdf"
    )

    st.subheader("📧 Enviar por correo electrónico")
    destinatario = st.text_input("Correo del destinatario")
    if st.button("Enviar por correo") and destinatario:
        try:
            msg = EmailMessage()
            msg['Subject'] = f"Liquidación de Honorarios - {profesional}"
            msg['From'] = "remitente@ejemplo.com"
            msg['To'] = destinatario
            msg.set_content("Adjunto encontrará el archivo de liquidación en PDF.")

            pdf_data = to_pdf(edited_df).read()
            msg.add_attachment(pdf_data, maintype='application', subtype='pdf', filename=f"Liquidacion_{profesional}.pdf")

            with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
                smtp.starttls()
                smtp.login("tu_correo@gmail.com", "tu_contraseña")
                smtp.send_message(msg)
            st.success("Correo enviado exitosamente.")
        except Exception as e:
            st.error(f"Error al enviar el correo: {e}")
