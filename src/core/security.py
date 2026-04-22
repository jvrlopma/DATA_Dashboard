"""Gestion de credenciales cifradas con Fernet (cryptography).

Flujo:
  1. generate_key.py  -> genera secrets.key (Fernet key, 32 bytes en base64)
  2. encrypt_credentials.py -> lee secrets.key, cifra credenciales -> credentials.enc
  3. Esta clase (CredentialStore) -> descifra credentials.enc en memoria en runtime

Las rutas de secrets.key y credentials.enc se pasan via variables de entorno
SECRETS_KEY_PATH y CREDENTIALS_PATH. Nunca se hardcodean en el codigo.
"""

import json
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken


class CredentialStore:
    """Lee y descifra las credenciales de SQL Server en memoria.

    Los datos descifrados solo viven en RAM; nunca se escriben a disco ni logs.

    Args:
        key_path:         Ruta al fichero secrets.key.
        credentials_path: Ruta al fichero credentials.enc.

    Raises:
        FileNotFoundError: Si alguno de los dos ficheros no existe.
        ValueError:        Si la clave no puede descifrar el fichero de credenciales.
    """

    def __init__(self, key_path: Path | str, credentials_path: Path | str) -> None:
        self._key_path = Path(key_path)
        self._creds_path = Path(credentials_path)
        self._credentials: dict = self._load()

    def _load(self) -> dict:
        if not self._key_path.exists():
            raise FileNotFoundError(f"Fichero de clave no encontrado: {self._key_path}")
        if not self._creds_path.exists():
            raise FileNotFoundError(
                f"Fichero de credenciales no encontrado: {self._creds_path}"
            )

        key = self._key_path.read_bytes().strip()
        fernet = Fernet(key)

        try:
            encrypted = self._creds_path.read_bytes()
            plaintext = fernet.decrypt(encrypted)
        except InvalidToken as e:
            raise ValueError(
                "No se pudo descifrar el fichero de credenciales. "
                "Verifica que secrets.key corresponde a credentials.enc."
            ) from e

        return json.loads(plaintext.decode("utf-8"))

    @property
    def server(self) -> str:
        """Servidor SQL Server (hostname o IP)."""
        return self._credentials["server"]

    @property
    def database(self) -> str:
        """Nombre de la base de datos."""
        return self._credentials["database"]

    @property
    def user(self) -> str:
        """Usuario de SQL Server."""
        return self._credentials["user"]

    @property
    def password(self) -> str:
        """Contrasena de SQL Server (solo en memoria)."""
        return self._credentials["password"]

    def __repr__(self) -> str:
        return f"CredentialStore(server={self.server!r}, database={self.database!r}, user={self.user!r})"


def load_credentials_from_env() -> CredentialStore:
    """Carga las credenciales usando las rutas definidas en variables de entorno.

    Variables de entorno requeridas:
        SECRETS_KEY_PATH   - ruta absoluta a secrets.key
        CREDENTIALS_PATH   - ruta absoluta a credentials.enc

    Raises:
        EnvironmentError: Si alguna variable de entorno no esta definida.
        FileNotFoundError: Si alguno de los ficheros no existe.
    """
    key_path = os.environ.get("SECRETS_KEY_PATH", "")
    creds_path = os.environ.get("CREDENTIALS_PATH", "")

    missing = [v for v, val in [("SECRETS_KEY_PATH", key_path), ("CREDENTIALS_PATH", creds_path)]
               if not val]
    if missing:
        raise EnvironmentError(
            f"Variables de entorno no definidas: {', '.join(missing)}. "
            "Configuralas en el servicio de Windows antes de arrancar."
        )

    return CredentialStore(key_path, creds_path)


def generate_key() -> bytes:
    """Genera una nueva clave Fernet aleatoria.

    Returns:
        Bytes de la clave (base64 URL-safe, 44 caracteres).
    """
    return Fernet.generate_key()


def encrypt_credentials(key: bytes, server: str, database: str,
                        user: str, password: str) -> bytes:
    """Cifra las credenciales y devuelve los bytes cifrados.

    Args:
        key:      Clave Fernet (bytes).
        server:   Hostname o IP del servidor SQL Server.
        database: Nombre de la base de datos.
        user:     Usuario de SQL Server.
        password: Contrasena.

    Returns:
        Bytes cifrados listos para escribir en credentials.enc.
    """
    payload = json.dumps({
        "server": server,
        "database": database,
        "user": user,
        "password": password,
    }).encode("utf-8")
    return Fernet(key).encrypt(payload)
