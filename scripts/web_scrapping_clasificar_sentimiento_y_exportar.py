"""
Clasifica el sentimiento de los tweets recolectados (1=positivo, 0=negativo)
usando RoBERTuito (modelo en español entrenado específicamente en tweets),
y exporta el CSV final con columnas: fecha, comentario, distrito, sentimiento.

Requisitos (pesado, ~2-3 GB de descarga la primera vez por PyTorch + modelo):
    uv pip install pysentimiento torch pandas

Uso:
    python clasificar_sentimiento_y_exportar.py
"""
import truststore
truststore.inject_into_ssl()

import json

import pandas as pd
from pysentimiento import create_analyzer

RUTA_JSON = "bronce_tweets_precios_lima.json"
RUTA_CSV_FINAL = "tweets_precios_lima_final.csv"
META_TWEETS = 3000
TAM_LOTE = 32


def main():
    with open(RUTA_JSON, "r", encoding="utf-8") as f:
        resultados = json.load(f)

    df = pd.DataFrame(resultados).drop_duplicates(subset="comentario").reset_index(drop=True)
    print(f"Tweets únicos disponibles: {len(df)}")

    if len(df) > META_TWEETS:
        df = df.sample(META_TWEETS, random_state=42).reset_index(drop=True)
        print(f"Muestreado a {META_TWEETS} tweets.")

    print("Cargando modelo de sentimiento (RoBERTuito, primera vez tarda por la descarga)...")
    analyzer = create_analyzer(task="sentiment", lang="es")

    textos = df["comentario"].tolist()
    etiquetas = []

    for i in range(0, len(textos), TAM_LOTE):
        lote = textos[i:i + TAM_LOTE]
        predicciones = analyzer.predict(lote)
        for pred in predicciones:
            if pred.output == "POS":
                etiquetas.append(1)
            elif pred.output == "NEG":
                etiquetas.append(0)
            else:  # NEU: desempata con la probabilidad más alta entre POS y NEG
                etiquetas.append(1 if pred.probas["POS"] >= pred.probas["NEG"] else 0)
        print(f"  Clasificados {min(i + TAM_LOTE, len(textos))}/{len(textos)}")

    df["sentimiento"] = etiquetas

    df[["fecha", "comentario", "distrito", "sentimiento"]].to_csv(
        RUTA_CSV_FINAL, index=False, encoding="utf-8"
    )

    print(f"\nCSV final: {len(df)} tweets -> {RUTA_CSV_FINAL}")
    print(df["sentimiento"].value_counts())


if __name__ == "__main__":
    main()
