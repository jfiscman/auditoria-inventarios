#!/usr/bin/env python3
"""
Auditoría de Inventarios — Streamlit App
=========================================
Compara conteo físico de sucursal vs. stock del sistema central.
Para el analista: subí los CSVs, obtené el reporte al instante.

Uso:
  streamlit run auditoria_app.py
"""

import streamlit as st
import pandas as pd
import csv
import os
import json
from datetime import datetime
from io import StringIO
from pathlib import Path

# ─────────────────────────────────────────────
#  Configuración de página
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Auditoría de Inventarios",
    page_icon="📦",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── Estilo personalizado (light mode, cream bg) ───
st.markdown("""
<style>
    /* Base */
    .stApp {
        background-color: #f7f6f3;
    }
    .main > div {
        background-color: #f7f6f3;
    }
    /* Cards blancas */
    div[data-testid="stMetric"],
    div.stAlert,
    div.stInfo,
    div.stSuccess,
    div.stWarning,
    div.stError,
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    /* Métricas */
    [data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        padding: 20px 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    [data-testid="stMetric"] label {
        color: #6b7280;
        font-size: 0.85rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #111827;
        font-size: 1.8rem;
        font-weight: 700;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.85rem;
    }
    /* Botón primario */
    .stButton > button {
        background-color: #4f46e5;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.15s;
    }
    .stButton > button:hover {
        background-color: #4338ca;
        color: white;
        box-shadow: 0 2px 8px rgba(79,70,229,0.25);
    }
    /* File uploader */
    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 12px;
        padding: 8px;
        border: 2px dashed #e2e1dd;
        transition: border-color 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #4f46e5;
    }
    /* Headers */
    h1, h2, h3 {
        color: #111827;
    }
    h1 {
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    h2 {
        font-size: 1.3rem;
        font-weight: 600;
        margin-top: 1.5rem;
    }
    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        color: #6b7280;
    }
    .stTabs [aria-selected="true"] {
        color: #4f46e5;
        font-weight: 600;
    }
    /* DataFrame */
    [data-testid="stDataFrame"] {
        background: white;
        border-radius: 12px;
        padding: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    /* Divider */
    hr {
        border-color: #e2e1dd;
        margin: 1.5rem 0;
    }
    /* Footer badge */
    .footer-badge {
        text-align: center;
        color: #9ca3af;
        font-size: 0.75rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #e2e1dd;
    }
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #faf9f7;
        border-right: 1px solid #e2e1dd;
    }
    section[data-testid="stSidebar"] .stMarkdown {
        color: #374151;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Lógica de auditoría (reescrita para pandas)
# ─────────────────────────────────────────────

COL_SKU_CANDIDATES = ['sku', 'codigo', 'código', 'cod', 'producto', 'id',
                       'codigo_producto', 'código_producto', 'articulo',
                       'artículo', 'sku_producto']
COL_QTY_CANDIDATES = ['cantidad', 'stock', 'existencia', 'existencias',
                       'unidades', 'qty', 'cant', 'inv', 'inventario',
                       'saldo', 'cantidad_existente']


def detectar_columna(df: pd.DataFrame, candidates: list[str], fallback_idx: int = 0) -> str:
    """Busca la primera columna del df que coincida con los candidatos."""
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for c in candidates:
        if c in cols_lower:
            return cols_lower[c]
    # Fallback: usar la columna en posición fallback_idx
    return df.columns[fallback_idx]


def parse_cantidad(val) -> int:
    """Convierte a entero tolerando formatos argentinos."""
    if val is None:
        return 0
    v = str(val).strip()
    if not v:
        return 0
    # Sacar puntos de miles
    v = v.replace('.', '').replace(',', '.')
    try:
        return int(float(v))
    except ValueError:
        return 0


@st.cache_data(show_spinner="🔎 Analizando inventarios...")
def ejecutar_auditoria(df_fisico: pd.DataFrame, df_central: pd.DataFrame,
                       sku_col_f: str, qty_col_f: str,
                       sku_col_c: str, qty_col_c: str) -> dict:
    """Ejecuta la comparación y devuelve resultados estructurados."""

    # Preparar datos
    f = df_fisico[[sku_col_f, qty_col_f]].copy()
    f.columns = ['sku', 'cantidad']
    f['cantidad'] = f['cantidad'].apply(parse_cantidad)
    f = f.groupby('sku', as_index=False)['cantidad'].sum()

    c = df_central[[sku_col_c, qty_col_c]].copy()
    c.columns = ['sku', 'cantidad']
    c['cantidad'] = c['cantidad'].apply(parse_cantidad)
    c = c.groupby('sku', as_index=False)['cantidad'].sum()

    # Indexar
    fisico_dict = dict(zip(f['sku'], f['cantidad']))
    central_dict = dict(zip(c['sku'], c['cantidad']))

    todos_skus = sorted(set(fisico_dict) | set(central_dict))

    coinciden = []
    sobrantes = []
    faltantes = []
    solo_fisico = []
    solo_central = []

    total_f = 0
    total_c = 0

    for sku in todos_skus:
        qf = fisico_dict.get(sku, 0)
        qc = central_dict.get(sku, 0)
        total_f += qf
        total_c += qc
        diff = qf - qc

        if sku not in central_dict:
            solo_fisico.append({'SKU': sku, 'Cantidad Físico': qf})
        elif sku not in fisico_dict:
            solo_central.append({'SKU': sku, 'Cantidad Central': qc})
        elif diff == 0:
            coinciden.append({'SKU': sku, 'Cantidad': qf})
        elif diff > 0:
            sobrantes.append({'SKU': sku, 'Físico': qf, 'Central': qc, 'Diferencia': diff})
        else:
            faltantes.append({'SKU': sku, 'Físico': qf, 'Central': qc, 'Diferencia': diff})

    n_total = len(todos_skus)
    n_ok = len(coinciden)
    pct = (n_ok / n_total * 100) if n_total else 0

    if pct >= 95:
        verdict = ("✅", "APROBADA", "Sin diferencias significativas.")
    elif pct >= 80:
        verdict = ("⚠️", "OBSERVADA", "Revisar diferencias detectadas.")
    else:
        verdict = ("🔴", "RECHAZADA", "Requiere investigación.")

    return {
        'stats': {
            'total_sku': n_total,
            'coinciden': n_ok,
            'diferencias': len(sobrantes) + len(faltantes),
            'sobrantes': len(sobrantes),
            'faltantes': len(faltantes),
            'solo_fisico': len(solo_fisico),
            'solo_central': len(solo_central),
            'total_fisico': total_f,
            'total_central': total_c,
            'diferencia_neta': total_f - total_c,
            'pct_coincidencia': round(pct, 1),
            'veredicto_icono': verdict[0],
            'veredicto': verdict[1],
            'veredicto_msg': verdict[2],
        },
        'tablas': {
            'coinciden': pd.DataFrame(coinciden) if coinciden else pd.DataFrame(),
            'sobrantes': pd.DataFrame(sobrantes) if sobrantes else pd.DataFrame(),
            'faltantes': pd.DataFrame(faltantes) if faltantes else pd.DataFrame(),
            'solo_fisico': pd.DataFrame(solo_fisico) if solo_fisico else pd.DataFrame(),
            'solo_central': pd.DataFrame(solo_central) if solo_central else pd.DataFrame(),
        },
        'fisico_dict': fisico_dict,
        'central_dict': central_dict,
    }


def generar_reporte_txt(resultado: dict, sucursal: str = "") -> str:
    """Genera reporte en texto plano."""
    s = resultado['stats']
    lines = []
    lines.append("=" * 64)
    lines.append("  REPORTE DE AUDITORÍA DE INVENTARIO")
    if sucursal:
        lines.append(f"  Sucursal: {sucursal}")
    lines.append(f"  Fecha: {datetime.now():%Y-%m-%d %H:%M}")
    lines.append("=" * 64)
    lines.append("")
    lines.append("📊  RESUMEN")
    lines.append("-" * 40)
    lines.append(f"  SKU únicos analizados:    {s['total_sku']:>6}")
    lines.append(f"  Coinciden (sin diff):     {s['coinciden']:>6}  ({s['pct_coincidencia']}%)")
    lines.append(f"  Con diferencias:           {s['diferencias']:>6}")
    lines.append(f"  → Sobrantes:               {s['sobrantes']:>6}")
    lines.append(f"  → Faltantes:               {s['faltantes']:>6}")
    lines.append(f"  Solo en físico:            {s['solo_fisico']:>6}")
    lines.append(f"  Solo en central:           {s['solo_central']:>6}")
    lines.append("")
    lines.append(f"  Total unidades físicas:    {s['total_fisico']:>8}")
    lines.append(f"  Total unidades central:    {s['total_central']:>8}")
    lines.append(f"  Diferencia neta:           {s['diferencia_neta']:>8}")
    lines.append("")
    lines.append(f"  VEREDICTO: {s['veredicto_icono']} {s['veredicto']} — {s['veredicto_msg']}")
    lines.append("")

    def fmt_tabla(titulo, df, cols):
        if df.empty:
            return
        lines.append(f"{titulo}")
        lines.append("-" * 64)
        headers = "  ".join(f"{c:<20}" for c in cols)
        lines.append(f"  {headers}")
        lines.append("  " + "-" * (len(cols) * 22))
        for _, row in df.iterrows():
            vals = "  ".join(f"{str(row[c]):<20}" for c in cols)
            lines.append(f"  {vals}")
        lines.append("")

    t = resultado['tablas']
    fmt_tabla("🔴  FALTANTES", t['faltantes'], ['SKU', 'Físico', 'Central', 'Diferencia'])
    fmt_tabla("🟡  SOBRANTES", t['sobrantes'], ['SKU', 'Físico', 'Central', 'Diferencia'])
    fmt_tabla("❓  EN FÍSICO — NO EN CENTRAL", t['solo_fisico'], ['SKU', 'Cantidad Físico'])
    fmt_tabla("❓  EN CENTRAL — NO EN FÍSICO", t['solo_central'], ['SKU', 'Cantidad Central'])

    lines.append("")
    lines.append("=" * 64)
    lines.append("")
    lines.append("  Auditor: ___________________________")
    lines.append("  Fecha:   ___________________________")
    lines.append("")
    return "\n".join(lines)


def guardar_historial(resultado: dict, sucursal: str, archivo_f: str, archivo_c: str):
    """Guarda un registro de la auditoría en un JSON acumulativo."""
    hist_path = Path(st.session_state.get('historial_path', 'auditorias_historial.json'))
    registro = {
        'fecha': datetime.now().isoformat(),
        'sucursal': sucursal,
        'archivo_fisico': archivo_f,
        'archivo_central': archivo_c,
        'stats': resultado['stats'],
    }
    if hist_path.exists():
        with open(hist_path, 'r', encoding='utf-8') as f:
            historial = json.load(f)
    else:
        historial = []
    historial.append(registro)
    with open(hist_path, 'w', encoding='utf-8') as f:
        json.dump(historial, f, indent=2, ensure_ascii=False)


# ─────────────────────────────────────────────
#  UI
# ─────────────────────────────────────────────

st.markdown(
    "<h1 style='display: flex; align-items: center; gap: 10px;'>"
    "📦 Auditoría de Inventarios</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color: #6b7280; margin-top: -4px;'>"
    "Compará el conteo <b>físico</b> de una sucursal contra el <b>stock del sistema central</b>.</p>",
    unsafe_allow_html=True,
)

# ─── Generar CSVs de ejemplo ───

@st.cache_data
def generar_ejemplo_fisico() -> str:
    """Genera un CSV de ejemplo para conteo físico."""
    import pandas as pd
    data = {
        'sku': ['LAP-001', 'LAP-002', 'MON-001', 'TEC-001', 'TEC-002',
                'MOU-001', 'MOU-002', 'AUD-001', 'WEB-001', 'WEB-002',
                'CAB-001', 'DIS-001'],
        'cantidad': [5, 3, 12, 20, 15,
                     8, 6, 10, 4, 7,
                     3, 9],
    }
    return pd.DataFrame(data).to_csv(index=False)


@st.cache_data
def generar_ejemplo_central() -> str:
    """Genera un CSV de ejemplo para stock central (con diferencias)."""
    data = {
        'sku': ['LAP-001', 'LAP-002', 'MON-001', 'TEC-001', 'TEC-002',
                'MOU-001', 'MOU-002', 'AUD-001', 'WEB-001', 'WEB-002',
                'CAB-001', 'CAB-002', 'DIS-001', 'DIS-002'],
        'cantidad': [5, 5, 12, 18, 15,
                     8, 4, 12, 4, 10,
                     3, 6, 10, 4],
    }
    return pd.DataFrame(data).to_csv(index=False)


# ─── Sidebar: instrucciones + ejemplos ───
with st.sidebar:
    st.markdown("### 🧾 ¿Cómo funciona?")
    st.markdown("""
1. **Subí los dos archivos CSV** — el conteo físico de la sucursal y el stock del sistema central.
2. **Confirmá las columnas** — SKU y cantidad se detectan solas, pero podés cambiarlas.
3. **Ejecutá la auditoría** — al instante ves el resultado.
4. **Descargá el reporte** — en texto plano o CSV con las diferencias.

---
**Formato esperado:**

Los CSVs deben tener al menos:
- Una columna con el **código SKU** del producto
- Una columna con la **cantidad**

Soportamos formatos argentinos (puntos de miles).
""")

    st.markdown("---")
    st.markdown("### 📥 Descargar ejemplos")
    st.markdown(
        "<p style='color: #6b7280; font-size: 0.85rem;'>"
        "Probá la app con estos archivos de muestra:</p>",
        unsafe_allow_html=True,
    )

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.download_button(
            "📋 Físico",
            data=generar_ejemplo_fisico(),
            file_name="ejemplo_conteo_fisico.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_e2:
        st.download_button(
            "💻 Central",
            data=generar_ejemplo_central(),
            file_name="ejemplo_stock_central.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown(
        "<p style='color: #9ca3af; font-size: 0.78rem;'>"
        "Los ejemplos ya tienen diferencias preparadas para que veas "
        "cómo funciona la auditoría.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        "<p style='color: #9ca3af; font-size: 0.8rem;'>"
        "v1.0 — Agente de Auditoría</p>",
        unsafe_allow_html=True,
    )

# ─── Uploaders ───
col1, col2 = st.columns(2)

with col1:
    fisico_file = st.file_uploader(
        "📋 **Conteo FÍSICO**",
        type=['csv', 'txt'],
        help="CSV con el conteo real de la sucursal (SKU + cantidad)",
    )

with col2:
    central_file = st.file_uploader(
        "💻 **Stock CENTRAL**",
        type=['csv', 'txt'],
        help="CSV con el stock del sistema central (SKU + cantidad)",
    )

# ─── Sesión para mantener sucursal ───
if 'sucursal' not in st.session_state:
    st.session_state.sucursal = ""
if 'historial_path' not in st.session_state:
    st.session_state.historial_path = str(Path.home() / ".auditoria_inventarios_historial.json")

# ─── Procesar si hay ambos archivos ───
if fisico_file is not None and central_file is not None:
    # Leer CSVs
    try:
        df_fisico = pd.read_csv(fisico_file, dtype=str)
        df_central = pd.read_csv(central_file, dtype=str)
    except Exception as e:
        st.error(f"❌ Error al leer los CSVs: {e}")
        st.stop()

    # Validar que no estén vacíos
    if df_fisico.empty:
        st.error("❌ El archivo de conteo físico está vacío.")
        st.stop()
    if df_central.empty:
        st.error("❌ El archivo de stock central está vacío.")
        st.stop()

    # ─── Detectar columnas ───
    sku_col_f = detectar_columna(df_fisico, COL_SKU_CANDIDATES)
    qty_col_f = detectar_columna(df_fisico, COL_QTY_CANDIDATES, fallback_idx=1)
    sku_col_c = detectar_columna(df_central, COL_SKU_CANDIDATES)
    qty_col_c = detectar_columna(df_central, COL_QTY_CANDIDATES, fallback_idx=1)

    # ─── Preview + configuración de columnas ───
    st.markdown("---")
    st.markdown("### 📋 Vistazo de los datos")

    tab1, tab2 = st.tabs(["📋 Conteo Físico", "💻 Stock Central"])

    with tab1:
        st.dataframe(df_fisico.head(10), use_container_width=True, hide_index=True)
        st.caption(f"{len(df_fisico)} filas • Columnas: {', '.join(df_fisico.columns)}")

    with tab2:
        st.dataframe(df_central.head(10), use_container_width=True, hide_index=True)
        st.caption(f"{len(df_central)} filas • Columnas: {', '.join(df_central.columns)}")

    # ─── Columna mapping ───
    st.markdown("### ⚙️ Columnas para la comparación")
    st.caption("Si la detección automática no es correcta, ajustalas manualmente.")

    col_a, col_b, col_c, col_d = st.columns(4)

    with col_a:
        sku_f = st.selectbox("SKU (físico)", df_fisico.columns,
                              index=list(df_fisico.columns).index(sku_col_f))
    with col_b:
        qty_f = st.selectbox("Cantidad (físico)", df_fisico.columns,
                              index=list(df_fisico.columns).index(qty_col_f))
    with col_c:
        sku_c = st.selectbox("SKU (central)", df_central.columns,
                              index=list(df_central.columns).index(sku_col_c))
    with col_d:
        qty_c = st.selectbox("Cantidad (central)", df_central.columns,
                              index=list(df_central.columns).index(qty_col_c))

    # ─── Sucursal ───
    st.markdown("### 🏪 Sucursal")
    sucursal = st.text_input("Nombre de la sucursal (opcional, para el reporte)",
                              value=st.session_state.sucursal,
                              placeholder="Ej: Sucursal Centro")
    st.session_state.sucursal = sucursal

    # ─── Botón ejecutar ───
    st.markdown("---")
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        ejecutar = st.button("▶️  Ejecutar Auditoría", type="primary", use_container_width=True)

    if ejecutar:
        resultado = ejecutar_auditoria(
            df_fisico, df_central,
            sku_f, qty_f, sku_c, qty_c
        )

        s = resultado['stats']

        # Guardar historial
        guardar_historial(resultado, sucursal, fisico_file.name, central_file.name)

        # ─── VEREDICTO ───
        ver_color = {"APROBADA": "green", "OBSERVADA": "orange", "RECHAZADA": "red"}
        vcolor = ver_color.get(s['veredicto'], "gray")
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 20px;
                    border-left: 5px solid {vcolor};
                    box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 20px;">
            <span style="font-size: 1.5rem;">{s['veredicto_icono']}</span>
            <span style="font-size: 1.3rem; font-weight: 700; color: {vcolor};">
                {s['veredicto']}
            </span>
            <span style="color: #6b7280; margin-left: 8px;">— {s['veredicto_msg']}</span>
        </div>
        """, unsafe_allow_html=True)

        # ─── Métricas principales ───
        st.markdown("### 📊 Resumen")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("SKU Analizados", s['total_sku'])
        m2.metric("Coinciden", f"{s['coinciden']} ({s['pct_coincidencia']}%)")
        m3.metric("Con Diferencias", s['diferencias'],
                  delta=f"+{s['sobrantes']} sobr / -{s['faltantes']} falt")
        m4.metric("Diferencia Neta (uds)", s['diferencia_neta'])

        m5, m6, m7, m8 = st.columns(4)
        m5.metric("Total Unid. Físico", f"{s['total_fisico']:,}")
        m6.metric("Total Unid. Central", f"{s['total_central']:,}")
        m7.metric("Solo en Físico", s['solo_fisico'])
        m8.metric("Solo en Central", s['solo_central'])

        # ─── Tablas de detalle ───
        tabs = resultado['tablas']

        if not tabs['faltantes'].empty:
            st.markdown("### 🔴 Faltantes (stock central > conteo físico)")
            st.dataframe(
                tabs['faltantes'].style.applymap(
                    lambda _: 'color: #dc2626; font-weight: 600;',
                    subset=['Diferencia'],
                ),
                use_container_width=True, hide_index=True,
            )

        if not tabs['sobrantes'].empty:
            st.markdown("### 🟡 Sobrantes (conteo físico > stock central)")
            st.dataframe(
                tabs['sobrantes'].style.applymap(
                    lambda _: 'color: #d97706; font-weight: 600;',
                    subset=['Diferencia'],
                ),
                use_container_width=True, hide_index=True,
            )

        if not tabs['solo_fisico'].empty:
            st.markdown("### ❓ En físico, no registrados en central")
            st.dataframe(tabs['solo_fisico'], use_container_width=True, hide_index=True)

        if not tabs['solo_central'].empty:
            st.markdown("### ❓ En central, no registrados en físico")
            st.dataframe(tabs['solo_central'], use_container_width=True, hide_index=True)

        if not tabs['coinciden'].empty:
            with st.expander(f"✅ Productos que coinciden ({len(tabs['coinciden'])})"):
                st.dataframe(tabs['coinciden'], use_container_width=True, hide_index=True)

        # ─── Exportación ───
        st.markdown("### 💾 Exportar resultados")

        reporte_txt = generar_reporte_txt(resultado, sucursal)

        # Generar CSV de diferencias
        diffs_rows = []
        for _, row in tabs['faltantes'].iterrows():
            diffs_rows.append({**row.to_dict(), 'Tipo': 'FALTANTE'})
        for _, row in tabs['sobrantes'].iterrows():
            diffs_rows.append({**row.to_dict(), 'Tipo': 'SOBRANTE'})
        for _, row in tabs['solo_fisico'].iterrows():
            diffs_rows.append({'SKU': row['SKU'], 'Físico': row['Cantidad Físico'],
                               'Central': 0, 'Diferencia': row['Cantidad Físico'],
                               'Tipo': 'SOLO_FISICO'})
        for _, row in tabs['solo_central'].iterrows():
            diffs_rows.append({'SKU': row['SKU'], 'Físico': 0,
                               'Central': row['Cantidad Central'],
                               'Diferencia': -row['Cantidad Central'],
                               'Tipo': 'SOLO_CENTRAL'})

        df_difs = pd.DataFrame(diffs_rows) if diffs_rows else pd.DataFrame()
        csv_difs = df_difs.to_csv(index=False) if not df_difs.empty else ""

        base_name = f"auditoria_{sucursal or 'sucursal'}_{datetime.now():%Y%m%d_%H%M%S}"

        col_d1, col_d2, col_d3 = st.columns(3)
        with col_d1:
            st.download_button(
                "📄 Descargar Reporte (.txt)",
                data=reporte_txt,
                file_name=f"{base_name}.txt",
                mime="text/plain",
                use_container_width=True,
            )
        with col_d2:
            if csv_difs:
                st.download_button(
                    "📊 Descargar Diferencias (.csv)",
                    data=csv_difs,
                    file_name=f"{base_name}_diferencias.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
        with col_d3:
            st.download_button(
                "📋 Descargar Datos completos (.csv)",
                data=pd.concat([
                    tabs['coinciden'].assign(Tipo='COINCIDE') if not tabs['coinciden'].empty else pd.DataFrame(),
                    tabs['faltantes'].assign(Tipo='FALTANTE') if not tabs['faltantes'].empty else pd.DataFrame(),
                    tabs['sobrantes'].assign(Tipo='SOBRANTE') if not tabs['sobrantes'].empty else pd.DataFrame(),
                    tabs['solo_fisico'].assign(Tipo='SOLO_FISICO') if not tabs['solo_fisico'].empty else pd.DataFrame(),
                    tabs['solo_central'].assign(Tipo='SOLO_CENTRAL') if not tabs['solo_central'].empty else pd.DataFrame(),
                ], ignore_index=True).to_csv(index=False),
                file_name=f"{base_name}_completo.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # ─── Nota final ───
        st.markdown("")
        if s['veredicto'] in ("APROBADA",):
            st.success(
                "✅ No se detectaron diferencias que requieran acción. "
                "Podés firmar el reporte y archivar."
            )
        elif s['veredicto'] == "OBSERVADA":
            st.warning(
                "⚠️ Revisá las diferencias marcadas. Si corresponden a errores "
                "de carga o movimientos no registrados, ajustá el stock central."
            )
        else:
            st.error(
                "🔴 Se detectaron diferencias significativas. Se recomienda "
                "realizar un recuento físico de los productos conflictivos "
                "antes de ajustar el sistema."
            )

else:
    # ─── Estado inicial (sin archivos) ───
    st.markdown("")
    st.info(
        "👆 Subí los dos archivos CSV para comenzar la auditoría.\n\n"
        "**Formato:** cada archivo debe tener al menos una columna de SKU "
        "y una columna de cantidad. El sistema detecta las columnas "
        "automáticamente."
    )

    # ─── Botones de ejemplo en la pantalla principal ───
    st.markdown("### 📥 ¿No tenés archivos a mano?")
    st.markdown(
        "<p style='color: #6b7280;'>"
        "Descargá estos archivos de ejemplo y probá la app:</p>",
        unsafe_allow_html=True,
    )

    col_ej1, col_ej2, col_ej3 = st.columns([1, 1, 2])
    with col_ej1:
        st.download_button(
            "📋 Descargar ejemplo — Conteo FÍSICO",
            data=generar_ejemplo_fisico(),
            file_name="ejemplo_conteo_fisico.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_ej2:
        st.download_button(
            "💻 Descargar ejemplo — Stock CENTRAL",
            data=generar_ejemplo_central(),
            file_name="ejemplo_stock_central.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with col_ej3:
        st.markdown(
            "<p style='color: #9ca3af; font-size: 0.85rem; padding-top: 6px;'>"
            "Los ejemplos ya incluyen diferencias preparadas "
            "para que veas cómo funciona la auditoría.</p>",
            unsafe_allow_html=True,
        )

    # ─── Últimas auditorías ───
    hist_path = Path(st.session_state.historial_path)
    if hist_path.exists():
        try:
            with open(hist_path, 'r') as f:
                historial = json.load(f)
            if historial:
                st.markdown("---")
                st.markdown("### 🕐 Últimas auditorías realizadas")
                for h in reversed(historial[-5:]):
                    s = h['stats']
                    st.markdown(
                        f"**{s['veredicto_icono']} {h.get('sucursal', '—')}** "
                        f"— {s['coinciden']}/{s['total_sku']} OK ({s['pct_coincidencia']}%) "
                        f"· {h['fecha'][:10]}"
                    )
        except Exception:
            pass

# ─── Footer ───
st.markdown(
    '<div class="footer-badge">'
    'Agente de Auditoría de Inventarios · Hecho con Streamlit</div>',
    unsafe_allow_html=True,
)
