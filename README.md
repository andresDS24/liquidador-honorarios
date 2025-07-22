# Liquidador Honorarios Web

Este sistema es una plataforma interactiva desarrollada con **Streamlit** para cargar, analizar y liquidar honorarios médicos de forma automatizada con base en especialidades, tipos de procedimiento, cobertura y reglas específicas por profesional. 

---

## 🧠 Funcionalidad General

El sistema permite:

- 📅 Carga de archivo Excel con información de servicios prestados.
- ✅ Eliminación de duplicados.
- 🧮 Homologación automática de códigos SOAT a CUPS.
- 📃 Asignación automática de UVR desde base interna.
- ✏️ Ingreso manual de UVR con replicación a códigos repetidos.
- 🔄 Unificación de especialidades por profesional.
- 👩‍⚕️ Selección de profesional y aplicación de parámetros de liquidación.
- 🔄 Modificación manual de valores.
- 🔗 Exportación a Excel o PDF.
- 🔒 Panel de parametrización de especialistas.
- 📊 Módulo de reportes e informes.

---

## 📜 Flujo de liquidación

1. Cargar archivo Excel.
2. Homologar códigos SOAT a CUPS.
3. Buscar UVR correspondiente de forma automática.
4. Ingresar manualmente UVR si no se encuentra y replicar.
5. Seleccionar especialista y aplicar reglas.
6. Revisar y modificar valores si es necesario.
7. Exportar informe individual o consolidado.

---

## 📊 Informes disponibles

- Valor total facturado.
- Valor total liquidado por profesional.
- Porcentaje liquidado sobre valor facturado.
- Informes por bloque de especialistas.

---

## 📂 Estructura de archivos esperada

| Columna           | Descripción                               |
|------------------|--------------------------------------------|
| `CUPS`           | Código del procedimiento                   |
| `Especialista`   | Nombre del profesional                      |
| `Especialidad`   | Tipo de especialidad                        |
| `Tipo Procedimiento` | Consulta, Proced Qx, etc.               |
| `Plan Beneficios`| EPS, SOAT, etc.                             |
| `Valor Total`    | Valor total facturado                       |
| `Valor UVR`      | Si aplica, UVR del procedimiento            |

---

## 🔄 Lógica por especialidad

- **Anestesiología:** ISS * 960 + 30%, ajustado por vía. Opcional: incremento al 60%.
- **Ortopedia General:** Consulta fija $27,000. Procedimientos quirúrgicos: ISS + 20%. No quirúrgicos: 70% del valor facturado.
- **Socios Ortopedia:** SOAT: 70%. No SOAT: 85% del valor facturado.
- **Cirujano Mano / Pie / Reconstructivo:** ISS + 30% sobre UVR, con excepciones por grupo.
- **Maxilofacial, Medicina del dolor, Fisiatría, etc.:** Consultas y procedimientos con valores fijos o porcentajes del valor facturado según reglas propias.

---

## 🤝 Funciones avanzadas

- Eliminar filas duplicadas.
- Crear nuevo especialista y copiar parámetros de otro.
- Identificar códigos sin UVR y permitir ingreso manual.
- Homologación de SOAT a ISS con base interna.
- Campo para seleccionar y unificar especialidades por profesional.
- Exportar por lote informes discriminados en archivos individuales.

---

## 🌐 Ejecución local

```bash
# Crear entorno virtual
python -m venv env
source env/bin/activate   # o .\env\Scripts\activate en Windows

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
streamlit run app.py
```

---

## 🧪 Sugerencia de mejoras futuras

- Dashboard con métricas agregadas
- Base de datos relacional para especialistas
- Reportes automáticos mensuales

---

Desarrollado para **Andrés Díaz Solano & Clínica de Fracturas SAS**
