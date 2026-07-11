"""
Recolección de tweets sobre precios de alimentos en Lima (2015-01-01 a 2024-06-30).
Usa todas las cuentas activas en el pool de twscrape en PARALELO (más cuentas = más rápido).
Se detiene automáticamente al alcanzar META_TWEETS. Guarda progreso incrementalmente
para poder cortar y reanudar sin perder avance ni repetir queries ya hechas.

Requisitos:
    uv pip install twscrape python-dotenv

Antes de correr:
    1. Configura tu .env (ver add_accounts.py) y corre: python add_accounts.py
    2. Ajusta META_TWEETS si quieres otro número.

Uso:
    python recolectar_tweets_precios_lima.py
"""
import truststore
truststore.inject_into_ssl()

import asyncio
import json
import os
import time
import unicodedata
from datetime import date
from dateutil.relativedelta import relativedelta

from twscrape import API, gather

# ------------------------------------------------------------------
# 1. Diccionarios de términos
# ------------------------------------------------------------------
PRODUCTOS = [
    "papa", "papa amarilla", "tomate", "pollo", "pollo entero", "arroz",
    "aceite", "cebolla", "limón", "huevo", "pan", "azúcar", "azúcar rubia",
    "leche", "leche evaporada", "leche fresca", "carne", "carne molida",
    "carne de res", "carne de cerdo", "chuleta de cerdo", "pescado", "atún",
    "trucha", "jurel", "bonito", "calamar", "camarón", "langostino",
    "camote", "yuca", "plátano", "palta", "naranja", "mandarina", "fideos",
    "lenteja", "frijol", "menestras", "arveja", "zanahoria", "ajo",
    "harina", "quinua", "kiwicha", "trigo", "choclo", "maíz", "apio",
    "betarraga", "vainita", "espinaca", "lechuga", "col", "coliflor",
    "brócoli", "champiñón", "pimiento", "ají", "culantro", "mango",
    "papaya", "sandía", "melón", "uva", "manzana", "pera", "piña",
    "queso", "queso fresco", "mantequilla", "margarina", "manteca",
    "yogurt", "sal", "avena", "café", "té", "cacao", "chocolate",
    "galletas", "mermelada", "vinagre", "mostaza", "mayonesa",
    "salsa de tomate", "leche condensada", "conserva de pescado",
    "gaseosa", "agua embotellada", "agua mineral", "jugo envasado",
    "cerveza", "vino", "pisco", "gas balón", "GLP", "gasolina", "diesel",
    "kerosene", "pasaje combi", "pasaje de bus", "peaje",
]

FRASES = [
    "está carísimo", "subió de precio", "no alcanza la plata", "por las nubes",
    "canasta básica", "inflación alimentos", "todo está caro",
    "los precios subieron", "no me alcanza el sueldo", "la plata no rinde",
    "sube el costo de vida", "canasta familiar cara", "aumento de precios",
    "alza de precios", "carestía de vida", "escasez de alimentos",
    "el kilo de papa", "ya no alcanza", "inflación en Perú", "el pasaje subió",
    "el pollo está caro", "todo subió de precio", "la canasta subió",
    "no me alcanza el dinero", "los alimentos suben", "aumentó el precio",
    "la inflación nos está matando", "el sueldo no alcanza",
    "cada vez más caro", "no se puede vivir así", "costo de vida en Perú",
    "crisis económica Perú", "el dólar subió", "tipo de cambio Perú",
    "aumento del pasaje", "paro de transportistas", "desabastecimiento",
    "especulación de precios", "acaparamiento de alimentos",
    "protesta por precios", "marcha por el alza de precios",
    "el precio se disparó", "los precios están locos",
    "no sé cómo vamos a vivir", "la economía está fatal",
    "el gobierno debería intervenir", "los comerciantes suben todo",
    "los intermediarios ganan más", "hay que importar alimentos",
    "el fenómeno El Niño subió los precios", "la sequía afectó las cosechas",
    "las lluvias dañaron los cultivos", "bloqueo de carreteras",
    "paro agrario", "paro de agricultores", "huelga de camioneros",
    "afectó la cosecha", "faltan productos en el mercado",
    "los supermercados suben precios", "Plaza Vea precios",
    "Metro precios", "Tottus precios", "Wong precios",
]

