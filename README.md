# Liquidador de Honorarios Médicos - WebApp

Plataforma para liquidación profesional de servicios médicos:

## Funcionalidades
- Carga desde Excel o edición directa en la web.
- Homologación SOAT ↔ CUPS.
- Cálculo de UVR automático o manual.
- Liquidación automatizada según especialidad.
- Validaciones visuales para datos faltantes.
- Reportes en tiempo real:
  - Totales por profesional
  - Porcentaje liquidado vs facturado
  - Gráfico comparativo
- Exportación por profesional en PDF y Excel.
- Descarga consolidada en ZIP.

## Uso
1. Sube los archivos a Streamlit Cloud o ejecuta localmente con:
```bash
streamlit run liquidador_app.py
```

2. Carga un archivo Excel o edita los datos manualmente.
3. Aplica reglas y valida la información.
4. Exporta resultados por profesional.
