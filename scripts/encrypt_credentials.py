"""Cifra las credenciales de SQL Server y las guarda en credentials.enc.

Requiere que secrets.key haya sido generado previamente con generate_key.py.
Las credenciales se piden de forma interactiva por consola y nunca se
escriben en texto plano a disco.

Uso:
    python scripts/encrypt_credentials.py [--key RUTA_KEY] [--out RUTA_ENC]

Argumentos:
    --key  Ruta a secrets.key (default: secrets.key en el CWD).
    --out  Ruta de salida para credentials.enc (default: credentials.enc en el CWD).
"""

import argparse
import getpass
import sys
from pathlib import Path

from src.core.security import encrypt_credentials


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cifra credenciales SQL Server para DATA_Dashboard."
    )
    parser.add_argument("--key", default="secrets.key",
                        help="Ruta a secrets.key (default: secrets.key)")
    parser.add_argument("--out", default="credentials.enc",
                        help="Ruta de salida de credentials.enc (default: credentials.enc)")
    args = parser.parse_args()

    key_path = Path(args.key)
    out_path = Path(args.out)

    if not key_path.exists():
        print(f"ERROR: No se encuentra '{key_path}'. Genera primero la clave con generate_key.py.")
        sys.exit(1)

    key = key_path.read_bytes().strip()

    print("=== Cifrado de credenciales SQL Server — DATA_Dashboard ===")
    print(f"Clave: {key_path.resolve()}")
    print(f"Salida: {out_path.resolve()}")
    print()
    print("Introduce los datos de conexion (la contrasena no se mostrara en pantalla):")
    print()

    server   = input("  Servidor SQL Server (hostname o IP): ").strip()
    database = input("  Base de datos: ").strip()
    user     = input("  Usuario: ").strip()
    password = getpass.getpass("  Contrasena: ")

    if not all([server, database, user, password]):
        print("ERROR: Todos los campos son obligatorios.")
        sys.exit(1)

    # Verificacion
    print()
    print("Resumen (sin contrasena):")
    print(f"  Servidor:  {server}")
    print(f"  Base datos: {database}")
    print(f"  Usuario:   {user}")
    resp = input("Cifrar y guardar? (s/N): ").strip().lower()
    if resp != "s":
        print("Operacion cancelada.")
        sys.exit(0)

    encrypted = encrypt_credentials(key, server, database, user, password)
    out_path.write_bytes(encrypted)

    print()
    print(f"Credenciales cifradas guardadas en: {out_path.resolve()}")
    print()
    print("IMPORTANTE:")
    print(f"  1. Mueve '{out_path}' a la ruta protegida del servidor (junto a secrets.key).")
    print( "  2. Configura SECRETS_KEY_PATH y CREDENTIALS_PATH en el servicio de Windows.")
    print( "  3. Verifica permisos NTFS: solo la cuenta de servicio puede leer ambos ficheros.")
    print( "  4. Elimina cualquier copia temporal de este script que contenga la contrasena.")


if __name__ == "__main__":
    main()
