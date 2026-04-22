"""Tests unitarios para src/utils/date_utils.py."""

import pytest
from datetime import date, datetime

from src.utils.date_utils import int_to_date, build_datetime


class TestIntToDate:
    def test_fecha_normal(self):
        assert int_to_date(20240115) == date(2024, 1, 15)

    def test_primer_dia_del_anio(self):
        assert int_to_date(20230101) == date(2023, 1, 1)

    def test_ultimo_dia_del_anio(self):
        assert int_to_date(20231231) == date(2023, 12, 31)

    def test_anio_bisiesto(self):
        assert int_to_date(20240229) == date(2024, 2, 29)

    def test_longitud_incorrecta_lanza_valueerror(self):
        with pytest.raises(ValueError):
            int_to_date(2024115)

    def test_fecha_invalida_lanza_valueerror(self):
        with pytest.raises((ValueError, Exception)):
            int_to_date(20241332)  # mes 13


class TestBuildDatetime:
    def test_construccion_normal(self):
        dt = build_datetime(20240115, 8, 30)
        assert dt == datetime(2024, 1, 15, 8, 30)

    def test_medianoche(self):
        dt = build_datetime(20240101, 0, 0)
        assert dt == datetime(2024, 1, 1, 0, 0)

    def test_ultima_hora(self):
        dt = build_datetime(20241231, 23, 59)
        assert dt == datetime(2024, 12, 31, 23, 59)
