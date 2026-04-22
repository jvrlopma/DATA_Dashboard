"""Punto de entrada de DATA_Dashboard (Streamlit).

Configura la pagina, carga el repositorio y enruta a la vista seleccionada.
"""

import streamlit as st

from src.core.data_access.factory import get_repository
from src.ui.styles import inject_css

# ---------------------------------------------------------------------------
# Configuracion de pagina (debe ser la primera llamada a Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DATA Dashboard — Aqualia",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

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
import os

with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "aqualia-logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=140)
    else:
        st.markdown("**DATA Dashboard**")
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
