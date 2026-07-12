# Food Price Forecasting Perú
### Sistema de Alerta Temprana de Inflación de Alimentos Básicos en Mercados de Lima

Proyecto desarrollado como trabajo final para el curso de **Big Data Analytics (UNMSM)**. El sistema anticipa la volatilidad de precios mayoristas con dos semanas de antelación, integrando fuentes de datos estructurados y no estructurados mediante una arquitectura Big Data.

---

## Dashboard en vivo
Puedes visualizar el dashboard interactivo desplegado en la nube aquí:
[**Dashboard: Alerta de Precios de Alimentos - Lima**](https://food-price-forecasting-peru-olfdb5ejpdckasaxwkrrgq.streamlit.app/)

---

## Arquitectura del Data Lake (Medallion en GCP)
El procesamiento se realiza de forma distribuida utilizando **Apache Spark (PySpark)** sobre **Google Cloud Storage**:

* **Zona Bronce (Raw):** Ingesta cruda de SISAP-MIDAGRI, SENAMHI, SUNAT, INEI y Twitter (vía `twscrape`).
* **Zona Plata (Cleaned):** Limpieza, joins espaciales/temporales y análisis de sentimiento (VADER).
* **Zona Oro (Aggregated):** Tablas de negocio (`kpi_precios`, `kpi_sentimiento`, `clusters_productos`) optimizadas en formato Parquet.

---

## Modelos de Machine Learning (MLflow)
Los experimentos han sido auditados bajo el ciclo de vida de MLflow:

1.  **Forecasting:** Modelos ARIMA y LSTM para la predicción de precios a 2 semanas.
2.  **Segmentación:** Algoritmo KMeans para agrupar productos por perfiles de volatilidad.
3.  **Clasificación:** Random Forest para detección de alertas de subida (>10%).

---

## Estructura del Repositorio

```text
.
├── dashboard/         # Código fuente de la app (Streamlit) y datos (Zona Oro)
├── data/              # Documentación de la arquitectura en GCS
├── docs/              # Reporte metodológico y registros de mlruns
├── notebooks/         # Notebooks 01-07 (ETL en PySpark y Modelado ML)
├── scripts/           # Scripts de recolección automatizada (.py)
├── .gitignore         # Configuración de seguridad (credentials, etc.)
└── README.md          # Documentación principal