# Frases de tono positivo/neutro (para que el dataset no quede 100% negativo)
FRASES_POSITIVAS = [
    "bajó el precio", "bajaron los precios", "está más barato",
    "precio estable", "los precios se mantienen", "buena oferta en el mercado",
    "encontré barato", "rebajaron el precio", "por fin bajó el precio",
    "gracias a Dios está barato", "el precio del pollo bajó",
    "la papa está barata", "buenos precios en el mercado",
    "descuento en el mercado", "oferta de temporada", "precio accesible",
    "cosecha abundante", "buena cosecha este año", "mejoró la economía",
    "el sueldo alcanza mejor", "bajó la inflación", "controlaron los precios",
    "precios justos", "buen precio en el mercado", "alimentos accesibles",
]

MERCADOS = [
    "mercado mayorista Lima", "mercado central Lima", "mercado Santa Anita",
    "La Parada Lima", "feria de abastos Lima", "mercado de abastos Lima",
    "Gran Mercado Mayorista de Lima", "Mercado de Productores Santa Anita",
    "Terminal Pesquero Villa María del Triunfo", "Mercado Caquetá",
    "Mercado Unicachi", "Mercado Ceres", "Mercado Modelo Lima",
    "Mercado de Frutas Lima", "Mercado Mayorista N8", "Mercado Minorista N1",
    "Mercado de Comas", "Mercado de Independencia", "Mercado Productores Lima",
    "Mercado Grau", "Feria Agropecuaria Lima", "Mercado Surquillo N1",
    "Mercado Surquillo N2", "Mercado de Magdalena", "Mercado de Jesús María",
    "Mercado de Barranco", "Mercado Municipal de Miraflores",
    "Mercado de Pueblo Libre", "Mercado de San Isidro", "Mercado San Cosme",
    "Mercado Manco Cápac", "Mercado de Flores Surquillo", "Mercado Génova Chorrillos",
    "Camal de Yerbateros", "Parque Porcino Ate",
]

# Todos los distritos de Lima Metropolitana + Callao
DISTRITOS = [
    "Ancón", "Ate", "Barranco", "Bellavista", "Breña", "Callao", "Carabayllo",
    "Carmen de la Legua Reynoso", "Chaclacayo", "Chorrillos", "Cieneguilla",
    "Comas", "El Agustino", "Independencia", "Jesús María", "La Molina",
    "La Perla", "La Punta", "La Victoria", "Lince", "Los Olivos",
    "Lurigancho", "Lurín", "Magdalena del Mar", "Mi Perú", "Miraflores",
    "Pachacámac", "Pucusana", "Pueblo Libre", "Puente Piedra",
    "Punta Hermosa", "Punta Negra", "Rímac", "San Bartolo", "San Borja",
    "San Isidro", "San Juan de Lurigancho", "San Juan de Miraflores",
    "San Luis", "San Martín de Porres", "San Miguel", "Santa Anita",
    "Santa María del Mar", "Santa Rosa", "Santiago de Surco", "Surquillo",
    "Ventanilla", "Villa El Salvador", "Villa María del Triunfo",
]

CONTEXTO = "Lima"

SEED_TERMS = (
    [f"precio {p} {CONTEXTO}" for p in PRODUCTOS]
    + [f"{f} {CONTEXTO}" for f in FRASES]
    + [f"{f} {CONTEXTO}" for f in FRASES_POSITIVAS]
    + MERCADOS
    + [f"mercado {d}" for d in DISTRITOS]
    + [f"precio papa {d}" for d in DISTRITOS]
    + [f"canasta básica {d}" for d in DISTRITOS]
)

TWEETS_POR_QUERY = 60
LANG = "es"
META_TWEETS = 3000
RUTA_JSON = "bronce_tweets_precios_lima.json"
RUTA_COMPLETADAS = "queries_completadas.json"


