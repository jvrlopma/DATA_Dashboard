"""Tests unitarios para ExcelRepository."""

import pytest
from datetime import date
from pathlib import Path

from src.core.data_access.excel_repository import ExcelRepository

FIXTURE = Path(__file__).parent / "fixtures" / "sample_executions.xlsx"

# Proyectos presentes en la fixture
PROYECTOS = ["AqualiaDW", "AqualiaODS", "Aqualia_GIS"]


@pytest.fixture(scope="module")
def repo() -> ExcelRepository:
    """Repositorio cargado con la fixture minima."""
    return ExcelRepository(FIXTURE)


# ---------------------------------------------------------------------------
# get_all_executions
# ---------------------------------------------------------------------------

class TestGetAllExecutions:
    def test_devuelve_dataframe_con_todas_las_filas(self, repo):
        df = repo.get_all_executions()
        assert len(df) == 6

    def test_columnas_obligatorias_presentes(self, repo):
        df = repo.get_all_executions()
        for col in ("Id", "proyecto", "nFecha_ejecucion", "xEjecutadosOK", "xError"):
            assert col in df.columns

    def test_no_modifica_datos_internos(self, repo):
        df1 = repo.get_all_executions()
        df1["proyecto"] = "MODIFICADO"
        df2 = repo.get_all_executions()
        assert "MODIFICADO" not in df2["proyecto"].values


# ---------------------------------------------------------------------------
# get_executions_by_project
# ---------------------------------------------------------------------------

class TestGetExecutionsByProject:
    def test_filtra_por_proyecto(self, repo):
        df = repo.get_executions_by_project("AqualiaDW")
        assert (df["proyecto"] == "AqualiaDW").all()

    def test_devuelve_dos_filas_para_aqualia_dw(self, repo):
        df = repo.get_executions_by_project("AqualiaDW")
        assert len(df) == 2

    def test_proyecto_inexistente_devuelve_dataframe_vacio(self, repo):
        df = repo.get_executions_by_project("ProyectoQueNoExiste")
        assert len(df) == 0


# ---------------------------------------------------------------------------
# get_last_execution_per_project
# ---------------------------------------------------------------------------

class TestGetLastExecutionPerProject:
    def test_devuelve_una_fila_por_proyecto(self, repo):
        df = repo.get_last_execution_per_project()
        assert len(df) == len(PROYECTOS)
        assert set(df["proyecto"]) == set(PROYECTOS)

    def test_selecciona_la_fecha_mas_reciente(self, repo):
        df = repo.get_last_execution_per_project()
        for _, row in df.iterrows():
            assert row["nFecha_ejecucion"] == 20240102

    def test_xejecutadosok_de_aqualia_dw_es_95(self, repo):
        df = repo.get_last_execution_per_project()
        row = df[df["proyecto"] == "AqualiaDW"].iloc[0]
        assert row["xEjecutadosOK"] == 95.0


# ---------------------------------------------------------------------------
# get_executions_in_range
# ---------------------------------------------------------------------------

class TestGetExecutionsInRange:
    def test_rango_completo_devuelve_todas_las_filas(self, repo):
        df = repo.get_executions_in_range(date(2024, 1, 1), date(2024, 1, 2))
        assert len(df) == 6

    def test_rango_un_dia(self, repo):
        df = repo.get_executions_in_range(date(2024, 1, 1), date(2024, 1, 1))
        assert len(df) == 3
        assert (df["nFecha_ejecucion"] == 20240101).all()

    def test_rango_sin_datos_devuelve_vacio(self, repo):
        df = repo.get_executions_in_range(date(2023, 1, 1), date(2023, 12, 31))
        assert len(df) == 0

    def test_rango_un_solo_dia_segundo(self, repo):
        df = repo.get_executions_in_range(date(2024, 1, 2), date(2024, 1, 2))
        assert len(df) == 3
        assert (df["nFecha_ejecucion"] == 20240102).all()


# ---------------------------------------------------------------------------
# get_available_projects
# ---------------------------------------------------------------------------

class TestGetAvailableProjects:
    def test_devuelve_lista_de_proyectos(self, repo):
        projects = repo.get_available_projects()
        assert set(projects) == set(PROYECTOS)

    def test_lista_ordenada_alfabeticamente(self, repo):
        projects = repo.get_available_projects()
        assert projects == sorted(projects)


# ---------------------------------------------------------------------------
# Errores de inicializacion
# ---------------------------------------------------------------------------

class TestInicializacion:
    def test_fichero_inexistente_lanza_filenotfounderror(self):
        with pytest.raises(FileNotFoundError):
            ExcelRepository(Path("no_existe.xlsx"))

    def test_carga_excel_real_sin_errores(self):
        real = Path(__file__).parent.parent / "data" / "PWC_Monitorizacion_CdM.xlsx"
        if real.exists():
            r = ExcelRepository(real)
            df = r.get_all_executions()
            assert len(df) > 0
            assert set(r.get_available_projects()) == {
                "AqualiaApemsa", "AqualiaDW", "AqualiaODS",
                "AqualiaSII2_Doc_AEF", "AqualiaSII2_FICO",
                "AqualiaTPL", "Aqualia_Diario", "Aqualia_GIS",
            }
