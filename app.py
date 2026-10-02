import streamlit as st
import os
from pathlib import Path

# --- CONFIGURACIÓN DE PÁGINA (Ícono de pestaña personalizado) ---
FAVICON_PATH = Path(__file__).parent / "assets" / "konyu_logo.png"

st.set_page_config(
    page_title="Konyu Recetas",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "🐱",
    layout="wide"
)

# --- HELPER DE IMÁGENES KONYU ---
def mostrar_konyu(nombre_imagen, caption="", width=120):
    base_dir = Path(__file__).parent
    ruta = base_dir / "assets" / nombre_imagen
    if ruta.exists():
        st.image(str(ruta), caption=caption, width=width)
    else:
        st.caption(f"🐱 {caption}" if caption else "🐱")

# --- PANTALLA DE LOGIN ---
def render_login():
    # Imagen superior de Konyu
    mostrar_konyu("konyu_logo.png", caption="Konyu supervisando el sistema", width=130)
    
    # Título limpio (sin emoji al lado)
    st.title("Konyu Recetas")
    st.subheader("Control e Histórico de Recetas y Vales")
    
    st.markdown("### 🔒 Iniciar Sesión")
    # ... (resto de tu formulario de login)


# --- SECCIÓN SIDEBAR / ASISTENCIA ---
# Reemplazar la imagen en el sidebar para orientación:
with st.sidebar:
    # Foto de Konyu para orientar
    mostrar_konyu("konyu_ok.png", caption="Konyu te orienta", width=110)


# --- VISTA DE VALES (Perfil Sucursal) ---
# En la función/vista de Vales Pendientes agregar:
def render_vales_sucursal():
    st.title("📜 Gestión de Vales e Histórico de Cargas")
    
    # Mensaje de Konyu te acompaña
    mostrar_konyu("konyu_logo.png", caption="Konyu te acompaña", width=100)
    
    # ... (resto del código de vales)
