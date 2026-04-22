"""Punto de entrada de DATA_Dashboard (Streamlit)."""

import os
import streamlit as st

from src.core.data_access.factory import get_repository
from src.ui.styles import inject_css, apply_plotly_theme

# ---------------------------------------------------------------------------
# Configuracion de pagina (primera llamada a Streamlit)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="DATA Dashboard — Aqualia",
    page_icon=":bar_chart:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Tema (claro / oscuro)
# ---------------------------------------------------------------------------
dark = st.session_state.get("dark", False)
apply_plotly_theme(dark)
inject_css(dark)

# ---------------------------------------------------------------------------
# Repositorio de datos
# ---------------------------------------------------------------------------
@st.cache_resource
def load_repository():
    return get_repository()

repo = load_repository()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "aqualia-logo.png")
    if os.path.exists(logo_path):
        st.image(logo_path, width=140)
    else:
        st.markdown("**DATA Dashboard**")

    st.markdown(
        '<p style="font-size:10px;font-family:\'JetBrains Mono\',monospace;'
        'text-transform:uppercase;letter-spacing:0.08em;margin:4px 0 12px;'
        'color:var(--dd-text3)">Aqualia · DATA</p>',
        unsafe_allow_html=True,
    )

    new_dark = st.toggle("Tema oscuro", value=dark)
    if new_dark != dark:
        st.session_state.dark = new_dark
        st.rerun()

    st.divider()

    vista = st.radio(
        "Navegación",
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
