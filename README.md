# 💼 Liquidador de Honorarios Médicos

Aplicación interactiva desarrollada en Streamlit para cargar servicios médicos, homologar códigos, calcular liquidaciones por especialista, generar informes automáticos y exportar resultados.

## 🚀 Funcionalidades principales

- Carga de archivo Excel de servicios.
- Homologación automática de códigos SOAT a CUPS.
- Asignación automática de UVR desde:
  - Excel (`tarifas_iss_completo.xlsx`)
  - PDF (`tarifas-iss-2001.pdf`)
- Ingreso manual de UVR cuando no se encuentra automáticamente (replicado en todos los códigos repetidos).
- Liquidación automática por especialista con reglas específicas para:
  - Anestesiología (con modo diferencial)
  - Ortopedia (general, pediátrica, reconstructiva, mano, pie y socio)
  - Neurocirugía
  - Medicina del dolor
  - Medicina física y rehabilitación
  - Medicina laboral
  - Cirugía maxilofacial
- Selección del profesional a liquidar con métricas por valor total y porcentaje.
- Exportación individual a CSV.
- Informe general por especialista descargable en resumen.

## 📝 Requisitos

El archivo `requirements.txt` incluye:

```
streamlit
pandas
openpyxl
PyPDF2
xlsxwriter
```

## 📦 Archivos esperados

- `servicios.xlsx`: base con columnas como `Especialista`, `CUPS`, `Valor Total`, `Tipo Procedimiento`, `Plan Beneficios`, etc.
- `tarifas_iss_completo.xlsx`: base con columnas `Código ISS` y `UVR`.
- `tarifas-iss-2001.pdf`: documento que contiene códigos y UVR como respaldo adicional.

## ▶️ Ejecución local

1. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Ejecuta la app:
   ```bash
   streamlit run liquidador_app.py
   ```

## 📊 Salidas del sistema

- `liquidacion_profesional.csv`: Liquidación filtrada por especialista.
- `resumen_liquidacion.csv`: Consolidado por especialista (total liquidado).
