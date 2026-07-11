# 🌽 Food Price Forecasting Perú
### Sistema de Alerta Temprana de Inflación de Alimentos Básicos en Mercados de Lima

Este repositorio contiene el pipeline de Big Data y Machine Learning desarrollado como Proyecto Final del curso de **Big Data Analytics (UNMSM)**. El sistema anticipa la volatilidad de precios mayoristas con dos semanas de anticipación integrando múltiples fuentes de datos estructurados y no estructurados.


---

## 🏗️ Arquitectura del Data Lake (Medallion en GCP)
El proyecto utiliza **Google Cloud Storage** como repositorio central, procesado de forma distribuida mediante **Apache Spark (PySpark)**:

* **🥉 Zona Bronce (Raw):** Ingesta cruda de SISAP-MIDAGRI (Precios), SENAMHI (Clima), SUNAT (Importaciones), INEI (Shapefiles) y Twitter (Scraping vía `twscrape`).
* **🥈 Zona Plata (Cleaned):** Limpieza, joins espaciales (GeoPandas) y temporales, cálculo de lags y Análisis de Sentimiento (VADER). Almacenado en formato Parquet.
* **🥇 Zona Oro (Aggregated):** Tablas de negocio estructuradas con KPIs (`kpi_precios`, `kpi_sentimiento` y `clusters_productos`) listas para alimentar el Dashboard.

---

## 🧠 Modelos de Machine Learning (MLflow)
Todos los experimentos y artefactos fueron auditados y registrados usando **MLflow**:

1. **Forecasting (Regresión):** Gradient Boosted Trees (GBT) para predecir el precio exacto a 2 semanas.
2. **Segmentación (Clustering):** Algoritmo KMeans para agrupar productos por su perfil de volatilidad histórica.
3. **Clasificador de Alerta Binaria:** Random Forest para predecir si un producto subirá más del 10% en las próximas dos semanas.

---

## 📂 Estructura del Repositorio

```text
.
├── dashboard/         # Archivo .pbix de Power BI con las 6 vistas
├── data/              # README sustentando la arquitectura en GCS
├── docs/              # Reporte Metodológico y registros de mlruns
├── notebooks/         # Notebooks 01 al 07 (ETL en PySpark y Modelado ML)
├── scripts/           # Scripts de recolección automatizada (.py)
├── .gitignore         # Reglas de seguridad para credenciales GCP y Big Data
└── README.md          # Documentación principal
