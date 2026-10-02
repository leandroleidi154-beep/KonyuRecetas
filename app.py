import streamlit as st
import pandas as pd
import json
import io
import os
from datetime import datetime, date
from pathlib import Path

# Librerías de ReportLab para la generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- CONFIGURACIÓN DE PÁGINA (Favicon / Ícono de pestaña con Konyu) ---
BASE_DIR = Path(__file__).parent
FAVICON_PATH = BASE_DIR / "assets" / "konyu_logo.png"

st.set_page_config(
    page_title="Konyu Recetas",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "🐱",
    layout="wide"
)

# --- HELPER DE IMÁGENES KONYU ---
def mostrar_konyu(nombre_imagen, caption="", width=120):
    ruta = BASE_DIR / "assets" / nombre_imagen
    if ruta.exists():
        st.image(str(ruta), caption=caption, width=width)
    else:
        assets_dir = BASE_DIR / "assets"
        encontrado = False
        if assets_dir.exists():
            nombre_base = Path(nombre_imagen).stem.lower()
            for archivo in assets_dir.iterdir():
                if archivo.stem.lower() == nombre_base and archivo.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']:
                    st.image(str(archivo), caption=caption, width=width)
                    encontrado = True
                    break
        if not encontrado and caption:
            st.caption(f"🐱 {caption}")

# --- ARCHIVOS DE PERSISTENCIA ---
ARCHIVO_VALES = "repositorio_vales.json"
ARCHIVO_HISTORIAL = "historial_cargas.json"

# --- USUARIOS DE PRUEBA Y AUTENTICACIÓN ---
USUARIOS = {
    "sucu01": {"clave": "sucu123", "rol": "sucursal", "nombre": "Sucursal 01 - Centro"},
    "sucu02": {"clave": "sucu123", "rol": "sucursal", "nombre": "Sucursal 02 - Norte"},
    "mutuales": {"clave": "admin123", "rol": "administrador", "nombre": "Gestión Mutuales / Admin"}
}

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "usuario" not in st.session_state:
    st.session_state.usuario = ""
if "rol" not in st.session_state:
    st.session_state.rol = ""
if "nombre_usuario" not in st.session_state:
    st.session_state.nombre_usuario = ""

# --- FUNCIONES DE PERSISTENCIA ---
def cargar_vales():
    if os.path.exists(ARCHIVO_VALES):
        try:
            with open(ARCHIVO_VALES, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_vales(vales):
    with open(ARCHIVO_VALES, "w", encoding="utf-8") as f:
        json.dump(vales, f, ensure_ascii=False, indent=4)

def cargar_historial():
    if os.path.exists(ARCHIVO_HISTORIAL):
        try:
            with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def guardar_historial(historial):
    with open(ARCHIVO_HISTORIAL, "w", encoding="utf-8") as f:
        json.dump(historial, f, ensure_ascii=False, indent=4)

# --- GENERADOR DE PDF (ReportLab) ---
def generar_pdf_cierre(lote_info, vales_lote):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36, leftMargin=36,
        topMargin=36, bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=10
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#4A5568")
    )

    story.append(Paragraph("<b>REPORTE DE CIERRE DE LOTE - VALES / RECETAS</b>", title_style))
    story.append(Paragraph(f"<b>Lote ID:</b> {lote_info.get('ID_Lote')} | <b>Fecha Envío:</b> {lote_info.get('Fecha_Envio')} | <b>Sucursal:</b> {lote_info.get('Sucursal')}", subtitle_style))
    story.append(Spacer(1, 15))

    encabezados = ["ID Vale", "Ticket", "F. Origen", "Obra Social", "Tramitación", "Motivo"]
    datos_tabla = [[Paragraph(f"<b>{h}</b>", styles['Normal']) for h in encabezados]]

    for v in vales_lote:
        fila = [
            Paragraph(str(v.get("ID_Vale", "")), styles['Normal']),
            Paragraph(str(v.get("N_Ticket", "")), styles['Normal']),
            Paragraph(str(v.get("Fecha_Origen", "")), styles['Normal']),
            Paragraph(str(v.get("Obra_Social", "")), styles['Normal']),
            Paragraph(str(v.get("TT_Tramitacion", "")), styles['Normal']),
            Paragraph(str(v.get("Motivo", "")), styles['Normal']),
        ]
        datos_tabla.append(fila)

    tabla = Table(datos_tabla, colWidths=[65, 65, 70, 110, 100, 130])
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    story.append(tabla)
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- PANTALLA DE LOGIN ---
def render_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        mostrar_konyu("konyu_logo.png", caption="Konyu supervisando el sistema", width=140)
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
                st.error("Usuario o contraseña incorrectos.")
                
        st.caption("🔒 Credenciales de prueba: `sucu01` / `sucu123` | `mutuales` / `admin123`")

