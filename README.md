# 💼 Plataforma de Liquidación de Honorarios Médicos

Sistema profesional para calcular, gestionar y exportar la liquidación de honorarios a especialistas de salud según reglas específicas por especialidad, plan y procedimiento.

---

## 🗂️ Carga y gestión de archivos
- Carga de archivo Excel con base de servicios.
- Validación de columnas requeridas (`CUPS`, `UVR`, `Especialista`, etc).
- Detección automática de faltantes (homologación/UVR).
- Edición manual de CUPS y UVR.
- Eliminación de duplicados (opcional).
- Botón “No aplica” para continuar sin completar.

---

## 👩‍⚕️ Gestión de profesionales
- Selección del profesional a liquidar.
- Agregar nuevos profesionales.
- Copiar configuración de otro profesional.
- Listado dinámico desde el archivo cargado.

---

## ⚙️ Configuraciones de liquidación
- Conversión de tarifas SOAT ↔ ISS.
- Checkbox: Anestesiología diferencial (+60%).
- Checkbox: Socio ortopedista, cirujano de pie/tobillo, reconstructivo.

---

## 📐 Reglas personalizadas por especialidad

Incluye fórmulas y tarifas para:

- **Anestesiología**: UVR ISS (960) +30%, mult. vía y diferencial.
- **Maxilofacial**: consulta e interconsulta fijas, proc. al 70%.
- **Fisiatría**: consultas, infiltraciones, juntas, proc. no quirúrgicos.
- **Dolor**: bloqueos, interconsultas, 70% valor facturado.
- **Laboral**: 85% consultas, 80% juntas.
- **Neurocirugía**: 70% SOAT, 80% otros.
- **Ortopedia pediátrica**: valores fijos por consulta y yesos.
- **Ortopedia general y socios**: diferenciación por plan.
- **Cirugía de pie/tobillo**: ISS+30% sin diferenciación por múltiple.
- **Cirugía reconstructiva**: valor fijo por paciente, ISS+20% otros.
- **Cirugía de mano**: ISS+30%, PGP al 30%.

---

## 📊 Cálculo y visualización
- Aplicación automática de fórmula por fila.
- Vista editable de valores liquidados.
- Cálculo de totales y % liquidado.

---

## 📤 Exportación y distribución
- Exportar resultados en Excel individual por profesional.
- Generar ZIP con informes.
- Exportación por lote y PDF por profesional (integración avanzada).
- Botón para envío por correo (opcional).

---

## 📈 Módulo de reportes
- Reportes por especialidad, plan, % y valor.
- Resumen por grupo o bloque de especialistas.
