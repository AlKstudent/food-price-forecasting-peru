"""
Agrega o actualiza todas las cuentas definidas en .env (patrón X_USERNAME_N / X_COOKIES_N)
al pool de twscrape usando cookies de sesión. Soporta 1 o varias cuentas.

.env esperado:
    X_USERNAME_1=Danielqv26
    X_COOKIES_1=auth_token=...; ct0=...
    X_USERNAME_2=otra_cuenta      (opcional)
    X_COOKIES_2=auth_token=...; ct0=...   (opcional)

Uso:
    python add_accounts.py
"""
import truststore
truststore.inject_into_ssl()

import asyncio
import os
from dotenv import load_dotenv
from twscrape import API

load_dotenv()


def leer_cuentas_env():
    cuentas = []
    n = 1
    while True:
        username = os.environ.get(f"X_USERNAME_{n}")
        cookies = os.environ.get(f"X_COOKIES_{n}")
        if not username or not cookies:
            break
        cuentas.append({"username": username, "cookies": cookies})
        n += 1
    return cuentas


async def main():
    cuentas_env = leer_cuentas_env()
    if not cuentas_env:
        print("No se encontró ninguna cuenta en .env (esperaba X_USERNAME_1 / X_COOKIES_1).")
        return

    api = API()
    existentes = {c.username for c in await api.pool.get_all()}

    for cuenta in cuentas_env:
        if cuenta["username"] in existentes:
            await api.pool.delete_accounts([cuenta["username"]])
        await api.pool.add_account(
            cuenta["username"], "unused", "unused@unused.com", "unused",
            cookies=cuenta["cookies"],
        )

    print("\nEstado final del pool:")
    for c in await api.pool.get_all():
        print(f"  {c.username}: active={c.active}")


if __name__ == "__main__":
    asyncio.run(main())
