# Liquidador de Honorarios Médicos

Aplicación web para calcular y exportar la liquidación de honorarios médicos basada en archivos Excel de producción médica.

## Funcionalidades

- Carga de archivo Excel (.xlsx)
- Eliminación de filas duplicadas
- Agregado de nuevos especialistas copiando configuraciones existentes
- Selección de profesional a liquidar
- Aplicación de reglas por especialidad (valor fijo, porcentaje, UVR)
- Conversión SOAT ↔ ISS
- Vista editable de datos
- Exportación en Excel
- Visualización de métricas de resumen (% participación, totales)

## Cómo usar localmente

1. Clona este repositorio o descarga los archivos.
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Ejecuta la app:
   ```bash
   streamlit run liquidador_app.py
   ```

4. Accede a `http://localhost:8501` desde tu navegador.

## Publicación en Streamlit Cloud

1. Sube este repositorio a GitHub.
2. Ve a [streamlit.io/cloud](https://streamlit.io/cloud)
3. Crea una nueva app seleccionando tu repo.
4. Elige `liquidador_app.py` como archivo principal.
