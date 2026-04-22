"""Punto de entrada de DATA_Dashboard (Streamlit)."""

import os
import streamlit as st

from src.core.data_access.factory import get_repository
from src.ui.styles import inject_css, set_dark, apply_plotly_theme

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
# Estado de tema
# ---------------------------------------------------------------------------
if "dark" not in st.session_state:
    st.session_state.dark = False

set_dark(st.session_state.dark)
apply_plotly_theme()
inject_css()

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
        f'<p style="font-size:10px;font-family:\'JetBrains Mono\',monospace;'
        f'text-transform:uppercase;letter-spacing:0.08em;margin:4px 0 0;'
        f'color:{"#8890a8" if st.session_state.dark else "#8a909a"}">Aqualia · DATA</p>',
        unsafe_allow_html=True,
    )

    st.divider()

    vista = st.radio(
        "Navegación",
        options=["Resumen global", "Detalle por proyecto", "Operativa diaria"],
        index=0,
        label_visibility="collapsed",
    )

    st.divider()

    # Toggle de tema claro/oscuro
    col_icon, col_btn = st.columns([1, 3])
    with col_icon:
        st.markdown(
            f'<div style="font-size:20px;padding-top:4px">{"🌙" if not st.session_state.dark else "☀️"}</div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        label = "Tema oscuro" if not st.session_state.dark else "Tema claro"
        if st.button(label, use_container_width=True):
            st.session_state.dark = not st.session_state.dark
            st.rerun()

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
