"""Vista 2 — Detalle por proyecto (se implementa en la Fase 4)."""

import streamlit as st
from src.core.data_access.base_repository import BaseRepository


def render(repo: BaseRepository) -> None:
    """Renderiza la Vista 2 — Detalle por proyecto."""
    st.title("Detalle por proyecto")
    st.info("Esta vista se implementa en la Fase 4.")
