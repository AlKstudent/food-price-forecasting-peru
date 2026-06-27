# food-price-forecasting-peru
Big Data pipeline for predictive analytics on food commodity prices in Peru using Apache Spark, MLflow, and time series modeling.
## Estructura del Proyecto

```text
.
├── app/               # Dashboard Streamlit
├── data/              # Arquitectura Medallion
│   ├── bronce/        # Datos crudos (Raw)
│   ├── plata/         # Datos procesados (Cleaned)
│   └── oro/           # Datos finales (Aggregated)
├── docs/              # Entregables y arquitectura
├── notebooks/         # Experimentos y EDA
├── scripts/           # Scripts de recolección de datos
└── src/               # Lógica del pipeline ETL
