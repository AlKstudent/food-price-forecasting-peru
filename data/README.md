# Data Lake (Arquitectura Medallion)

 **Nota: Esta carpeta está intencionalmente vacía en el repositorio.**

Este proyecto implementa una arquitectura real de Big Data. Debido a los altos volúmenes de información manejados en el pipeline, los archivos de datos no se controlan mediante Git.

Toda la data estructurada y no estructurada está centralizada en **Google Cloud Storage (GCS)**, dividida en tres capas para garantizar escalabilidad:

* **Zona Bronce:** Datos crudos (SISAP, SENAMHI, SUNAT, INEI, Tweets).
* **Zona Plata:** Datos limpios, integrados y enriquecidos (formato Parquet).
* **Zona Oro:** KPIs, resultados de clustering y data lista para el Dashboard.

Los notebooks de la carpeta `/notebooks` se conectan directamente al bucket de GCP para ejecutar las transformaciones distribuidas en Apache Spark.
