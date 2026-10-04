import datetime
import io
import json
import os
import re
import pandas as pd
import streamlit as st
from supabase import create_client, Client

# --- INICIALIZACIÓN SEGURA DE SUPABASE ---
supabase: Client = None

try:
    if "supabase" in st.secrets and "SUPABASE_URL" in st.secrets["supabase"]:
        url: str = st.secrets["supabase"]["SUPABASE_URL"]
        key: str = st.secrets["supabase"]["SUPABASE_KEY"]
        supabase = create_client(url, key)
    else:
        st.error("⚠️ Falta la sección [supabase] en Streamlit Secrets.")
except Exception as e:
    st.error(f"⚠️ Error al conectar con Supabase: {e}")

# Importaciones para ReportLab (PDF)
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from pathlib import Path

# Obtenemos la ruta de la imagen
FAVICON_PATH = Path(__file__).parent / "assets" / "konyu_logo.png"

st.set_page_config(
    page_title="Konyu Recetas",
    page_icon=str(FAVICON_PATH) if FAVICON_PATH.exists() else "🐱",
    layout="wide",
)

# Estilos CSS con paleta personalizada
st.markdown(
    """
    <style>
        .stApp { background-color: #0B0F17; color: #E2E8F0; }
        [data-testid="stSidebar"] { background-color: #111827; border-right: 1px solid #1E293B; }
        .stMetric { background-color: #161D2A; padding: 15px; border-radius: 12px; border: 1px solid #1E293B; }
    </style>
""",
    unsafe_allow_html=True,
)


# Helper para cargar imágenes de Konyu con fallback de emoji
def mostrar_konyu(nombre_imagen, caption="", width=120):
    ruta = os.path.join("assets", nombre_imagen)
    if os.path.exists(ruta):
        st.image(ruta, caption=caption, width=width)
    else:
        st.caption(f"🐱 {caption}" if caption else "🐱")


# Archivos de persistencia
ARCHIVO_VALES = "repositorio_vales.json"
ARCHIVO_CARGAS = "historial_cargas.json"

COLUMNAS_VALES = [
    "ID_Vale",
    "ID_Lote",
    "Sucursal",
    "Fecha_Origen",
    "Obra_Social",
    "Plan",
    "N_Ticket",
    "TT_Tramitacion",
    "Motivo",
    "Estado",
    "Fecha_Resolucion",
    "Observacion",
]

COLUMNAS_CARGAS = [
    "ID_Lote",
    "Sucursal",
    "Fecha_Carga",
    "Total_Recetas",
    "Fisico_Enviado",
    "Vales_Generados",
    "Estado_Lote",
    "Desglose_Obra_Social",
    "Detalle_Recetas_Fisicas",
]

USUARIOS_BASE = {
    "admin": {"pass": "admin123", "nombre": "Administración Central", "rol": "Mutuales"}
}


# --- PERSISTENCIA DE USUARIOS (SUPABASE) ---
def cargar_usuarios():
    """Lee todos los usuarios desde la tabla 'usuarios' en Supabase."""
    try:
        response = supabase.table("usuarios").select("*").execute()
        usuarios_dict = {}
        for user in response.data:
            usuarios_dict[user["username"]] = {
                "nombre": user["nombre"],
                "pass": user["pass"],
                "rol": user["rol"],
            }
        return usuarios_dict if usuarios_dict else USUARIOS_BASE
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return USUARIOS_BASE


def guardar_usuarios_dict(dict_usr):
    """Guarda/actualiza los usuarios directamente en Supabase."""
    try:
        datos = []
        for username, data in dict_usr.items():
            datos.append(
                {
                    "username": username,
                    "nombre": data["nombre"],
                    "pass": data["pass"],
                    "rol": data["rol"],
                }
            )
        supabase.table("usuarios").upsert(datos).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar en la base de datos: {e}")
        return False


# --- PEGAR ACÁ (ENTRE LÍNEA 93 Y 94) ---
def render_gestion_usuarios():
    st.title("👤 Gestión y Alta de Usuarios")
    st.caption("Panel exclusivo para crear y administrar accesos")
    st.write("---")

    usuarios_actuales = cargar_usuarios()

    col_crear, col_lista = st.columns([1, 1])

    with col_crear:
        st.subheader("➕ Crear Nuevo Usuario")
        nuevo_user = (
            st.text_input("Usuario (Login)", placeholder="Ej: sucu01").strip().lower()
        )
        nuevo_nombre = st.text_input(
            "Nombre visible / Sucursal", placeholder="Ej: Sucursal 01 - Centro"
        )
        nueva_clave = st.text_input("Contraseña", type="password")
        nuevo_rol = st.selectbox("Rol", ["Sucursal", "Mutuales"])

        if st.button("Guardar Usuario", type="primary"):
            if not nuevo_user or not nuevo_nombre or not nueva_clave:
                st.error("Completá todos los campos antes de guardar.")
            elif nuevo_user in usuarios_actuales:
                st.warning("Ese usuario ya existe. Elegí otro nombre de login.")
            else:
                usuarios_actuales[nuevo_user] = {
                    "pass": nueva_clave,
                    "nombre": nuevo_nombre,
                    "rol": nuevo_rol,
                }
                guardar_usuarios_dict(usuarios_actuales)
                st.success(f"¡Usuario '{nuevo_nombre}' creado con éxito!")
                st.rerun()

    with col_lista:
        st.subheader("📋 Usuarios Registrados")
        lista_tabla = []
        for u, datos in usuarios_actuales.items():
            lista_tabla.append(
                {
                    "Usuario": u,
                    "Nombre / Sucursal": datos["nombre"],
                    "Rol": datos["rol"],
                }
            )
        st.dataframe(lista_tabla, use_container_width=True)


# LUEGO SIGUE TU CÓDIGO EXISTENTE DE LA LÍNEA 94 EN ADELANTE:
def cargar_json(filepath, columnas):
    if os.path.exists(filepath):
        ...


def cargar_json(filepath, columnas):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return pd.DataFrame(columns=columnas)
                data = json.loads(content)
                df = pd.DataFrame(data)
                for col in columnas:
                    if col not in df.columns:
                        if col == "Estado_Lote":
                            df[col] = "PENDIENTE"
                        elif col in ["Desglose_Obra_Social", "Detalle_Recetas_Fisicas"]:
                            df[col] = "[]" if col == "Detalle_Recetas_Fisicas" else "{}"
                        else:
                            df[col] = "-"
                return df[columnas]
        except Exception:
            return pd.DataFrame(columns=columnas)
    else:
        df_vacio = pd.DataFrame(columns=columnas)
        guardar_json(df_vacio, filepath)
        return df_vacio


def guardar_json(df, filepath):
    try:
        data = df.to_dict(orient="records")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Error al guardar datos: {e}")


