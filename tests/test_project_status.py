"""Tests exhaustivos de la logica de estado de proyectos ETL.

Cubre todos los casos limite exigidos en PROJECT_SPEC.md seccion 2.2:
    Grupo A: xEjecutadosOK == 100 (OK) y < 100 (CRITICO)
    Grupo B: >= 90 (OK), >= 80 y < 90 (REGULAR), < 80 (CRITICO)
    Transversal: sin ejecuciones recientes -> CRITICO + sin_datos_recientes
"""

import pytest
from datetime import datetime, timedelta

from src.domain.models import ProjectStatus, ProjectHealth
from src.domain.project_status import (
    compute_status,
    compute_project_health,
    execution_from_row,
)

import pandas as pd

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2024, 1, 15, 12, 0)  # momento fijo para los tests

PROYECTO_A = "AqualiaDW"          # Grupo A
PROYECTO_B = "AqualiaODS"         # Grupo B


def _make_execution(proyecto: str, xok: float, horas_atras: float = 1.0):
    """Crea un Execution ficticio con datetime_ejecucion reciente."""
    from src.domain.models import Execution
    dt = NOW - timedelta(hours=horas_atras)
    return Execution(
        id=1, proyecto=proyecto,
        nFecha_ejecucion=int(dt.strftime("%Y%m%d")),
        hora_ejecucion=dt.hour, minuto_ejecucion=dt.minute,
        nTotalEjecuciones=100, nEjecutadosOkProc=int(xok),
        nErrorProc=100 - int(xok), nEsperaProc=0, nEnEjecucionProc=0,
        nTotalInstalaciones=100, nEjecutadosOkInst=100,
        nErrorInst=0, nEsperaInst=0, nEnEjecucionInst=0,
        xEjecutadosOK=xok, xError=100.0 - xok,
        xEspera=0.0, xEnEjecucion=0.0,
        datetime_ejecucion=dt,
    )


# ---------------------------------------------------------------------------
# compute_status — Grupo A
# ---------------------------------------------------------------------------

class TestComputeStatusGrupoA:
    """Proyectos: AqualiaApemsa, AqualiaDW, AqualiaSII2_FICO, Aqualia_Diario."""

    @pytest.mark.parametrize("proyecto", [
        "AqualiaApemsa", "AqualiaDW", "AqualiaSII2_FICO", "Aqualia_Diario"
    ])
    def test_100_es_ok(self, proyecto):
        assert compute_status(proyecto, 100.0) == ProjectStatus.OK

    @pytest.mark.parametrize("proyecto", [
        "AqualiaApemsa", "AqualiaDW", "AqualiaSII2_FICO", "Aqualia_Diario"
    ])
    def test_99_99_es_critico(self, proyecto):
        assert compute_status(proyecto, 99.99) == ProjectStatus.CRITICO

    @pytest.mark.parametrize("proyecto", [
        "AqualiaApemsa", "AqualiaDW", "AqualiaSII2_FICO", "Aqualia_Diario"
    ])
    def test_90_es_critico(self, proyecto):
        assert compute_status(proyecto, 90.0) == ProjectStatus.CRITICO

    @pytest.mark.parametrize("proyecto", [
        "AqualiaApemsa", "AqualiaDW", "AqualiaSII2_FICO", "Aqualia_Diario"
    ])
    def test_0_es_critico(self, proyecto):
        assert compute_status(proyecto, 0.0) == ProjectStatus.CRITICO


# ---------------------------------------------------------------------------
# compute_status — Grupo B
# ---------------------------------------------------------------------------

class TestComputeStatusGrupoB:
    """Proyectos: AqualiaODS, AqualiaSII2_Doc_AEF, AqualiaTPL, Aqualia_GIS."""

    @pytest.mark.parametrize("proyecto", [
        "AqualiaODS", "AqualiaSII2_Doc_AEF", "AqualiaTPL", "Aqualia_GIS"
    ])
    def test_100_es_ok(self, proyecto):
        assert compute_status(proyecto, 100.0) == ProjectStatus.OK

    @pytest.mark.parametrize("proyecto", [
        "AqualiaODS", "AqualiaSII2_Doc_AEF", "AqualiaTPL", "Aqualia_GIS"
    ])
    def test_90_es_ok(self, proyecto):
        assert compute_status(proyecto, 90.0) == ProjectStatus.OK

    @pytest.mark.parametrize("proyecto", [
        "AqualiaODS", "AqualiaSII2_Doc_AEF", "AqualiaTPL", "Aqualia_GIS"
    ])
    def test_89_99_es_regular(self, proyecto):
        assert compute_status(proyecto, 89.99) == ProjectStatus.REGULAR

    @pytest.mark.parametrize("proyecto", [
        "AqualiaODS", "AqualiaSII2_Doc_AEF", "AqualiaTPL", "Aqualia_GIS"
    ])
    def test_80_es_regular(self, proyecto):
        assert compute_status(proyecto, 80.0) == ProjectStatus.REGULAR

    @pytest.mark.parametrize("proyecto", [
        "AqualiaODS", "AqualiaSII2_Doc_AEF", "AqualiaTPL", "Aqualia_GIS"
    ])
    def test_79_99_es_critico(self, proyecto):
        assert compute_status(proyecto, 79.99) == ProjectStatus.CRITICO

    @pytest.mark.parametrize("proyecto", [
        "AqualiaODS", "AqualiaSII2_Doc_AEF", "AqualiaTPL", "Aqualia_GIS"
    ])
    def test_0_es_critico(self, proyecto):
        assert compute_status(proyecto, 0.0) == ProjectStatus.CRITICO


