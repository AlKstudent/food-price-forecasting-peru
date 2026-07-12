# Food Price Forecasting Perú
### Sistema de Alerta Temprana de Inflación de Alimentos Básicos en Mercados de Lima

Proyecto desarrollado como trabajo final para el curso de **Big Data (UNMSM)**. El sistema anticipa la volatilidad de precios mayoristas con dos semanas de antelación, integrando múltiples fuentes de datos estructurados y no estructurados (SISAP, SENAMHI, SUNAT y Twitter) mediante una arquitectura Big Data.

---

## Demo y Visualización

* **Video Demostrativo:** [Ver Demo en YouTube](https://youtu.be/JCnsvEPCe_E)
* **Dashboard Interactivo en vivo:** [Alerta de Precios de Alimentos - Lima](https://food-price-forecasting-peru-olfdb5ejpdckasaxwkrrgq.streamlit.app/)

---

## Integrantes y Participación (Grupo 5)

Todos los miembros participaron activamente en el diseño, desarrollo e implementación de la arquitectura de datos y modelado.

* **Alexis Medrano Rivera** - 25%
* **Andrew Rivera Laura** - 25%
* **Carlos Garrido Silva** - 25%
* **Daniel Quispe Villena** - 25%

---

## Arquitectura del Data Lake (Medallion en GCP)

El procesamiento se realiza de forma distribuida utilizando **Apache Spark (PySpark)** sobre **Google Cloud Storage**:

* **Zona Bronce (Raw):** Ingesta cruda de SISAP-MIDAGRI, SENAMHI, SUNAT, INEI y Twitter (vía `twscrape`).
* **Zona Plata (Cleaned):** Limpieza, joins espaciales/temporales y análisis de sentimiento (VADER).
* **Zona Oro (Aggregated):** Tablas de negocio (`kpi_precios`, `kpi_sentimiento`, `clusters_productos`) optimizadas en formato Parquet.

---

## Modelos de Machine Learning (MLflow)

Los experimentos han sido auditados bajo el ciclo de vida de MLflow:

1. **Forecasting:** Modelos **Regresión Lineal**, **Random Forest** y **XGBoost** para la predicción de precios a 2 semanas.
2. **Segmentación:** Algoritmos **KMeans** y **Agglomerative Clustering** (Jerárquico) para agrupar productos por perfiles de volatilidad.
3. **Clasificación:** Modelos **Random Forest**, **GBT Classifier** y **Regresión Logística** para detección de alertas de subida (>10%).

---

## Estructura del Repositorio

```text
.
├── dashboard/         # Código fuente de la app (Streamlit) y datos (Zona Oro)
├── data/              # Documentación de la arquitectura (Datos pesados ignorados)
├── docs/              # Reporte metodológico final y registros de mlruns (PDFs)
├── notebooks/         # Notebooks 01-07 (ETL en PySpark y Modelado ML)
├── scripts/           # Scripts de recolección automatizada (.py)
├── .gitignore         # Configuración de seguridad (credentials, .csv, .parquet, etc.)
└── README.md          # Documentación principal