# --- MENÚ LATERAL ---
def render_sidebar():
    with st.sidebar:
        mostrar_konyu("konyu_ok.png", caption="Konyu te orienta", width=110)
        st.write(f"**Usuario:** {st.session_state.nombre_usuario}")
        st.write(f"**Rol:** {st.session_state.rol.capitalize()}")
        st.write("---")
        
        if st.session_state.rol == "sucursal":
            opcion = st.radio("Menú de Navegación", ["Carga de Lote / CSV", "Gestión de Vales"])
        else:
            opcion = st.radio("Menú de Navegación", ["Panel General Admin", "Auditoría / Mutuales"])
            
        st.write("---")
        if st.button("Cerrar Sesión", use_container_width=True):
            st.session_state.autenticado = False
            st.rerun()
        return opcion

# --- VISTA 1: CARGA DE LOTE / CSV (Pestaña original devuelta) ---
def render_carga_lote():
    st.title("📥 Carga de Vales y Recetas (CSV)")
    
    col_info, col_img = st.columns([3, 1])
    with col_info:
        st.caption(f"**Sucursal activa:** {st.session_state.nombre_usuario}")
    with col_img:
        mostrar_konyu("konyu_logo.png", caption="Konyu te acompaña", width=90)
        
    st.write("---")
    
    archivo_subido = st.file_uploader("Selecciona el archivo CSV exportado del sistema de recetas", type=["csv"])
    
    if archivo_subido is not None:
        try:
            df = pd.read_csv(archivo_subido, sep=None, engine='python')
            st.success("Archivo leído con éxito. Vista previa de los registros:")
            st.dataframe(df.head(10), use_container_width=True)
            
            if st.button("Procesar y Guardar Vales", type="primary"):
                vales_existentes = cargar_vales()
                nuevos_vales = []
                
                for idx, row in df.iterrows():
                    vales_existentes.append({
                        "ID_Vale": f"VALE-{datetime.now().strftime('%Y%m%d%H%M%S')}-{idx}",
                        "Sucursal": st.session_state.nombre_usuario,
                        "Fecha_Origen": str(row.get("Fecha", date.today())),
                        "N_Ticket": str(row.get("Ticket", row.get("N_Ticket", "S/N"))),
                        "Obra_Social": str(row.get("Obra Social", row.get("Obra_Social", "General"))),
                        "TT_Tramitacion": str(row.get("Tramite", row.get("TT_Tramitacion", "Presencial"))),
                        "Motivo": str(row.get("Motivo", "Carga Estándar")),
                        "Estado": "Pendiente",
                        "Observacion": str(row.get("Observacion", ""))
                    })
                
                guardar_vales(vales_existentes)
                st.balloons()
                st.success(f"¡Se procesaron y guardaron {len(df)} vales correctamente!")
        except Exception as e:
            mostrar_konyu("konyu_warning.png", caption="Atención con el archivo", width=90)
            st.error(f"Error al leer el archivo CSV: {e}")