# ---------------------------------------------------------------------------
# compute_status — proyecto desconocido
# ---------------------------------------------------------------------------

class TestComputeStatusProyectoDesconocido:
    def test_proyecto_desconocido_lanza_valueerror(self):
        with pytest.raises(ValueError, match="Proyecto desconocido"):
            compute_status("ProyectoInexistente", 100.0)


# ---------------------------------------------------------------------------
# compute_project_health — con datos recientes
# ---------------------------------------------------------------------------

class TestComputeProjectHealthConDatos:
    def test_grupo_a_100_ok(self):
        exec_ = _make_execution(PROYECTO_A, 100.0)
        h = compute_project_health(PROYECTO_A, exec_, NOW)
        assert h.estado == ProjectStatus.OK
        assert h.sin_datos_recientes is False
        assert h.xEjecutadosOK == 100.0

    def test_grupo_a_99_critico(self):
        exec_ = _make_execution(PROYECTO_A, 99.0)
        h = compute_project_health(PROYECTO_A, exec_, NOW)
        assert h.estado == ProjectStatus.CRITICO
        assert h.sin_datos_recientes is False

    def test_grupo_b_90_ok(self):
        exec_ = _make_execution(PROYECTO_B, 90.0)
        h = compute_project_health(PROYECTO_B, exec_, NOW)
        assert h.estado == ProjectStatus.OK

    def test_grupo_b_85_regular(self):
        exec_ = _make_execution(PROYECTO_B, 85.0)
        h = compute_project_health(PROYECTO_B, exec_, NOW)
        assert h.estado == ProjectStatus.REGULAR

    def test_grupo_b_79_critico(self):
        exec_ = _make_execution(PROYECTO_B, 79.0)
        h = compute_project_health(PROYECTO_B, exec_, NOW)
        assert h.estado == ProjectStatus.CRITICO

    def test_ultima_ejecucion_correcta(self):
        exec_ = _make_execution(PROYECTO_A, 100.0, horas_atras=2.0)
        h = compute_project_health(PROYECTO_A, exec_, NOW)
        assert h.ultima_ejecucion == exec_.datetime_ejecucion


# ---------------------------------------------------------------------------
# compute_project_health — sin datos recientes
# ---------------------------------------------------------------------------

class TestComputeProjectHealthSinDatos:
    def test_none_execution_es_critico_sin_datos(self):
        h = compute_project_health(PROYECTO_A, None, NOW)
        assert h.estado == ProjectStatus.CRITICO
        assert h.sin_datos_recientes is True
        assert h.xEjecutadosOK is None
        assert h.ultima_ejecucion is None

    def test_ejecucion_hace_25h_es_sin_datos(self):
        exec_ = _make_execution(PROYECTO_A, 100.0, horas_atras=25.0)
        h = compute_project_health(PROYECTO_A, exec_, NOW, inactivity_hours=24)
        assert h.estado == ProjectStatus.CRITICO
        assert h.sin_datos_recientes is True

    def test_ejecucion_hace_24h_exactas_es_sin_datos(self):
        # El limite es estricto: < limite => sin datos
        exec_ = _make_execution(PROYECTO_A, 100.0, horas_atras=24.0)
        h = compute_project_health(PROYECTO_A, exec_, NOW, inactivity_hours=24)
        assert h.sin_datos_recientes is True

    def test_ejecucion_hace_23h_tiene_datos(self):
        exec_ = _make_execution(PROYECTO_A, 100.0, horas_atras=23.0)
        h = compute_project_health(PROYECTO_A, exec_, NOW, inactivity_hours=24)
        assert h.sin_datos_recientes is False

    def test_etiqueta_estado_sin_datos(self):
        h = compute_project_health(PROYECTO_A, None, NOW)
        assert h.etiqueta_estado == "Sin datos recientes"

    def test_etiqueta_estado_ok(self):
        exec_ = _make_execution(PROYECTO_A, 100.0)
        h = compute_project_health(PROYECTO_A, exec_, NOW)
        assert h.etiqueta_estado == "OK"

    def test_etiqueta_estado_regular(self):
        exec_ = _make_execution(PROYECTO_B, 85.0)
        h = compute_project_health(PROYECTO_B, exec_, NOW)
        assert h.etiqueta_estado == "REGULAR"


# ---------------------------------------------------------------------------
# execution_from_row
# ---------------------------------------------------------------------------

class TestExecutionFromRow:
    def test_construye_execution_desde_series(self):
        row = pd.Series({
            "Id": 42, "proyecto": "AqualiaDW",
            "nFecha_ejecucion": 20240115, "Hora_ejecucion": 8, "Minuto_ejecucion": 30,
            "nTotalEjecuciones": 100, "nEjecutadosOkProc": 100, "nErrorProc": 0,
            "nEsperaProc": 0, "nEnEjecucionProc": 0,
            "nTotalInstalaciones": 200, "nEjecutadosOkInst": 200,
            "nErrorInst": 0, "nEsperaInst": 0, "nEnEjecucionInst": 0,
            "xEjecutadosOK": 100.0, "xError": 0.0, "xEspera": 0.0, "xEnEjecucion": 0.0,
        })
        exec_ = execution_from_row(row)
        assert exec_.id == 42
        assert exec_.proyecto == "AqualiaDW"
        assert exec_.xEjecutadosOK == 100.0
        assert exec_.datetime_ejecucion == datetime(2024, 1, 15, 8, 30)
