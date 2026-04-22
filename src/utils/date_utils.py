"""Utilidades de conversion de fechas para DATA_Dashboard."""

from datetime import date, datetime


def int_to_date(n: int) -> date:
    """Convierte un entero YYYYMMDD a un objeto date.

    Args:
        n: Fecha en formato YYYYMMDD (ej.: 20240115).

    Returns:
        Objeto date correspondiente.

    Raises:
        ValueError: Si el entero no representa una fecha valida.
    """
    s = str(n)
    if len(s) != 8:
        raise ValueError(f"Se esperaba un entero YYYYMMDD de 8 digitos, se recibio: {n!r}")
    return date(int(s[:4]), int(s[4:6]), int(s[6:8]))


def build_datetime(nfecha: int, hora: int, minuto: int) -> datetime:
    """Construye un datetime a partir de los campos de ejecucion del Excel.

    Args:
        nfecha: Fecha en formato YYYYMMDD.
        hora:   Hora de ejecucion (0-23).
        minuto: Minuto de ejecucion (0-59).

    Returns:
        Objeto datetime con la fecha y hora de la ejecucion.
    """
    d = int_to_date(nfecha)
    return datetime(d.year, d.month, d.day, hora, minuto)