def _sin_tildes(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def detectar_distrito(texto: str):
    texto_norm = _sin_tildes(texto.lower())
    for d in DISTRITOS:
        if _sin_tildes(d.lower()) in texto_norm:
            return d
    if "lima" in texto_norm:
        return "Lima (sin distrito específico)"
    return None


def generar_ventanas(inicio: date, fin: date, meses: int = 12):
    ventanas = []
    actual = inicio
    while actual < fin:
        siguiente = min(actual + relativedelta(months=meses), fin)
        ventanas.append((actual, siguiente))
        actual = siguiente
    return ventanas


VENTANAS = generar_ventanas(date(2015, 1, 1), date(2024, 6, 30), meses=12)


def cargar_json(ruta, default):
    if os.path.exists(ruta):
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def guardar_json(ruta, data):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def procesar_query(api, termino, desde, hasta, vistos, completadas):
    clave = f"{termino}|{desde.isoformat()}|{hasta.isoformat()}"
    if clave in completadas:
        return clave, []

    query = f'{termino} lang:{LANG} since:{desde.isoformat()} until:{hasta.isoformat()}'
    try:
        tweets = await gather(api.search(query, limit=TWEETS_POR_QUERY))
    except Exception as e:
        print(f"[WARN] fallo en '{query}': {e}")
        return None, []  # no marcar como completada, para reintentar despues

    nuevos = []
    for t in tweets:
        if t.id in vistos:
            continue
        vistos.add(t.id)
        nuevos.append({
            "id": t.id,
            "fecha": t.date.isoformat(),
            "comentario": t.rawContent,
            "distrito": detectar_distrito(t.rawContent),
            "likes": t.likeCount,
            "retweets": t.retweetCount,
            "termino_busqueda": termino,
        })
    return clave, nuevos


async def recolectar():
    api = API()

    cuentas = await api.pool.get_all()
    activas = [c for c in cuentas if c.active]
    if not activas:
        print("No hay ninguna cuenta activa. Corre primero: python add_accounts.py")
        return []

    concurrencia = len(activas)
    print(f"Cuentas activas: {concurrencia} -> concurrencia de {concurrencia} queries simultáneas")

    resultados = cargar_json(RUTA_JSON, [])
    completadas = set(cargar_json(RUTA_COMPLETADAS, []))
    vistos = {r["id"] for r in resultados}
    print(f"Tweets ya recolectados: {len(resultados)} | Queries ya completadas: {len(completadas)}")

    pendientes = [
        (termino, desde, hasta)
        for termino in SEED_TERMS
        for desde, hasta in VENTANAS
        if f"{termino}|{desde.isoformat()}|{hasta.isoformat()}" not in completadas
    ]
    print(f"Queries pendientes: {len(pendientes)}")

    inicio = time.time()

    for i in range(0, len(pendientes), concurrencia):
        if len(resultados) >= META_TWEETS:
            print(f"\n[META ALCANZADA] {len(resultados)} tweets únicos. Deteniendo.")
            break

        lote = pendientes[i:i + concurrencia]
        tareas = [procesar_query(api, t, d, h, vistos, completadas) for t, d, h in lote]
        respuestas = await asyncio.gather(*tareas)

        for clave, nuevos in respuestas:
            if clave is not None:
                completadas.add(clave)
            if nuevos:
                resultados.extend(nuevos)

        guardar_json(RUTA_JSON, resultados)
        guardar_json(RUTA_COMPLETADAS, sorted(completadas))

        transcurrido_min = (time.time() - inicio) / 60
        n = len(resultados)
        pct = min(100, n / META_TWEETS * 100)
        ritmo = n / transcurrido_min if transcurrido_min > 0 else 0
        restante_min = max(0, (META_TWEETS - n) / ritmo) if ritmo > 0 else float("inf")
        print(
            f"  >> Progreso: {n}/{META_TWEETS} ({pct:.1f}%) | "
            f"transcurrido: {transcurrido_min:.1f} min | "
            f"estimado restante: {restante_min:.1f} min"
        )

    print(f"\nTotal final: {len(resultados)} tweets únicos -> {RUTA_JSON}")
    return resultados


if __name__ == "__main__":
    asyncio.run(recolectar())
