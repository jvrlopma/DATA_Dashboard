"""Vista 3 — Operativa diaria (se implementa en la Fase 5)."""

import streamlit as st
from src.core.data_access.base_repository import BaseRepository


def render(repo: BaseRepository) -> None:
    """Renderiza la Vista 3 — Operativa diaria."""
    st.title("Operativa diaria")
    st.info("Esta vista se implementa en la Fase 5.")
