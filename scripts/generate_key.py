"""Genera una clave Fernet nueva y la guarda en secrets.key.

Ejecutar UNA SOLA VEZ en el servidor destino, antes de cifrar credenciales.
La clave generada debe guardarse en una ruta protegida por permisos NTFS
(ver docs/SECURITY.md para la configuracion de permisos recomendada).

Uso:
    python scripts/generate_key.py [--out RUTA]

Argumentos:
    --out  Ruta donde guardar secrets.key (por defecto: secrets.key en el CWD).

AVISO: si ya existe un fichero secrets.key en la ruta destino, el script
pedira confirmacion antes de sobreescribirlo, ya que los credentials.enc
generados con la clave anterior quedarian inutilizables.
"""

import argparse
import sys
from pathlib import Path

from cryptography.fernet import Fernet


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera una clave Fernet para DATA_Dashboard.")
    parser.add_argument(
        "--out", default="secrets.key",
        help="Ruta de salida para la clave (default: secrets.key)"
    )
    args = parser.parse_args()

    out_path = Path(args.out)

    if out_path.exists():
        resp = input(
            f"AVISO: '{out_path}' ya existe. Si lo sobreescribes, el fichero\n"
            f"credentials.enc actual quedara INUTILIZABLE.\n"
            f"Continuar? (s/N): "
        ).strip().lower()
        if resp != "s":
            print("Operacion cancelada.")
            sys.exit(0)

    key = Fernet.generate_key()
    out_path.write_bytes(key)

    print(f"Clave generada y guardada en: {out_path.resolve()}")
    print()
    print("IMPORTANTE:")
    print(f"  1. Mueve '{out_path}' a la ruta protegida del servidor (fuera del repo y del .exe).")
    print( "  2. Configura permisos NTFS: solo la cuenta de servicio puede leer este fichero.")
    print( "  3. Ejecuta 'python scripts/encrypt_credentials.py' para cifrar las credenciales.")
    print( "  4. Guarda una copia de seguridad de la clave en un lugar seguro.")


if __name__ == "__main__":
    main()
