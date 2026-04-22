"""Punto de entrada de DATA_Dashboard (Streamlit).

Configura la pagina, carga el repositorio y enruta a la vista seleccionada.
"""

import streamlit as st

from src.core.data_access.factory import get_repository

# ---------------------------------------------------------------------------
# Configuracion de pagina (debe ser la primera llamada a Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DATA Dashboard — Aqualia",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Carga del repositorio (cacheada para no releer el Excel en cada interaccion)
# ---------------------------------------------------------------------------
@st.cache_resource
def load_repository():
    """Carga y devuelve el repositorio de datos (singleton por sesion)."""
    return get_repository()


repo = load_repository()

# ---------------------------------------------------------------------------
# Navegacion lateral
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("DATA Dashboard")
    st.caption("Departamento de DATA — Aqualia TI")
    st.divider()

    vista = st.radio(
        "Navegacion",
        options=["Resumen global", "Detalle por proyecto", "Operativa diaria"],
        index=0,
        label_visibility="collapsed",
    )

    st.divider()
    st.caption("Fuente: PWC_Monitorizacion_CdM")

# ---------------------------------------------------------------------------
# Enrutamiento
# ---------------------------------------------------------------------------
if vista == "Resumen global":
    from src.ui.views.overview import render
    render(repo)

elif vista == "Detalle por proyecto":
    from src.ui.views.project_detail import render
    render(repo)

else:
    from src.ui.views.daily_ops import render
    render(repo)