# --- VISTA 2: GESTIÓN DE VALES (Vista completa) ---
def render_vales_sucursal():
    st.title("📜 Gestión de Vales e Histórico de Cargas")
    
    col_info, col_img = st.columns([3, 1])
    with col_info:
        st.caption(f"**Sucursal activa:** {st.session_state.nombre_usuario}")
    with col_img:
        mostrar_konyu("konyu_logo.png", caption="Konyu te acompaña", width=90)
        
    st.write("---")
    
    vales_totales = cargar_vales()
    vales_sucu = [v for v in vales_totales if v.get("Sucursal") == st.session_state.nombre_usuario]
    
    tab1, tab2, tab3 = st.tabs([
        "📦 Vales Pendientes (Enviar / Anular)", 
        "✅ Histórico de Vales Enviados y Resueltos", 
        "📋 Histórico de Lotes y Descarga PDF"
    ])
    
    with tab1:
        st.markdown("#### 1. Vales Pendientes de Envío")
        pendientes = [v for v in vales_sucu if v.get("Estado") == "Pendiente"]
        
        if not pendientes:
            st.info("No hay vales pendientes de envío para esta sucursal.")
            mostrar_konyu("konyu_empty.png", caption="Sin registros pendientes", width=110)
        else:
            df_pend = pd.DataFrame(pendientes)
            st.dataframe(df_pend[["ID_Vale", "N_Ticket", "Fecha_Origen", "Obra_Social", "Motivo"]], use_container_width=True)
            
            if st.button("Enviar Lote a Mutuales / Admin", type="primary"):
                id_lote = f"LOTE-{datetime.now().strftime('%Y%m%d%H%M')}"
                for v in vales_totales:
                    if v.get("Sucursal") == st.session_state.nombre_usuario and v.get("Estado") == "Pendiente":
                        v["Estado"] = "Enviado"
                        v["ID_Lote"] = id_lote
                
                guardar_vales(vales_totales)
                
                historial = cargar_historial()
                historial.append({
                    "ID_Lote": id_lote,
                    "Sucursal": st.session_state.nombre_usuario,
                    "Fecha_Envio": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Cantidad_Vales": len(pendientes)
                })
                guardar_historial(historial)
                st.success(f"¡Lote {id_lote} enviado con éxito!")
                st.rerun()

    with tab2:
        st.markdown("#### Histórico de Vales Enviados")
        enviados = [v for v in vales_sucu if v.get("Estado") != "Pendiente"]
        if not enviados:
            st.info("Aún no hay vales enviados.")
            mostrar_konyu("konyu_empty.png", caption="Sin historial de envíos", width=110)
        else:
            st.dataframe(pd.DataFrame(enviados), use_container_width=True)

    with tab3:
        st.markdown("#### Lotes Enviados y Descarga de PDF")
        historial = cargar_historial()
        historial_sucu = [h for h in historial if h.get("Sucursal") == st.session_state.nombre_usuario]
        
        if not historial_sucu:
            st.info("No hay lotes generados.")
            mostrar_konyu("konyu_empty.png", caption="Sin lotes registrados", width=110)
        else:
            for lote in historial_sucu:
                with st.expander(f"📦 Lote {lote['ID_Lote']} - {lote['Fecha_Envio']} ({lote['Cantidad_Vales']} vales)"):
                    vales_lote = [v for v in vales_totales if v.get("ID_Lote") == lote["ID_Lote"]]
                    pdf_bytes = generar_pdf_cierre(lote, vales_lote)
                    
                    st.download_button(
                        label="📄 Descargar Comprobante PDF",
                        data=pdf_bytes,
                        file_name=f"Cierre_Lote_{lote['ID_Lote']}.pdf",
                        mime="application/pdf"
                    )

# --- VISTA ADMIN ---
def render_admin():
    st.title("Panel de Administración General y Auditoría")
    mostrar_konyu("konyu_ok.png", caption="Konyu supervisa la gestión central", width=120)
    st.write("---")
    
    vales = cargar_vales()
    if not vales:
        st.info("No hay vales registrados en el sistema.")
        mostrar_konyu("konyu_empty.png", caption="Base de datos vacía", width=110)
    else:
        st.dataframe(pd.DataFrame(vales), use_container_width=True)

# --- FLUJO PRINCIPAL ---
def main():
    if not st.session_state.autenticado:
        render_login()
    else:
        opcion_menu = render_sidebar()
        
        if st.session_state.rol == "sucursal":
            if opcion_menu == "Carga de Lote / CSV":
                render_carga_lote()
            else:
                render_vales_sucursal()
        else:
            render_admin()

if __name__ == "__main__":
    main()
