import datetime
import re
import pandas as pd
import streamlit as st

# 1. Configuración de la página web
st.set_page_config(
    page_title="FARMA-CHECK",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos visuales para el modo oscuro (Dark Mode)
st.markdown(
    """
    <style>
        .stApp {
            background-color: #0B0F17;
            color: #E2E8F0;
        }
        [data-testid="stSidebar"] {
            background-color: #111827;
            border-right: 1px solid #1E293B;
        }
        .stMetric {
            background-color: #161D2A;
            padding: 15px;
            border-radius: 12px;
            border: 1px solid #1E293B;
        }
    </style>
""",
    unsafe_allow_html=True,
)

# Inicializar repositorios en session_state
if "repositorio_vales" not in st.session_state:
    st.session_state.repositorio_vales = pd.DataFrame(
        columns=[
            "ID_Vale",
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
    )

if "tickets_tildados" not in st.session_state:
    st.session_state.tickets_tildados = set()


# 2. Función para procesar el CSV de Zweb
def procesar_csv(file):
    recetas = []
    obra_social_actual = "GENERAL"
    patron_ticket = re.compile(r"(\d{4}-\d{8})")
    lines = file.getvalue().decode("latin1").splitlines()

    for line in lines:
        columnas = [p.strip() for p in line.split(";") if p.strip()]

        if columnas:
            val = columnas[0]
            if not (
                val.startswith("A") and len(val) == 5 and val[1:].isdigit()
            ):
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

            recetas.append({
                "Obra Social": obra_social_actual,
                "Plan": plan,
                "N° Ticket": ticket_nro,
                "T.T (Tramitación)": tt_nro,
            })

    return pd.DataFrame(recetas)


# 3. Menú Lateral
with st.sidebar:
    st.title("🐾 FARMA-CHECK")
    st.caption("Control de Recetas y Vales")
    st.divider()

    menu = st.radio(
        "Navegación",
        ["📊 Control del Día", "📦 Gestión de Vales", "⚙️ Configuración"],
    )

# 4. Pantalla Principal: Control del Día
if menu == "📊 Control del Día":
    st.title("Control de Recetas Diarias")
    st.write("Cargá el archivo CSV del día para validar el envío y gestionar faltantes.")

    archivo_csv = st.file_uploader(
        "Cargar informe Zweb (.csv)", type=["csv"], key="csv_uploader"
    )

    if archivo_csv is not None:
        df_recetas = procesar_csv(archivo_csv)

        if not df_recetas.empty:
            # Vales activos guardados en la BD de session_state
            vales_activos_tickets = st.session_state.repositorio_vales[
                st.session_state.repositorio_vales["Estado"] == "PENDIENTE"
            ]["N_Ticket"].tolist()

            df_recetas["Es_Vale_Activo"] = df_recetas["N° Ticket"].isin(vales_activos_tickets)

            total_recetas_zweb = len(df_recetas)
            vales_descontados = df_recetas["Es_Vale_Activo"].sum()
            esperado_fisico = total_recetas_zweb - vales_descontados

            # KPIs Superiores
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Recetas Zweb", total_recetas_zweb)
            col2.metric("Vales Activos Registrados", vales_descontados)
            col3.metric("Físico Esperado", esperado_fisico)

            st.divider()

            # 1. Resumen y Validación por Obra Social
            st.subheader("1. Conteo y Validación por Obra Social")
            resumen = (
                df_recetas[~df_recetas["Es_Vale_Activo"]]
                .groupby("Obra Social")
                .size()
                .reset_index(name="Físico Esperado")
            )

            st.write("Indicá la cantidad real de recetas que tenés físicamente para enviar:")

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
                    key=f"input_{os_nombre}",
                    label_visibility="collapsed",
                )

                diferencia = enviado_real - esperado

                if diferencia < 0:
                    faltantes = abs(diferencia)
                    c_os4.warning(f"⚠️️ Faltan {faltantes} receta(s)")
                else:
                    c_os4.success("✅ OK")

            st.divider()

            # 2. Buscador y Selección Interactiva de Vales
            st.subheader("2. Seleccionar Recetas para Convertir en Vale")
            st.caption("Buscá las recetas faltantes, tildá las casillas a la derecha y presioná 'Generar Vales'.")

            c_busc1, c_busc2 = st.columns([3, 1])
            busqueda = c_busc1.text_input(
                "Buscar Ticket o T.T",
                placeholder="Ingresá número de Ticket o T.T para filtrar...",
            )
            os_filtro = c_busc2.selectbox(
                "Filtrar por Obra Social",
                ["Todas"] + list(resumen["Obra Social"].unique()),
            )

            # Filtrar recetas disponibles (que no sean ya vales activos)
            df_disponibles = df_recetas[~df_recetas["Es_Vale_Activo"]].copy()

            if os_filtro != "Todas":
                df_disponibles = df_disponibles[df_disponibles["Obra Social"] == os_filtro]

            if busqueda:
                df_disponibles = df_disponibles[
                    df_disponibles["N° Ticket"].str.contains(busqueda)
                    | df_disponibles["T.T (Tramitación)"].str.contains(busqueda)
                ]

            # Agregar columna de tilde
            df_disponibles["Marcar_Vale"] = df_disponibles["N° Ticket"].isin(st.session_state.tickets_tildados)

            # Usar st.data_editor para permitir tildar casillas directamente
            edited_df = st.data_editor(
                df_disponibles[["Obra Social", "Plan", "N° Ticket", "T.T (Tramitación)", "Marcar_Vale"]],
                column_config={
                    "Marcar_Vale": st.column_config.CheckboxColumn(
                        "¿Convertir en Vale?",
                        default=False,
                    )
                },
                disabled=["Obra Social", "Plan", "N° Ticket", "T.T (Tramitación)"],
                hide_index=True,
                use_container_width=True,
                key="editor_vales",
            )

            # Sincronizar tildados del editor con session_state
            if "editor_vales" in st.session_state and "edited_rows" in st.session_state.editor_vales:
                for idx, cambios in st.session_state.editor_vales["edited_rows"].items():
                    if "Marcar_Vale" in cambios:
                        ticket_afectado = df_disponibles.iloc[idx]["N° Ticket"]
                        if cambios["Marcar_Vale"]:
                            st.session_state.tickets_tildados.add(ticket_afectado)
                        else:
                            st.session_state.tickets_tildados.discard(ticket_afectado)

            # Mostrar tickets seleccionados acumulados abajo
            st.markdown("##### 🛒 Recetas Seleccionadas para Vale")

            df_seleccionados = df_recetas[df_recetas["N° Ticket"].isin(st.session_state.tickets_tildados)].copy()

            if not df_seleccionados.empty:
                # Renderizar cada receta tildada con un botón de tacho de basura para quitarla
                for idx_sel, fila_sel in df_seleccionados.iterrows():
                    col_os, col_plan, col_tick, col_tt, col_del = st.columns([3, 2, 3, 3, 1])
                    col_os.write(fila_sel["Obra Social"])
                    col_plan.write(fila_sel["Plan"])
                    col_tick.write(fila_sel["N° Ticket"])
                    col_tt.write(fila_sel["T.T (Tramitación)"])

                    # Botón para des-seleccionar la receta individual
                    if col_del.button("🗑️️", key=f"del_{fila_sel['N° Ticket']}"):
                        st.session_state.tickets_tildados.discard(fila_sel["N° Ticket"])
                        if "editor_vales" in st.session_state:
                            del st.session_state["editor_vales"]
                        st.rerun()

                st.divider()

                col_motivo, col_btn_gen, col_btn_limp = st.columns([3, 2, 1])
                motivo_general = col_motivo.text_input(
                    "Motivo para los vales seleccionados",
                    value="Medicamento pendiente de entrega",
                )

                if col_btn_gen.button(f"📦 Generar {len(df_seleccionados)} Vale(s)", type="primary"):
                    nuevos_vales = []
                    for _, fila in df_seleccionados.iterrows():
                        nuevo_vale = {
                            "ID_Vale": f"VALE-{len(st.session_state.repositorio_vales) + len(nuevos_vales) + 1:04d}",
                            "Fecha_Origen": datetime.date.today().strftime("%Y-%m-%d"),
                            "Obra_Social": fila["Obra Social"],
                            "Plan": fila["Plan"],
                            "N_Ticket": fila["N° Ticket"],
                            "TT_Tramitacion": fila["T.T (Tramitación)"],
                            "Motivo": motivo_general,
                            "Estado": "PENDIENTE",
                            "Fecha_Resolucion": "-",
                            "Observacion": "-",
                        }
                        nuevos_vales.append(nuevo_vale)

                    st.session_state.repositorio_vales = pd.concat(
                        [st.session_state.repositorio_vales, pd.DataFrame(nuevos_vales)],
                        ignore_index=True,
                    )

                    st.session_state.tickets_tildados.clear()
                    if "editor_vales" in st.session_state:
                        del st.session_state["editor_vales"]
                    st.success(f"¡Se generaron {len(nuevos_vales)} vales exitosamente!")
                    st.rerun()

                # Botón "Limpiar Selección"
                if col_btn_limp.button("🧹 Limpiar Selección"):
                    st.session_state.tickets_tildados.clear()
                    if "editor_vales" in st.session_state:
                        del st.session_state["editor_vales"]
                    st.rerun()
            else:
                st.info("Aún no has tildado ninguna receta en la tabla.")

        else:
            st.warning("No se encontraron tickets válidos en el CSV.")

# 5. Pantalla: Gestión de Vales (Repositorio)
elif menu == "📦 Gestión de Vales":
    st.title("📦 Repositorio y Gestión de Vales")
    st.write("Administrá, resolvé o eliminá vales generados por error.")

    df_vales = st.session_state.repositorio_vales

    if df_vales.empty:
        st.info("No hay vales registrados en el sistema.")
    else:
        # Filtros de búsqueda (Estado + Texto libre)
        col_f1, col_f2 = st.columns([2, 3])

        estado_filtro = col_f1.radio(
            "Filtrar por Estado",
            ["PENDIENTE", "ENVIADO", "CANCELADO", "TODOS"],
            horizontal=True,
        )

        busqueda_vale = col_f2.text_input(
            "🔍 Buscar Vale por ID, Ticket, T.T u Obra Social",
            placeholder="Escribí para buscar...",
        )

        # Aplicar filtro por estado
        df_vales_view = df_vales.copy()
        if estado_filtro != "TODOS":
            df_vales_view = df_vales_view[df_vales_view["Estado"] == estado_filtro]

        # Aplicar filtro por texto ingresado
        if busqueda_vale:
            query = busqueda_vale.strip().lower()
            df_vales_view = df_vales_view[
                df_vales_view["ID_Vale"].str.lower().str.contains(query)
                | df_vales_view["N_Ticket"].str.lower().str.contains(query)
                | df_vales_view["TT_Tramitacion"].str.lower().str.contains(query)
                | df_vales_view["Obra_Social"].str.lower().str.contains(query)
            ]

        # Mostrar tabla filtrada
        st.dataframe(df_vales_view, use_container_width=True, hide_index=True)

        st.divider()

        # Acciones sobre Vales
        st.subheader("Acciones de Vales")

        if df_vales_view.empty:
            st.warning("No se encontraron vales que coincidan con la búsqueda.")
        else:
            c_act1, c_act2, c_act3 = st.columns([3, 2, 3])

            # El menú desplegable muestra únicamente los vales filtrados por la búsqueda arriba
            id_vale_sel = c_act1.selectbox(
                "Seleccionar Vale",
                options=df_vales_view["ID_Vale"].tolist(),
                format_func=lambda x: f"{x} | Ticket: {df_vales[df_vales['ID_Vale'] == x]['N_Ticket'].values[0]} | Estado: {df_vales[df_vales['ID_Vale'] == x]['Estado'].values[0]}",
            )

            obs_resolucion = c_act2.text_input("Observación / Nota", value="Procesado desde gestión")

            col_b1, col_b2, col_b3 = c_act3.columns(3)

            if col_b1.button("✅ Enviar", type="primary"):
                idx = st.session_state.repositorio_vales[
                    st.session_state.repositorio_vales["ID_Vale"] == id_vale_sel
                ].index[0]

                st.session_state.repositorio_vales.at[idx, "Estado"] = "ENVIADO"
                st.session_state.repositorio_vales.at[idx, "Fecha_Resolucion"] = datetime.date.today().strftime("%Y-%m-%d")
                st.session_state.repositorio_vales.at[idx, "Observacion"] = obs_resolucion

                st.success(f"Vale {id_vale_sel} marcado como ENVIADO.")
                st.rerun()

            if col_b2.button("❌ Cancelar"):
                idx = st.session_state.repositorio_vales[
                    st.session_state.repositorio_vales["ID_Vale"] == id_vale_sel
                ].index[0]

                st.session_state.repositorio_vales.at[idx, "Estado"] = "CANCELADO"
                st.session_state.repositorio_vales.at[idx, "Fecha_Resolucion"] = datetime.date.today().strftime("%Y-%m-%d")
                st.session_state.repositorio_vales.at[idx, "Observacion"] = obs_resolucion

                st.warning(f"Vale {id_vale_sel} CANCELADO.")
                st.rerun()

            # Botón para borrar vale cargado por error
            if col_b3.button("🗑️ Eliminar Error"):
                st.session_state.repositorio_vales = st.session_state.repositorio_vales[
                    st.session_state.repositorio_vales["ID_Vale"] != id_vale_sel
                ].reset_index(drop=True)

                st.error(f"Vale {id_vale_sel} ELIMINADO del sistema por error de carga.")
                st.rerun()