# Manejo de Sesión
if "usr_actual" not in st.session_state:
    st.session_state["usr_actual"] = None

if "tickets_tildados" not in st.session_state:
    st.session_state.tickets_tildados = set()

# 2. Pantalla de Inicio de Sesión
if st.session_state["usr_actual"] is None:
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        mostrar_konyu(
            "konyu_logo.png", caption="Konyu supervisando el sistema", width=130
        )
        st.markdown(
            "<h2 style='text-align: center; margin-bottom: 0px;'>Konyu Recetas</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align: center; color: gray; font-size: 0.9rem;'>Control e Histórico de Recetas y Vales</p>",
            unsafe_allow_html=True,
        )

        st.markdown("##### 🔒 Iniciar Sesión")
        user_input = st.text_input("Usuario", placeholder="Ej: sucu01 o mutuales")
        pass_input = st.text_input(
            "Contraseña", type="password", placeholder="••••••••"
        )

        if st.button("Ingresar al Sistema", type="primary", use_container_width=True):
            usuarios_actuales = cargar_usuarios()
            if (
                user_input in usuarios_actuales
                and usuarios_actuales[user_input]["pass"] == pass_input
            ):
                usr_data = usuarios_actuales[user_input]
                st.session_state["usr_actual"] = {
                    "username": user_input,
                    "nombre": usr_data["nombre"],
                    "rol": usr_data["rol"],
                }
                st.success(f"¡Bienvenido, {usr_data['nombre']}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

        st.caption(
            "🔒 Credenciales de prueba: `sucu01` / `sucu123` | `mutuales` / `admin123` "
        )

        st.stop()  # <-- Este st.stop() DEBE ir con 4 espacios (fuera de col_logo2 pero DENTRO del if principal)


# 3. Procesador de CSV Zweb
def procesar_csv(file):
    recetas = []
    obra_social_actual = "GENERAL"
    patron_ticket = re.compile(r"(\d{4}-\d{8})")
    lines = file.getvalue().decode("latin1").splitlines()

    for line in lines:
        columnas = [p.strip() for p in line.split(";") if p.strip()]

        if columnas:
            val = columnas[0]
            if not (val.startswith("A") and len(val) == 5 and val[1:].isdigit()):
                if val not in [
                    "T&S Web",
                    "Nodo:",
                    "Desde:",
                    "Recetas:",
                    "Plan",
                    "Mandataria:",
                ] and not (
                    val.startswith("$")
                    or val.startswith("Reporte")
                    or "Oculta OL:" in val
                    or "septiembre" in val
                ):
                    if not patron_ticket.search(line):
                        obra_social_actual = val.rstrip("!").strip()

        tickets = patron_ticket.findall(line)
        if len(tickets) >= 2:
            ticket_nro = tickets[0]
            tt_nro = tickets[1]
            partes_csv = [p.strip() for p in line.split(";")]
            plan = partes_csv[0] if partes_csv[0] else "GENERAL"

            recetas.append(
                {
                    "Obra Social": obra_social_actual,
                    "Plan": plan,
                    "N° Ticket": ticket_nro,
                    "T.T (Tramitación)": tt_nro,
                }
            )

    return pd.DataFrame(recetas)


def preparar_df_resumen(desglose_data):
    if isinstance(desglose_data, str):
        try:
            desglose_data = json.loads(desglose_data)
        except Exception:
            desglose_data = {}
    if isinstance(desglose_data, dict) and desglose_data:
        filas = [
            {"Obra Social": os, "Físico Esperado": cant}
            for os, cant in desglose_data.items()
        ]
        return pd.DataFrame(filas)
    elif isinstance(desglose_data, pd.DataFrame):
        return desglose_data
    return pd.DataFrame(columns=["Obra Social", "Físico Esperado"])


def preparar_df_recetas_fisicas(detalle_data):
    if isinstance(detalle_data, str):
        try:
            detalle_data = json.loads(detalle_data)
        except Exception:
            detalle_data = []
    if isinstance(detalle_data, list) and detalle_data:
        return pd.DataFrame(detalle_data)
    elif isinstance(detalle_data, pd.DataFrame):
        return detalle_data
    return pd.DataFrame(
        columns=["Obra Social", "Plan", "N° Ticket", "T.T (Tramitación)"]
    )


# 4. Generación de PDF ReportLab
def generar_pdf_cierre(
    df_resumen, df_recetas_fisicas, df_vales_generados, sucursal_nombre, fecha_lote
):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    story = []
    styles = getSampleStyleSheet()

    titulo_style = ParagraphStyle(
        "TituloPDF",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1E293B"),
        fontName="Helvetica-Bold",
    )
    subtitulo_style = ParagraphStyle(
        "SubtituloPDF",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
    )
    section_style = ParagraphStyle(
        "SectionPDF",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#0F172A"),
        fontName="Helvetica-Bold",
        spaceBefore=10,
        spaceAfter=5,
    )
    cell_style = ParagraphStyle(
        "CellPDF",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#334155"),
    )
    header_cell_style = ParagraphStyle(
        "HeaderCellPDF",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    story.append(
        Paragraph("<b>Konyu Recetas</b> - Planilla de Cierre de Lote", titulo_style)
    )
    story.append(
        Paragraph(
            f"<b>Sucursal:</b> {sucursal_nombre} | <b>Fecha Lote:</b> {fecha_lote}",
            subtitulo_style,
        )
    )
    story.append(Spacer(1, 10))
    story.append(
        HRFlowable(
            width="100%", thickness=1, color=colors.HexColor("#CBD5E1"), spaceAfter=15
        )
    )

    # 1. Resumen Agrupado
    story.append(
        Paragraph(
            "1. Resumen de Recetas Físicas a Enviar por Obra Social", section_style
        )
    )
    data_resumen = [
        [
            Paragraph("Obra Social", header_cell_style),
            Paragraph("Físico Esperado", header_cell_style),
        ]
    ]

    if not df_resumen.empty:
        col_conteo = (
            "Físico Esperado"
            if "Físico Esperado" in df_resumen.columns
            else df_resumen.columns[1]
        )
        for _, row in df_resumen.iterrows():
            data_resumen.append(
                [
                    Paragraph(str(row["Obra Social"]), cell_style),
                    Paragraph(str(row[col_conteo]), cell_style),
                ]
            )

        total_sum = df_resumen[col_conteo].sum()
        data_resumen.append(
            [
                Paragraph("<b>TOTAL FÍSICO A ENVIAR</b>", cell_style),
                Paragraph(f"<b>{total_sum}</b>", cell_style),
            ]
        )
    else:
        data_resumen.append(
            [
                Paragraph("Sin recetas físicas registradas", cell_style),
                Paragraph("0", cell_style),
            ]
        )

    tabla_resumen = Table(data_resumen, colWidths=[380, 160])
    tabla_resumen.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#F1F5F9")),
            ]
        )
    )
    story.append(tabla_resumen)
    story.append(Spacer(1, 15))

    # 2. Detalle de Recetas Físicas
    story.append(
        Paragraph("2. Detalle Individual de Recetas Físicas Enviadas", section_style)
    )
    if df_recetas_fisicas.empty:
        story.append(
            Paragraph("No hay detalle de recetas físicas registradas.", cell_style)
        )
    else:
        data_fisicas = [
            [
                Paragraph("Obra Social", header_cell_style),
                Paragraph("Plan", header_cell_style),
                Paragraph("N° Ticket", header_cell_style),
                Paragraph("T.T (Tramitación)", header_cell_style),
            ]
        ]
        for _, rf in df_recetas_fisicas.iterrows():
            data_fisicas.append(
                [
                    Paragraph(
                        str(rf.get("Obra Social", rf.get("Obra_Social", "-"))),
                        cell_style,
                    ),
                    Paragraph(str(rf.get("Plan", "-")), cell_style),
                    Paragraph(
                        str(rf.get("N° Ticket", rf.get("N_Ticket", "-"))), cell_style
                    ),
                    Paragraph(
                        str(rf.get("T.T (Tramitación)", rf.get("TT_Tramitacion", "-"))),
                        cell_style,
                    ),
                ]
            )

        tabla_fisicas = Table(data_fisicas, colWidths=[180, 120, 120, 120])
        tabla_fisicas.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#334155")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ]
            )
        )
        story.append(tabla_fisicas)

    story.append(Spacer(1, 15))

    # 3. Detalle de Vales
    story.append(Paragraph("3. Detalle de Vales Generados", section_style))
    if df_vales_generados.empty:
        story.append(Paragraph("No se registraron vales para este lote.", cell_style))
    else:
        data_vales = [
            [
                Paragraph("ID Vale", header_cell_style),
                Paragraph("Obra Social", header_cell_style),
                Paragraph("N° Ticket", header_cell_style),
                Paragraph("T.T", header_cell_style),
                Paragraph("Motivo", header_cell_style),
            ]
        ]
        for _, v in df_vales_generados.iterrows():
            data_vales.append(
                [
                    Paragraph(str(v["ID_Vale"]), cell_style),
                    Paragraph(str(v["Obra_Social"]), cell_style),
                    Paragraph(str(v["N_Ticket"]), cell_style),
                    Paragraph(str(v["TT_Tramitacion"]), cell_style),
                    Paragraph(str(v["Motivo"]), cell_style),
                ]
            )

        tabla_vales = Table(data_vales, colWidths=[70, 150, 100, 100, 120])
        tabla_vales.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ]
            )
        )
        story.append(tabla_vales)

    story.append(Spacer(1, 30))
    data_firmas = [
        [
            Paragraph(
                "__________________________________<br/>Firma Responsable Sucursal",
                cell_style,
            ),
            Paragraph(
                "__________________________________<br/>Firma / Recepción Mutuales",
                cell_style,
            ),
        ]
    ]
    tabla_firmas = Table(data_firmas, colWidths=[270, 270])
    tabla_firmas.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    story.append(tabla_firmas)

    doc.build(story)
    buffer.seek(0)
    return buffer


