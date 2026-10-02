import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA (Favicon / Ícono de pestaña) ---
BASE_DIR = Path(__file__).parent
FAVICON_PATH = BASE_DIR / "assets" / "konyu_logo.png"

st.set_page_config(
    page_title="Konyu Recetas",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "🐱",
    layout="wide"
)

# --- HELPER MEJORADO DE IMÁGENES KONYU ---
def mostrar_konyu(nombre_imagen, caption="", width=120):
    """Muestra imágenes de Konyu con fallback seguro si el archivo no se encuentra."""
    ruta = BASE_DIR / "assets" / nombre_imagen
    if ruta.exists():
        st.image(str(ruta), caption=caption, width=width)
    else:
        # Búsqueda insensible a mayúsculas/minúsculas
        assets_dir = BASE_DIR / "assets"
        encontrado = False
        if assets_dir.exists():
            nombre_base = Path(nombre_imagen).stem.lower()
            for archivo in assets_dir.iterdir():
                if archivo.stem.lower() == nombre_base and archivo.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                    st.image(str(archivo), caption=caption, width=width)
                    encontrado = True
                    break
        
        if not encontrado:
            st.caption(f"🐱 {caption}" if caption else "🐱")

# --- ESTADOS DE SESIÓN (SESSION STATE) ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""

# --- BASE DE DATOS DE USUARIOS (Simulación temporal) ---
USUARIOS = {
    "sucu01": {"clave": "sucu123", "rol": "sucursal", "nombre": "Sucursal 01 - Centro"},
    "mutuales": {"clave": "admin123", "rol": "administrador", "nombre": "Gestión Mutuales"}
}

# --- PANTALLA DE LOGIN ---
def render_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Imagen superior de Konyu
        mostrar_konyu("konyu_logo.png", caption="Konyu supervisando el sistema", width=140)
        
        # Título limpio (sin emoji al lado del texto)
        st.title("Konyu Recetas")
        st.markdown("##### Control e Histórico de Recetas y Vales")
        st.write("---")
        
        st.markdown("### 🔒 Iniciar Sesión")
        
        usuario_input = st.text_input("Usuario", placeholder="Ej: sucu01 o mutuales")
        clave_input = st.text_input("Contraseña", type="password")
        
        if st.button("Ingresar al Sistema", use_container_width=True):
            if usuario_input in USUARIOS and USUARIOS[usuario_input]["clave"] == clave_input:
                st.session_state.autenticado = True
                st.session_state.usuario = usuario_input
                st.session_state.rol = USUARIOS[usuario_input]["rol"]
                st.session_state.nombre_usuario = USUARIOS[usuario_input]["nombre"]
                st.rerun()
            else:
                mostrar_konyu("konyu_warning.png", caption="", width=80)
                st.error("Usuario o contraseña incorrectos. Por favor, reintenta.")
                
        st.caption("🔒 Credenciales de prueba: `sucu01` / `sucu123` | `mutuales` / `admin123`")

# --- NAVEGACIÓN Y MENÚ LATERAL ---
def render_sidebar():
    with st.sidebar:
        # Imagen de orientación en el menú
        mostrar_konyu("konyu_ok.png", caption="Konyu te orienta", width=110)
        
        st.write(f"**Usuario:** {st.session_state.nombre_usuario}")
        st.write(f"**Rol:** {st.session_state.rol.capitalize()}")
        st.write("---")
        
        if st.session_state.rol == "sucursal":
            opcion = st.radio("Menú de Navegación", ["Gestión de Vales", "Histórico de Envíos"])
        else:
            opcion = st.radio("Menú de Navegación", ["Panel General", "Validación Mutuales", "Gestión de Usuarios"])
            
        st.write("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
            
        return opcion

# --- VISTA: GESTIÓN DE VALES (Perfil Sucursal) ---
def render_vales_sucursal():
    st.title("Gestión de Vales e Histórico de Cargas")
    
    col_info, col_img = st.columns([3, 1])
    with col_info:
        st.caption(f"**Sucursal activa:** {st.session_state.nombre_usuario}")
    with col_img:
        # Konyu te acompaña en esta vista
        mostrar_konyu("konyu_logo.png", caption="Konyu te acompaña", width=90)
        
    st.write("---")
    
    tab1, tab2, tab3 = st.tabs([
        "📦 Vales Pendientes (Enviar / Anular)", 
        "✅ Histórico de Vales Enviados y Resueltos", 
        "📋 Histórico de Lotes y Descarga PDF"
    ])
    
    with tab1:
        st.markdown("#### 1. Vales Pendientes por Fecha de Origen")
        c1, c2 = st.columns(2)
        with c1:
            fecha_sel = st.date_input("📅 Fecha de Origen de la Receta / Vale", datetime.now())
        with c2:
            busq_libre = st.text_input("🔍 Buscar por Ticket, T.T u Obra Social", placeholder="Escribí número de ticket...")
            
        # Ejemplo de tabla sin datos para activar el estado vacío
        vales_ejemplo = [] 
        
        if not vales_ejemplo:
            st.info("No hay vales pendientes de envío para los filtros seleccionados.")
            mostrar_konyu("konyu_empty.png", caption="Sin registros pendientes", width=100)

    with tab2:
        st.markdown("#### Histórico de Vales Enviados")
        st.write("Acá podrás consultar las entregas confirmadas.")

    with tab3:
        st.markdown("#### Lotes y Comprobantes")
        st.write("Descarga de reportes en PDF generados con ReportLab.")

# --- VISTA: PANEL DE ADMINISTRACIÓN / MUTUALES ---
def render_admin_panel():
    st.title("Panel de Control General")
    st.write("Bienvenido al módulo de administración central.")
    mostrar_konyu("konyu_ok.png", caption="Sistema supervisado por Konyu", width=120)

# --- FLUJO PRINCIPAL DE LA APLICACIÓN ---
def main():
    if not st.session_state.autenticado:
        render_login()
    else:
        opcion_menu = render_sidebar()
        
        if st.session_state.rol == "sucursal":
            render_vales_sucursal()
        else:
            render_admin_panel()

if __name__ == "__main__":
    main()