# 5. Menú Lateral
with st.sidebar:
    mostrar_konyu("konyu_logo.png", caption="Konyu Recetas", width=90)
    st.title("🐱 Konyu Recetas")

    usr_actual = st.session_state.get("usr_actual", {})
    st.caption(f"👤 {usr_actual.get('nombre', 'Usuario')}")
    st.caption(f"Rol: {usr_actual.get('rol', '-')}")

    if st.button("🚪 Cerrar Sesión"):
        st.session_state["usr_actual"] = None
        st.rerun()

    st.divider()

    if usr_actual["rol"] == "Sucursal":
        menu = st.radio(
            "Navegación Sucursal",
            ["📥 Carga Diaria de Lote", "📜 Gestión de Vales e Histórico"],
        )
    else:
        menu = st.radio(
            "Navegación Mutuales",
            [
                "🕹️ Recepción de Lotes por Sucursal",
                "📜 Auditoría Global de Vales",
                "👤 Gestión de Usuarios",
            ],
        )


# 6. SUCURSAL - Carga Diaria
if usr_actual["rol"] == "Sucursal" and "Carga Diaria de Lote" in menu:
    col_titulo, col_konyu = st.columns([3, 1])

    with col_titulo:
        st.title("🕹️ Carga Diaria y Generación de Lote")
        st.write(f"Sucursal activa: **{usr_actual['nombre']}**")

    with col_konyu:
        ruta_acompana = os.path.join(
            os.path.dirname(__file__), "assets", "konyu_acompana.png"
        )
        if os.path.exists(ruta_acompana):
            st.image(ruta_acompana, caption="Konyu te acompaña", width=110)
        else:
            st.caption("🐱 Konyu te acompaña")

    c_f1, c_f2 = st.columns([2, 2])
    fecha_carga = c_f1.date_input(
        "Fecha de Carga del Lote", value=datetime.date.today()
    )
    archivo_csv = c_f2.file_uploader("Cargar CSV de Zweb", type=["csv"])

# Definición por defecto para evitar NameError
if "fecha_carga" not in locals():
    fecha_carga = datetime.date.today()

usuario_nombre = (
    usr_actual.get("username") or usr_actual.get("nombre", "SUCURSAL")
    if "usr_actual" in locals()
    else "SUCURSAL"
)
id_lote_actual = f"LOTE-{str(usuario_nombre).upper()}-{fecha_carga.strftime('%Y%m%d')}"

# Consulta a Supabase para traer la lista de cargas
res_cargas = supabase.table("cargas").select("*").execute()
df_cargas = pd.DataFrame(res_cargas.data) if res_cargas.data else pd.DataFrame()

# Buscar si existe el lote actual
if not df_cargas.empty and "id_lote" in df_cargas.columns:
    lote_cerrado = df_cargas[df_cargas["id_lote"] == id_lote_actual]
else:
    lote_cerrado = pd.DataFrame()

if not lote_cerrado.empty:
    lote_row = lote_cerrado.iloc[0]
    estado_lote_s = lote_row.get("estado_lote", "PENDIENTE")
    st.success(
        f"🔒 El Lote para la fecha **{fecha_carga}** (`{id_lote_actual}`) se encuentra **CERRADO Y PROCESADO**. Estado: **{estado_lote_s}**."
    )

    c_i1, c_i2, c_i3 = st.columns(3)
    c_i1.metric("Total Recetas Zweb", lote_row.get("total_recetas", 0))
    c_i2.metric("Físico Enviado", lote_row.get("fisico_enviado", 0))
    c_i3.metric("Vales Registrados", lote_row.get("vales_generados", 0))

    st.divider()
    df_vales_repo = cargar_json(ARCHIVO_VALES, COLUMNAS_VALES)
    vales_del_lote = (
        df_vales_repo[df_vales_repo["ID_Lote"] == id_lote_actual]
        if not df_vales_repo.empty
        else pd.DataFrame()
    )

    df_resumen_lote = preparar_df_resumen(lote_row.get("desglose_obra_social", "{}"))
    df_recetas_fisicas_lote = preparar_df_recetas_fisicas(
        lote_row.get("detalle_recetas_fisicas", "[]")
    )

    col_pdf, col_del = st.columns([3, 2])

    with col_pdf:
        pdf_bytes = generar_pdf_cierre(
            df_resumen_lote,
            df_recetas_fisicas_lote,
            vales_del_lote,
            usr_actual["nombre"],
            str(fecha_carga),
        )
        st.download_button(
            "📄 Descargar Planilla PDF de Cierre de este Lote",
            data=pdf_bytes,
            file_name=f"Cierre_{usr_actual['username']}_{fecha_carga}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

    with col_del:
        if st.button(
            "🗑 Cancelar / Eliminar Lote", type="secondary", use_container_width=True
        ):
            supabase.table("cargas").delete().eq("id_lote", id_lote_actual).execute()
            st.warning(
                f"Lote `{id_lote_actual}` fue cancelado/eliminado correctamente."
            )
            st.rerun()
# Le decimos a Streamlit que si el lote ya estaba cerrado, TERMINE ACÁ
if not lote_cerrado.empty:
    st.info(f"🔒 El lote `{id_lote_actual}` ya fue cerrado y procesado.")
    st.stop()

    if archivo_csv is not None:
        df_recetas = procesar_csv(archivo_csv)

        if not df_recetas.empty:
            df_vales_repo = cargar_json(ARCHIVO_VALES, COLUMNAS_VALES)
            df_vales_sucu_historial = (
                df_vales_repo[df_vales_repo["Sucursal"] == usr_actual["nombre"]]
                if not df_vales_repo.empty
                else pd.DataFrame()
            )

            dict_vales_existentes = {}
            if not df_vales_sucu_historial.empty:
                for _, row_v in df_vales_sucu_historial.iterrows():
                    dict_vales_existentes[row_v["N_Ticket"]] = {
                        "ID_Vale": row_v["ID_Vale"],
                        "Fecha": row_v["Fecha_Origen"],
                        "Estado": row_v["Estado"],
                    }

            df_recetas["Ya_Tiene_Vale"] = df_recetas["N° Ticket"].isin(
                dict_vales_existentes.keys()
            )

            total_recetas_zweb = len(df_recetas)
            vales_preexistentes_count = df_recetas["Ya_Tiene_Vale"].sum()
            esperado_fisico = total_recetas_zweb - vales_preexistentes_count

            col1, col2, col3 = st.columns(3)
            col1.metric("Total Recetas Zweb", total_recetas_zweb)
            col2.metric("Vales Ya Registrados (Previos)", vales_preexistentes_count)

            if vales_preexistentes_count > 0:
                st.info(
                    f"💡 Se detectaron **{vales_preexistentes_count}** receta(s)** en el CSV que ya fueron convertidas en Vale anteriormente."
                )

            st.divider()

            # PASO 1
            st.subheader("1. Conteo Físico por Obra Social")
            resumen = (
                df_recetas[~df_recetas["Ya_Tiene_Vale"]]
                .groupby("Obra Social")
                .size()
                .reset_index(name="Físico Esperado")
            )

            conteo_real_dict = {}

            for idx, row in resumen.iterrows():
                os_nombre = row["Obra Social"]
                esperado = row["Físico Esperado"]

                c_os1, c_os2, c_os3, c_os4 = st.columns([3, 2, 2, 3])
                c_os1.markdown(f"**{os_nombre}**")
                c_os2.caption(f"Esperado: {esperado}")

                enviado_real = c_os3.number_input(
                    f"Real {os_nombre}",
                    min_value=0,
                    max_value=esperado,
                    value=esperado,
                    key=f"inp_{os_nombre}",
                )
                conteo_real_dict[os_nombre] = enviado_real

                diferencia = enviado_real - esperado
                if diferencia < 0:
                    c_os4.warning(f"⚠ Faltan {abs(diferencia)} receta(s)")
                else:
                    c_os4.success("✅ OK")

                st.divider()

                # PASO 2
                st.subheader("2. Selección de Recetas para Convertir en Vale")

                df_disponibles = df_recetas.copy()

                def obtener_estado_vale(row):
                    t = row["N° Ticket"]
                    if t in dict_vales_existentes:
                        info = dict_vales_existentes[t]
                        return f"⚠ REGISTRADO ({info['ID_Vale']} - {info['Fecha']} [{info['Estado']}])"
                    return "Disponible"

                df_disponibles["Estado_Historial"] = df_disponibles.apply(
                    obtener_estado_vale, axis=1
                )
                st.session_state.tickets_tildados = {
                    t
                    for t in st.session_state.tickets_tildados
                    if t not in dict_vales_existentes
                }

                col_busq1, col_busq2 = st.columns([3, 1])
                busqueda_receta = col_busq1.text_input(
                    "🔍 Buscar receta por Ticket, T.T u Obra Social",
                    placeholder="Ej: 0908-00525809 o JERARQUICOS...",
                    key="busq_receta_lote",
                )
                if busqueda_receta:
                    if col_busq2.button("Limpiar Búsqueda", use_container_width=True):
                        st.session_state.busq_receta_lote = ""
                        st.rerun()

                df_filtrado_vista = df_disponibles.copy()
                if busqueda_receta:
                    q = busqueda_receta.strip().lower()
                    df_filtrado_vista = df_filtrado_vista[
                        df_filtrado_vista["N° Ticket"]
                        .astype(str)
                        .str.lower()
                        .str.contains(q)
                        | df_filtrado_vista["T.T (Tramitación)"]
                        .astype(str)
                        .str.lower()
                        .str.contains(q)
                        | df_filtrado_vista["Obra Social"]
                        .astype(str)
                        .str.lower()
                        .str.contains(q)
                        | df_filtrado_vista["Plan"]
                        .astype(str)
                        .str.lower()
                        .str.contains(q)
                    ]

                df_filtrado_vista["Marcar_Vale"] = df_filtrado_vista["N° Ticket"].isin(
                    st.session_state.tickets_tildados
                )

                edited_df = st.data_editor(
                    df_filtrado_vista[
                        [
                            "Obra Social",
                            "Plan",
                            "N° Ticket",
                            "T.T (Tramitación)",
                            "Estado_Historial",
                            "Marcar_Vale",
                        ]
                    ],
                    column_config={
                        "Estado_Historial": st.column_config.TextColumn(
                            "Estado en Histórico"
                        ),
                        "Marcar_Vale": st.column_config.CheckboxColumn(
                            "¿Convertir en Vale?", default=False
                        ),
                    },
                    disabled=[
                        "Obra Social",
                        "Plan",
                        "N° Ticket",
                        "T.T (Tramitación)",
                        "Estado_Historial",
                    ],
                    hide_index=True,
                    use_container_width=True,
                    key="editor_vales_sucu",
                )

                if (
                    "editor_vales_sucu" in st.session_state
                    and "edited_rows" in st.session_state.editor_vales_sucu
                ):
                    for idx, cambios in st.session_state.editor_vales_sucu[
                        "edited_rows"
                    ].items():
                        if "Marcar_Vale" in cambios:
                            ticket_afectado = df_filtrado_vista.iloc[idx]["N° Ticket"]
                            if ticket_afectado in dict_vales_existentes:
                                st.error(
                                    f"🚫 El ticket {ticket_afectado} ya fue convertido en vale anteriormente."
                                )
                            else:
                                if cambios["Marcar_Vale"]:
                                    st.session_state.tickets_tildados.add(
                                        ticket_afectado
                                    )
                                else:
                                    st.session_state.tickets_tildados.discard(
                                        ticket_afectado
                                    )

                df_seleccionados = df_recetas[
                    (df_recetas["N° Ticket"].isin(st.session_state.tickets_tildados))
                    & (~df_recetas["Ya_Tiene_Vale"])
                ].copy()

                motivo_general = "Medicamento pendiente de entrega"
                if not df_seleccionados.empty:
                    st.markdown(
                        f"**Recetas tildadas en este lote para Vale:** `{len(df_seleccionados)}`"
                    )
                    motivo_general = st.text_input(
                        "Motivo general de los vales", value=motivo_general
                    )

                st.divider()

                # PASO 3
                st.subheader("3. Confirmación y Cierre del Lote")

                total_fisico_enviar = sum(conteo_real_dict.values())
                cant_vales_a_crear = len(df_seleccionados)

                df_recetas_fisicas_enviadas = df_recetas[
                    (~df_recetas["N° Ticket"].isin(st.session_state.tickets_tildados))
                    & (~df_recetas["Ya_Tiene_Vale"])
                ][["Obra Social", "Plan", "N° Ticket", "T.T (Tramitación)"]].copy()

                st.warning(
                    f"📋 **Resumen Final de Cierre:**  \n"
                    f"• **Recetas Físicas a Enviar:** {total_fisico_enviar}  \n"
                    f"• **Nuevos Vales a Registrar:** {cant_vales_a_crear}"
                )

                if st.button(
                    "🔒 CONFIRMAR Y CERRAR LOTE DEL DÍA",
                    type="primary",
                    use_container_width=True,
                ):
                    tickets_duplicados_intentados = [
                        t
                        for t in st.session_state.tickets_tildados
                        if t in dict_vales_existentes
                    ]

                    if tickets_duplicados_intentados:
                        st.error(
                            f"⛔ ERROR DE SEGURIDAD: Los siguientes tickets ya existen en el repositorio: {', '.join(tickets_duplicados_intentados)}."
                        )
                    else:
                        cant_existentes = len(df_vales_repo)
                        nuevos_vales = []

                        for i, (_, fila) in enumerate(df_seleccionados.iterrows()):
                            nuevos_vales.append(
                                {
                                    "ID_Vale": f"VALE-{cant_existentes + i + 1:04d}",
                                    "ID_Lote": id_lote_actual,
                                    "Sucursal": usr_actual["nombre"],
                                    "Fecha_Origen": str(fecha_carga),
                                    "Obra_Social": fila["Obra Social"],
                                    "Plan": fila["Plan"],
                                    "N_Ticket": fila["N° Ticket"],
                                    "TT_Tramitacion": fila["T.T (Tramitación)"],
                                    "Motivo": motivo_general,
                                    "Estado": "PENDIENTE",
                                    "Fecha_Resolucion": "-",
                                    "Observacion": "-",
                                }
                            )

                        if nuevos_vales:
                            df_vales_actualizado = pd.concat(
                                [df_vales_repo, pd.DataFrame(nuevos_vales)],
                                ignore_index=True,
                            )
                            guardar_json(df_vales_actualizado, ARCHIVO_VALES)

                    nuevo_lote = {
                        "id_lote": id_lote_actual,
                        "sucursal": usr_actual["nombre"],
                        "fecha_carga": str(fecha_carga),
                        "total_recetas": total_recetas_zweb,
                        "fisico_enviado": total_fisico_enviar,
                        "vales_generados": cant_vales_a_crear,
                        "estado_lote": "ENVIADO",
                        "desglose_obra_social": json.dumps(
                            conteo_real_dict, ensure_ascii=False
                        ),
                        "detalle_recetas_fisicas": json.dumps(
                            df_recetas_fisicas_enviadas.to_dict(orient="records"),
                            ensure_ascii=False,
                        ),
                    }

                    # En lugar de guardar en el DataFrame local y llamar a guardar_json, guardás directamente en Supabase:
                    supabase.table("cargas").upsert(nuevo_lote).execute()

                    st.session_state.tickets_tildados.clear()
                    mostrar_konyu("konyu_ok.png", caption="¡Lote Cerrado!", width=100)
                    st.success(
                        f"🎉 ¡Lote {id_lote_actual} CERRADO Y ENVIADO con éxito!"
                    )
                    st.rerun()


# 7. SUCURSAL - Vales e Histórico
elif usr_actual["rol"] == "Sucursal" and menu == "📜 Gestión de Vales e Histórico":
    st.title("📜 Gestión de Vales e Histórico de Cargas")
    st.write(f"Sucursal: **{usr_actual['nombre']}**")

    df_cargas = cargar_json(ARCHIVO_CARGAS, COLUMNAS_CARGAS)
    df_vales = cargar_json(ARCHIVO_VALES, COLUMNAS_VALES)

    df_cargas_sucu = df_cargas[df_cargas["Sucursal"] == usr_actual["nombre"]]
    df_vales_sucu = df_vales[df_vales["Sucursal"] == usr_actual["nombre"]]

    tab1, tab2, tab3 = st.tabs(
        [
            "📦 Vales Pendientes (Enviar / Anular)",
            "✅ Histórico de Vales Enviados y Resueltos",
            "📋 Histórico de Lotes y Descarga PDF",
        ]
    )

    with tab1:
        st.subheader("1. Vales Pendientes por Fecha de Origen")
        vales_pendientes = df_vales_sucu[df_vales_sucu["Estado"] == "PENDIENTE"]

        if vales_pendientes.empty:
            mostrar_konyu("konyu_ok.png", caption="¡Todo al día!", width=100)
            st.info("🎉 ¡Excelente! No tenés vales pendientes en esta sucursal.")
        else:
            fechas_disponibles = sorted(
                list(vales_pendientes["Fecha_Origen"].unique()), reverse=True
            )

            c_sel1, c_sel2 = st.columns([2, 3])
            fecha_origen_sel = c_sel1.selectbox(
                "📅 Fecha de Origen de la Receta / Vale", fechas_disponibles
            )
            busqueda_query = c_sel2.text_input(
                "🔍 Buscar por Ticket, T.T u Obra Social",
                placeholder="Escribí número de ticket...",
                key="busq_pend",
            )

            vales_fecha_sel = vales_pendientes[
                vales_pendientes["Fecha_Origen"] == fecha_origen_sel
            ].copy()

            if busqueda_query:
                q = busqueda_query.strip().lower()
                vales_fecha_sel = vales_fecha_sel[
                    vales_fecha_sel["N_Ticket"].astype(str).str.lower().str.contains(q)
                    | vales_fecha_sel["TT_Tramitacion"]
                    .astype(str)
                    .str.lower()
                    .str.contains(q)
                    | vales_fecha_sel["Obra_Social"]
                    .astype(str)
                    .str.lower()
                    .str.contains(q)
                ]

            st.markdown(
                f"##### Vales Pendientes del `{fecha_origen_sel}` ({len(vales_fecha_sel)} disponibles)"
            )

            if vales_fecha_sel.empty:
                st.warning(
                    "No se encontraron vales pendientes para la búsqueda ingresada."
                )
            else:
                vales_fecha_sel["Seleccionar"] = False

                edited_vales_df = st.data_editor(
                    vales_fecha_sel[
                        [
                            "ID_Vale",
                            "Obra_Social",
                            "Plan",
                            "N_Ticket",
                            "TT_Tramitacion",
                            "Motivo",
                            "Seleccionar",
                        ]
                    ],
                    column_config={
                        "Seleccionar": st.column_config.CheckboxColumn(
                            "¿Marcar Vale?", default=False
                        )
                    },
                    disabled=[
                        "ID_Vale",
                        "Obra_Social",
                        "Plan",
                        "N_Ticket",
                        "TT_Tramitacion",
                        "Motivo",
                    ],
                    hide_index=True,
                    use_container_width=True,
                    key="editor_envio_vales",
                )

                vales_seleccionados_ids = []
                if (
                    "editor_envio_vales" in st.session_state
                    and "edited_rows" in st.session_state.editor_envio_vales
                ):
                    for row_idx, cambios in st.session_state.editor_envio_vales[
                        "edited_rows"
                    ].items():
                        if cambios.get("Seleccionar") is True:
                            id_v = vales_fecha_sel.iloc[row_idx]["ID_Vale"]
                            vales_seleccionados_ids.append(id_v)

                if vales_seleccionados_ids:
                    fecha_hoy_str = datetime.date.today().strftime("%Y-%m-%d")
                    st.success(
                        f"Has seleccionado **{len(vales_seleccionados_ids)} vale(s)** del `{fecha_origen_sel}`."
                    )

                    col_obs, col_btn1, col_btn2 = st.columns([3, 2, 2])
                    obs_nota = col_obs.text_input(
                        "Observación / Motivo de cambio",
                        value=f"Gestión realizada el {fecha_hoy_str}",
                    )

                    if col_btn1.button(
                        "🚀 REGISTRAR ENVÍO", type="primary", use_container_width=True
                    ):
                        for id_v in vales_seleccionados_ids:
                            idx = df_vales[df_vales["ID_Vale"] == id_v].index[0]
                            df_vales.at[idx, "Estado"] = "ENVIADO"
                            df_vales.at[idx, "Fecha_Resolucion"] = fecha_hoy_str
                            df_vales.at[idx, "Observacion"] = obs_nota

                        guardar_json(df_vales, ARCHIVO_VALES)
                        st.success(
                            f"¡Se registraron {len(vales_seleccionados_ids)} vales como ENVIADOS!"
                        )
                        st.rerun()

                    if col_btn2.button(
                        "❌ ANULAR / DESCHACAR",
                        type="secondary",
                        use_container_width=True,
                    ):
                        for id_v in vales_seleccionados_ids:
                            idx = df_vales[df_vales["ID_Vale"] == id_v].index[0]
                            df_vales.at[idx, "Estado"] = "CANCELADO"
                            df_vales.at[idx, "Fecha_Resolucion"] = fecha_hoy_str
                            df_vales.at[idx, "Observacion"] = (
                                f"Anulado sin enviar: {obs_nota}"
                            )

                        guardar_json(df_vales, ARCHIVO_VALES)
                        st.warning(
                            f"¡Se marcaron {len(vales_seleccionados_ids)} vales como CANCELADOS!"
                        )
                        st.rerun()

    with tab2:
        st.subheader("✅ Registro de Vales Completados y Enviados")
        vales_resueltos = df_vales_sucu[df_vales_sucu["Estado"] != "PENDIENTE"]

        if vales_resueltos.empty:
            st.info(
                "Aún no se registraron envíos ni resoluciones de vales en esta sucursal."
            )
        else:
            c_f_env1, c_f_env2 = st.columns([2, 3])
            estado_res_filtro = c_f_env1.selectbox(
                "Filtrar por Estado", ["TODOS", "ENVIADO", "CANCELADO"], index=0
            )
            busq_resueltos = c_f_env2.text_input(
                "🔍 Buscar por Ticket, T.T, ID o Nota",
                placeholder="Escribí para buscar...",
                key="busq_env",
            )

            df_res_view = vales_resueltos.copy()

            if estado_res_filtro != "TODOS":
                df_res_view = df_res_view[df_res_view["Estado"] == estado_res_filtro]

            if busq_resueltos:
                bq = busq_resueltos.strip().lower()
                df_res_view = df_res_view[
                    df_res_view["ID_Vale"].astype(str).str.lower().str.contains(bq)
                    | df_res_view["N_Ticket"].astype(str).str.lower().str.contains(bq)
                    | df_res_view["TT_Tramitacion"]
                    .astype(str)
                    .str.lower()
                    .str.contains(bq)
                    | df_res_view["Obra_Social"]
                    .astype(str)
                    .str.lower()
                    .str.contains(bq)
                    | df_res_view["Observacion"]
                    .astype(str)
                    .str.lower()
                    .str.contains(bq)
                ]

            st.markdown(f"##### Vales Registrados: **{len(df_res_view)}**")
            st.dataframe(
                df_res_view[
                    [
                        "ID_Vale",
                        "Fecha_Origen",
                        "Fecha_Resolucion",
                        "Obra_Social",
                        "N_Ticket",
                        "TT_Tramitacion",
                        "Estado",
                        "Observacion",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
            )

    with tab3:
        st.subheader("📋 Resumen de Lotes Diarios")
        if df_cargas_sucu.empty:
            st.info("No hay cargas registradas previamente.")
        else:
            st.dataframe(
                df_cargas_sucu.drop(
                    columns=["Desglose_Obra_Social", "Detalle_Recetas_Fisicas"],
                    errors="ignore",
                ),
                use_container_width=True,
                hide_index=True,
            )

            st.divider()

            st.subheader("📄 Descargar Planilla PDF de un Lote Pasado")
            lote_id_pdf = st.selectbox(
                "Seleccionar Lote para Descargar PDF",
                df_cargas_sucu["ID_Lote"].tolist(),
            )

            if lote_id_pdf:
                info_l = df_cargas_sucu[df_cargas_sucu["ID_Lote"] == lote_id_pdf].iloc[
                    0
                ]
                vales_l = df_vales_sucu[df_vales_sucu["ID_Lote"] == lote_id_pdf]
                df_res_l = preparar_df_resumen(info_l.get("Desglose_Obra_Social", "{}"))
                df_det_l = preparar_df_recetas_fisicas(
                    info_l.get("Detalle_Recetas_Fisicas", "[]")
                )

                pdf_b = generar_pdf_cierre(
                    df_res_l,
                    df_det_l,
                    vales_l,
                    usr_actual["nombre"],
                    info_l["Fecha_Carga"],
                )
                st.download_button(
                    f"📥 Descargar PDF Cierre {lote_id_pdf}",
                    data=pdf_b,
                    file_name=f"Cierre_{lote_id_pdf}.pdf",
                    mime="application/pdf",
                    type="primary",
                )


# 8. MUTUALES - Recepción
elif usr_actual["rol"] == "Mutuales" and menu == "📥 Recepción de Lotes por Sucursal":
    st.title("📥 Mesa de Entrada - Recepción Física de Lotes")
    st.write("Control directo de paquetes físicos y lotes enviados por las sucursales.")

    df_cargas_global = cargar_json(ARCHIVO_CARGAS, COLUMNAS_CARGAS)
    df_vales_global = cargar_json(ARCHIVO_VALES, COLUMNAS_VALES)

    usuarios_sistema = cargar_usuarios()
    sucursales_base = [
        datos["nombre"]
        for datos in usuarios_sistema.values()
        if datos.get("rol") == "Sucursal"
    ]

    if not sucursales_base:
        sucursales_base = ["Sin Sucursales"]

    col_sel_suc, col_fil_est = st.columns([3, 2])
    sucursal_seleccionada = col_sel_suc.selectbox(
        "🏢 Seleccionar Sucursal a Auditar", sucursales_base
    )
    filtro_estado = col_fil_est.selectbox(
        "Filtrar por Estado de Lote",
        ["TODOS", "ENVIADO (PENDIENTES DE CONFIRMAR)", "RECIBIDO", "CANCELADO"],
    )

    df_lotes_sucu = df_cargas_global[
        df_cargas_global["Sucursal"] == sucursal_seleccionada
    ].copy()

    if filtro_estado != "TODOS":
        if "ENVIADO" in filtro_estado:
            df_lotes_sucu = df_lotes_sucu[
                df_lotes_sucu["Estado_Lote"].isin(["ENVIADO", "PENDIENTE"])
            ]
        else:
            df_lotes_sucu = df_lotes_sucu[df_lotes_sucu["Estado_Lote"] == filtro_estado]

    st.divider()

    if df_lotes_sucu.empty:
        mostrar_konyu("konyu_empty.png", caption="Sin lotes pendientes", width=100)
        st.info(
            f"No hay lotes registrados para **{sucursal_seleccionada}** con el filtro seleccionado."
        )
    else:
        st.subheader(f"📋 Lotes de {sucursal_seleccionada} ({len(df_lotes_sucu)})")

        for idx, row in df_lotes_sucu.iterrows():
            id_lote = row["ID_Lote"]
            fecha_lote = row["Fecha_Carga"]
            recetas_fisicas = row["Fisico_Enviado"]
            vales_gen = row["Vales_Generados"]
            estado_lote = row.get("Estado_Lote", "ENVIADO")

            if estado_lote == "RECIBIDO":
                badge_estado = "✅ RECIBIDO"
            elif estado_lote == "CANCELADO":
                badge_estado = "❌ CANCELADO POR SUCURSAL"
            else:
                badge_estado = "⏳ EN TRANSITO / PENDIENTE DE RECEPCIÓN"

            with st.expander(
                f"📦 Lote `{id_lote}` | Fecha: **{fecha_lote}** | Estado: **{badge_estado}**",
                expanded=False,
            ):
                c_m1, c_m2, c_m3, c_m4 = st.columns([2, 2, 2, 3])
                c_m1.metric("Físico Declarado", f"{recetas_fisicas} recetas")
                c_m2.metric("Vales en Lote", f"{vales_gen} vales")
                c_m3.write(f"**Estado Actual:**  \n`{estado_lote}`")

                if estado_lote != "RECIBIDO" and estado_lote != "CANCELADO":
                    if c_m4.button(
                        "✅ Confirmar Recepción Física",
                        key=f"btn_recibido_{id_lote}",
                        type="primary",
                    ):
                        idx_l = df_cargas_global[
                            df_cargas_global["ID_Lote"] == id_lote
                        ].index[0]
                        df_cargas_global.at[idx_l, "Estado_Lote"] = "RECIBIDO"
                        guardar_json(df_cargas_global, ARCHIVO_CARGAS)
                        st.success(f"¡Lote {id_lote} confirmado como RECIBIDO!")
                        st.rerun()
                else:
                    c_m4.success("📦 Lote procesado y verificado por Mutuales.")

                st.divider()

                vales_lote = df_vales_global[df_vales_global["ID_Lote"] == id_lote]
                vales_pendientes_count = len(
                    vales_lote[vales_lote["Estado"] == "PENDIENTE"]
                )

                st.markdown(f"##### 🔎 Detalle de Vales en Lote `{id_lote}`")
                if vales_pendientes_count > 0:
                    st.warning(
                        f"⚠ Este lote contiene **{vales_pendientes_count} vale(s) PENDIENTE(S)** de entrega de medicamento."
                    )
                else:
                    st.info(
                        "ℹ Todos los vales de este lote están resueltos o no requirió vales."
                    )

                if vales_lote.empty:
                    st.caption("No se generaron vales en este lote.")
                else:
                    st.dataframe(
                        vales_lote[
                            [
                                "ID_Vale",
                                "Obra_Social",
                                "Plan",
                                "N_Ticket",
                                "TT_Tramitacion",
                                "Motivo",
                                "Estado",
                                "Observacion",
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True,
                    )

                df_resumen_lote_m = preparar_df_resumen(
                    row.get("Desglose_Obra_Social", "{}")
                )
                df_recetas_fisicas_m = preparar_df_recetas_fisicas(
                    row.get("Detalle_Recetas_Fisicas", "[]")
                )

                pdf_lote_bytes = generar_pdf_cierre(
                    df_resumen_lote_m,
                    df_recetas_fisicas_m,
                    vales_lote,
                    sucursal_seleccionada,
                    fecha_lote,
                )
                st.download_button(
                    f"📄 Descargar Planilla PDF de Cierre ({id_lote})",
                    data=pdf_lote_bytes,
                    file_name=f"Planilla_Cierre_{id_lote}.pdf",
                    mime="application/pdf",
                    key=f"pdf_btn_{id_lote}",
                )


# 9. MUTUALES - Auditoría Global
elif usr_actual["rol"] == "Mutuales" and menu == "📦 Auditoría Global de Vales":
    st.title("📦 Panel General de Auditoría de Vales")
    st.write("Módulo de consulta unificada por sucursal y fecha de origen.")

    df_vales_global = cargar_json(ARCHIVO_VALES, COLUMNAS_VALES)

    if df_vales_global.empty:
        mostrar_konyu("konyu_empty.png", caption="Sin vales registrados", width=100)
        st.info("No hay vales registrados en el sistema.")
    else:
        sucursales_list = sorted(
            list(
                set(
                    [
                        USUARIOS_BASE[u]["nombre"]
                        for u in USUARIOS_BASE
                        if USUARIOS_BASE[u]["rol"] == "Sucursal"
                    ]
                    + df_vales_global["Sucursal"].tolist()
                )
            )
        )

        st.subheader("🔎 Selección de Sucursal y Fecha")
        col_sucu_sel, col_fecha_sel = st.columns(2)

        sucu_seleccionada = col_sucu_sel.selectbox(
            "🏢 Seleccionar Sucursal",
            options=sucursales_list,
            index=None,
            placeholder="Selecciona una sucursal...",
        )

        fecha_seleccionada = None
        if sucu_seleccionada:
            fecha_seleccionada = col_fecha_sel.date_input(
                "📅 Seleccionar Fecha de Origen", value=None, format="YYYY-MM-DD"
            )
        else:
            col_fecha_sel.info(
                "👈 Primero selecciona una sucursal para habilitar el calendario."
            )

        st.divider()

        if sucu_seleccionada and fecha_seleccionada:
            fecha_str = fecha_seleccionada.strftime("%Y-%m-%d")

            df_vales_dia = df_vales_global[
                (df_vales_global["Sucursal"] == sucu_seleccionada)
                & (df_vales_global["Fecha_Origen"] == fecha_str)
            ].copy()

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Vales del Día", len(df_vales_dia))
            m2.metric(
                "Pendientes", len(df_vales_dia[df_vales_dia["Estado"] == "PENDIENTE"])
            )
            m3.metric(
                "Enviados", len(df_vales_dia[df_vales_dia["Estado"] == "ENVIADO"])
            )
            m4.metric(
                "Cancelados / Anulados",
                len(df_vales_dia[df_vales_dia["Estado"] == "CANCELADO"]),
            )

            st.divider()

            st.subheader(f"📋 Vales de {sucu_seleccionada} - Fecha: {fecha_str}")

            if df_vales_dia.empty:
                mostrar_konyu(
                    "konyu_empty.png", caption="Sin datos para esta fecha", width=100
                )
                st.warning(
                    f"No se encontraron vales registrados para **{sucu_seleccionada}** el día **{fecha_str}**."
                )
            else:
                c_f1, c_f2, c_f3 = st.columns([2, 2, 3])

                estados_list = ["TODOS"] + sorted(list(df_vales_dia["Estado"].unique()))
                obras_sociales_list = ["TODAS"] + sorted(
                    list(df_vales_dia["Obra_Social"].unique())
                )

                estado_filtro = c_f1.selectbox(
                    "Estado del Vale", estados_list, key="fil_est_aud"
                )
                os_filtro = c_f2.selectbox(
                    "Obra Social", obras_sociales_list, key="fil_os_aud"
                )
                busq_libre = c_f3.text_input(
                    "🔍 Buscar manualmente (Ticket / T.T / ID / Motivo)",
                    placeholder="Escribí para buscar...",
                    key="busq_aud",
                )

                df_filtrado_final = df_vales_dia.copy()

                if estado_filtro != "TODOS":
                    df_filtrado_final = df_filtrado_final[
                        df_filtrado_final["Estado"] == estado_filtro
                    ]
                if os_filtro != "TODAS":
                    df_filtrado_final = df_filtrado_final[
                        df_filtrado_final["Obra_Social"] == os_filtro
                    ]
                if busq_libre:
                    bq = busq_libre.strip().lower()
                    df_filtrado_final = df_filtrado_final[
                        df_filtrado_final["ID_Vale"]
                        .astype(str)
                        .str.lower()
                        .str.contains(bq)
                        | df_filtrado_final["N_Ticket"]
                        .astype(str)
                        .str.lower()
                        .str.contains(bq)
                        | df_filtrado_final["TT_Tramitacion"]
                        .astype(str)
                        .str.lower()
                        .str.contains(bq)
                        | df_filtrado_final["Motivo"]
                        .astype(str)
                        .str.lower()
                        .str.contains(bq)
                        | df_filtrado_final["Observacion"]
                        .astype(str)
                        .str.lower()
                        .str.contains(bq)
                    ]

                st.markdown(
                    f"##### Registros coincidentes: **{len(df_filtrado_final)}**"
                )

                st.dataframe(
                    df_filtrado_final, use_container_width=True, hide_index=True
                )

                csv_export = df_filtrado_final.to_csv(index=False, encoding="utf-8-sig")
                st.download_button(
                    "📥 Exportar Listado Filtrado a CSV / Excel",
                    data=csv_export,
                    file_name=f"Vales_{sucu_seleccionada}_{fecha_str}.csv",
                    mime="text/csv",
                )

        else:
            mostrar_konyu("konyu_logo.png", caption="Konyu te orienta", width=100)
            st.info(
                "📌 **Indicaciones:** Selecciona primero una sucursal y un día en el calendario para visualizar las métricas y la lista de vales correspondiente."
            )
# 10. MUTUALES - Gestión de Usuarios
elif usr_actual["rol"] == "Mutuales" and "Gestión de Usuarios" in menu:
    render_gestion_usuarios()
