#!/usr/bin/env python3
"""
Auditoría de Inventarios — Streamlit App
=========================================
Compara conteo físico de sucursal vs. stock del sistema central.
Con memoria persistente: guarda cada auditoría en SQLite y permite
consultar el historial completo en cualquier momento.

Uso:
  python3 -m streamlit run auditoria_app.py
"""

import streamlit as st
import pandas as pd
import csv
import os
import json
import sqlite3
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
    .stApp { background-color: #f7f6f3; }
    .main > div { background-color: #f7f6f3; }
    div[data-testid="stMetric"],
    div.stAlert, div.stInfo, div.stSuccess,
    div.stWarning, div.stError,
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
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
    .stButton > button[data-secondary="true"] {
        background-color: transparent;
        color: #4f46e5;
        border: 1px solid #d1d5db;
    }
    .stButton > button[data-secondary="true"]:hover {
        border-color: #4f46e5;
    }
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
    h1, h2, h3 { color: #111827; }
    h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.2rem; }
    h2 { font-size: 1.3rem; font-weight: 600; margin-top: 1.5rem; }
    .stTabs [data-baseweb="tab"] { font-weight: 500; color: #6b7280; }
    .stTabs [aria-selected="true"] { color: #4f46e5; font-weight: 600; }
    [data-testid="stDataFrame"] {
        background: white;
        border-radius: 12px;
        padding: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    hr { border-color: #e2e1dd; margin: 1.5rem 0; }
    .footer-badge {
        text-align: center;
        color: #9ca3af;
        font-size: 0.75rem;
        margin-top: 3rem;
        padding-top: 1rem;
        border-top: 1px solid #e2e1dd;
    }
    section[data-testid="stSidebar"] {
        background-color: #faf9f7;
        border-right: 1px solid #e2e1dd;
    }
    section[data-testid="stSidebar"] .stMarkdown { color: #374151; }
    /* Sucursal cards */
    .sucursal-card {
        background: white;
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        transition: all 0.15s;
        cursor: pointer;
        border: 1px solid #e8e7e4;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .sucursal-card:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.08);
        border-color: #c7c5c0;
        transform: translateY(-1px);
    }
    .sucursal-card .nombre {
        font-size: 1.1rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .sucursal-card .nombre .badge-count {
        background: #4f46e5;
        color: white;
        font-size: 0.75rem;
        font-weight: 600;
        padding: 1px 10px;
        border-radius: 20px;
    }
    .sucursal-card .meta {
        color: #9ca3af;
        font-size: 0.82rem;
        margin-bottom: 10px;
    }
    .sucursal-card .stats-row {
        display: flex;
        gap: 16px;
        margin-top: auto;
        padding-top: 10px;
        border-top: 1px solid #f0efec;
    }
    .sucursal-card .stat-item {
        text-align: center;
        flex: 1;
    }
    .sucursal-card .stat-item .num {
        font-size: 1.2rem;
        font-weight: 700;
        color: #111827;
    }
    .sucursal-card .stat-item .label {
        font-size: 0.7rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .sucursal-card .stat-item .num.aprobada { color: #16a34a; }
    .sucursal-card .stat-item .num.observada { color: #d97706; }
    .sucursal-card .stat-item .num.rechazada { color: #dc2626; }
    /* Timeline */
    .timeline-item {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin-bottom: 8px;
        border-left: 4px solid #d1d5db;
        transition: box-shadow 0.15s;
    }
    .timeline-item:hover {
        box-shadow: 0 3px 12px rgba(0,0,0,0.08);
    }
    .timeline-item.aprobada { border-left-color: #16a34a; }
    .timeline-item.observada { border-left-color: #d97706; }
    .timeline-item.rechazada { border-left-color: #dc2626; }
    .timeline-item .tl-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .timeline-item .tl-fecha {
        color: #9ca3af;
        font-size: 0.82rem;
    }
    .timeline-item .tl-veredicto {
        font-weight: 600;
        font-size: 0.9rem;
    }
    .timeline-item .tl-stats {
        color: #6b7280;
        font-size: 0.85rem;
        margin-top: 4px;
    }
    .timeline-item .tl-actions {
        display: flex;
        gap: 6px;
        margin-top: 8px;
    }
    div[data-testid="stExpander"] {
        background: white;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        border: none;
    }
    .historial-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        margin-bottom: 10px;
        cursor: pointer;
        transition: box-shadow 0.15s;
        border-left: 4px solid transparent;
    }
    .historial-card:hover {
        box-shadow: 0 3px 12px rgba(0,0,0,0.1);
    }
    .historial-card.aprobada { border-left-color: #16a34a; }
    .historial-card.observada { border-left-color: #d97706; }
    .historial-card.rechazada { border-left-color: #dc2626; }
    .historial-fecha { color: #9ca3af; font-size: 0.82rem; }
    .historial-sucursal { font-weight: 600; color: #111827; font-size: 1rem; }
    .historial-stats { color: #6b7280; font-size: 0.85rem; }
    .delete-btn {
        background: none;
        border: none;
        color: #dc2626;
        cursor: pointer;
        font-size: 0.85rem;
        padding: 4px 8px;
        border-radius: 6px;
    }
    .delete-btn:hover {
        background: #fef2f2;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  Base de datos SQLite (memoria persistente)
# ─────────────────────────────────────────────

DB_PATH = str(Path.home() / ".auditoria_inventarios.db")


def get_db() -> sqlite3.Connection:
    """Devuelve conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    """Crea las tablas si no existen."""
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS auditorias (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha           TEXT NOT NULL,
            sucursal        TEXT DEFAULT '',
            archivo_fisico  TEXT DEFAULT '',
            archivo_central TEXT DEFAULT '',
            total_sku       INTEGER DEFAULT 0,
            coinciden       INTEGER DEFAULT 0,
            diferencias     INTEGER DEFAULT 0,
            sobrantes       INTEGER DEFAULT 0,
            faltantes       INTEGER DEFAULT 0,
            solo_fisico     INTEGER DEFAULT 0,
            solo_central    INTEGER DEFAULT 0,
            total_unid_fis  INTEGER DEFAULT 0,
            total_unid_cen  INTEGER DEFAULT 0,
            diferencia_neta INTEGER DEFAULT 0,
            pct_coincidencia REAL DEFAULT 0,
            veredicto       TEXT DEFAULT '',
            csv_fisico      TEXT DEFAULT '',
            csv_central     TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS diferencias (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            audit_id        INTEGER NOT NULL,
            sku             TEXT NOT NULL,
            tipo            TEXT NOT NULL,
            cantidad_fisico INTEGER DEFAULT 0,
            cantidad_central INTEGER DEFAULT 0,
            diferencia      INTEGER DEFAULT 0,
            FOREIGN KEY (audit_id) REFERENCES auditorias(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_diferencias_audit
            ON diferencias(audit_id);
        CREATE INDEX IF NOT EXISTS idx_auditorias_fecha
            ON auditorias(fecha DESC);
        CREATE INDEX IF NOT EXISTS idx_auditorias_sucursal
            ON auditorias(sucursal);
    """)
    conn.commit()
    conn.close()


def guardar_auditoria(resultado: dict, sucursal: str,
                      archivo_f: str, archivo_c: str,
                      csv_fisico_raw: str, csv_central_raw: str) -> int:
    """Guarda la auditoría completa en SQLite. Devuelve el ID."""
    s = resultado['stats']
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO auditorias
            (fecha, sucursal, archivo_fisico, archivo_central,
             total_sku, coinciden, diferencias, sobrantes, faltantes,
             solo_fisico, solo_central,
             total_unid_fis, total_unid_cen, diferencia_neta,
             pct_coincidencia, veredicto,
             csv_fisico, csv_central)
        VALUES (?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?)
    """, (
        datetime.now().isoformat(),
        sucursal,
        archivo_f,
        archivo_c,
        s['total_sku'],
        s['coinciden'],
        s['diferencias'],
        s['sobrantes'],
        s['faltantes'],
        s['solo_fisico'],
        s['solo_central'],
        s['total_fisico'],
        s['total_central'],
        s['diferencia_neta'],
        s['pct_coincidencia'],
        s['veredicto'],
        csv_fisico_raw,
        csv_central_raw,
    ))
    audit_id = cur.lastrowid

    # Guardar diferencias
    rows = []
    t = resultado['tablas']
    for _, row in t['faltantes'].iterrows():
        rows.append((audit_id, row['SKU'], 'FALTANTE',
                     int(row['Físico']), int(row['Central']), int(row['Diferencia'])))
    for _, row in t['sobrantes'].iterrows():
        rows.append((audit_id, row['SKU'], 'SOBRANTE',
                     int(row['Físico']), int(row['Central']), int(row['Diferencia'])))
    for _, row in t['solo_fisico'].iterrows():
        rows.append((audit_id, row['SKU'], 'SOLO_FISICO',
                     int(row['Cantidad Físico']), 0, int(row['Cantidad Físico'])))
    for _, row in t['solo_central'].iterrows():
        rows.append((audit_id, row['SKU'], 'SOLO_CENTRAL',
                     0, int(row['Cantidad Central']), -int(row['Cantidad Central'])))
    for _, row in t['coinciden'].iterrows():
        rows.append((audit_id, row['SKU'], 'COINCIDE',
                     int(row['Cantidad']), int(row['Cantidad']), 0))

    if rows:
        conn.executemany("""
            INSERT INTO diferencias
                (audit_id, sku, tipo, cantidad_fisico, cantidad_central, diferencia)
            VALUES (?, ?, ?, ?, ?, ?)
        """, rows)

    conn.commit()
    conn.close()
    return audit_id


def listar_auditorias(limit: int = 50, sucursal_filtro: str = "",
                      veredicto_filtro: str = "") -> list:
    """Devuelve lista de auditorías con filtros opcionales."""
    conn = get_db()
    query = "SELECT * FROM auditorias"
    params = []
    condiciones = []
    if sucursal_filtro:
        condiciones.append("sucursal LIKE ?")
        params.append(f"%{sucursal_filtro}%")
    if veredicto_filtro:
        condiciones.append("veredicto = ?")
        params.append(veredicto_filtro)
    if condiciones:
        query += " WHERE " + " AND ".join(condiciones)
    query += " ORDER BY fecha DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def obtener_auditoria(audit_id: int) -> dict:
    """Devuelve una auditoría completa con sus diferencias."""
    conn = get_db()
    audit = conn.execute(
        "SELECT * FROM auditorias WHERE id = ?", (audit_id,)
    ).fetchone()
    if not audit:
        conn.close()
        return None
    diffs = conn.execute(
        "SELECT * FROM diferencias WHERE audit_id = ? ORDER BY tipo, sku",
        (audit_id,)
    ).fetchall()
    conn.close()
    return {
        'auditoria': dict(audit),
        'diferencias': [dict(d) for d in diffs],
    }


def eliminar_auditoria(audit_id: int):
    """Elimina una auditoría y sus diferencias (cascade)."""
    conn = get_db()
    conn.execute("DELETE FROM diferencias WHERE audit_id = ?", (audit_id,))
    conn.execute("DELETE FROM auditorias WHERE id = ?", (audit_id,))
    conn.commit()
    conn.close()


def estadisticas_generales() -> dict:
    """Devuelve estadísticas generales de todas las auditorías."""
    conn = get_db()
    r = conn.execute("""
        SELECT
            COUNT(*) as total_auditorias,
            COALESCE(SUM(total_sku), 0) as total_sku_auditados,
            COALESCE(SUM(diferencias), 0) as total_diferencias,
            COALESCE(AVG(pct_coincidencia), 0) as promedio_coincidencia,
            COUNT(CASE WHEN veredicto = 'APROBADA' THEN 1 END) as aprobadas,
            COUNT(CASE WHEN veredicto = 'OBSERVADA' THEN 1 END) as observadas,
            COUNT(CASE WHEN veredicto = 'RECHAZADA' THEN 1 END) as rechazadas,
            COUNT(DISTINCT sucursal) as sucursales_distintas
        FROM auditorias
    """).fetchone()
    conn.close()
    return dict(r)


def listar_sucursales() -> list:
    """Devuelve lista de sucursales con estadísticas resumidas."""
    conn = get_db()
    rows = conn.execute("""
        SELECT
            sucursal,
            COUNT(*) as total_auditorias,
            MAX(fecha) as ultima_fecha,
            ROUND(AVG(pct_coincidencia), 1) as promedio_coincidencia,
            MIN(pct_coincidencia) as peor_coincidencia,
            SUM(CASE WHEN veredicto = 'APROBADA' THEN 1 ELSE 0 END) as aprobadas,
            SUM(CASE WHEN veredicto = 'OBSERVADA' THEN 1 ELSE 0 END) as observadas,
            SUM(CASE WHEN veredicto = 'RECHAZADA' THEN 1 ELSE 0 END) as rechazadas
        FROM auditorias
        WHERE sucursal != ''
        GROUP BY sucursal
        ORDER BY ultima_fecha DESC
    """).fetchall()
    # También incluir las que no tienen sucursal
    orphans = conn.execute("""
        SELECT
            '(Sin sucursal)' as sucursal,
            COUNT(*) as total_auditorias,
            MAX(fecha) as ultima_fecha,
            ROUND(AVG(pct_coincidencia), 1) as promedio_coincidencia,
            MIN(pct_coincidencia) as peor_coincidencia,
            SUM(CASE WHEN veredicto = 'APROBADA' THEN 1 ELSE 0 END) as aprobadas,
            SUM(CASE WHEN veredicto = 'OBSERVADA' THEN 1 ELSE 0 END) as observadas,
            SUM(CASE WHEN veredicto = 'RECHAZADA' THEN 1 ELSE 0 END) as rechazadas
        FROM auditorias
        WHERE sucursal = ''
    """).fetchone()
    conn.close()
    resultado = [dict(r) for r in rows]
    if orphans and orphans['total_auditorias'] > 0:
        resultado.append(dict(orphans))
    return resultado


def auditorias_por_sucursal(sucursal: str) -> list:
    """Devuelve todas las auditorías de una sucursal, ordenadas por fecha."""
    if sucursal == '(Sin sucursal)':
        sucursal = ''
    conn = get_db()
    rows = conn.execute("""
        SELECT * FROM auditorias
        WHERE sucursal = ?
        ORDER BY fecha DESC
    """, (sucursal,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Inicializar base de datos al arrancar
init_db()

# ─────────────────────────────────────────────
#  Lógica de auditoría
# ─────────────────────────────────────────────

COL_SKU_CANDIDATES = ['sku', 'codigo', 'código', 'cod', 'producto', 'id',
                       'codigo_producto', 'código_producto', 'articulo',
                       'artículo', 'sku_producto']
COL_QTY_CANDIDATES = ['cantidad', 'stock', 'existencia', 'existencias',
                       'unidades', 'qty', 'cant', 'inv', 'inventario',
                       'saldo', 'cantidad_existente']


def detectar_columna(df: pd.DataFrame, candidates: list[str], fallback_idx: int = 0) -> str:
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for c in candidates:
        if c in cols_lower:
            return cols_lower[c]
    return df.columns[fallback_idx]


def parse_cantidad(val) -> int:
    if val is None:
        return 0
    v = str(val).strip()
    if not v:
        return 0
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
    f = df_fisico[[sku_col_f, qty_col_f]].copy()
    f.columns = ['sku', 'cantidad']
    f['cantidad'] = f['cantidad'].apply(parse_cantidad)
    f = f.groupby('sku', as_index=False)['cantidad'].sum()

    c = df_central[[sku_col_c, qty_col_c]].copy()
    c.columns = ['sku', 'cantidad']
    c['cantidad'] = c['cantidad'].apply(parse_cantidad)
    c = c.groupby('sku', as_index=False)['cantidad'].sum()

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


def reconstruir_resultado_desde_db(audit: dict, diffs: list) -> dict:
    """Reconstruye el dict 'resultado' desde los datos de la DB para mostrar en UI."""
    s = audit
    pct = s['pct_coincidencia']
    if pct >= 95:
        icono = "✅"
        texto = "APROBADA"
        msg = "Sin diferencias significativas."
    elif pct >= 80:
        icono = "⚠️"
        texto = "OBSERVADA"
        msg = "Revisar diferencias detectadas."
    else:
        icono = "🔴"
        texto = "RECHAZADA"
        msg = "Requiere investigación."

    stats = {
        'total_sku': s['total_sku'],
        'coinciden': s['coinciden'],
        'diferencias': s['diferencias'],
        'sobrantes': s['sobrantes'],
        'faltantes': s['faltantes'],
        'solo_fisico': s['solo_fisico'],
        'solo_central': s['solo_central'],
        'total_fisico': s['total_unid_fis'],
        'total_central': s['total_unid_cen'],
        'diferencia_neta': s['diferencia_neta'],
        'pct_coincidencia': pct,
        'veredicto_icono': icono,
        'veredicto': texto,
        'veredicto_msg': msg,
    }

    tablas = {
        'coinciden': pd.DataFrame(),
        'sobrantes': pd.DataFrame(),
        'faltantes': pd.DataFrame(),
        'solo_fisico': pd.DataFrame(),
        'solo_central': pd.DataFrame(),
    }

    coic, sob, falt, sf, sc = [], [], [], [], []
    for d in diffs:
        t = d['tipo']
        if t == 'COINCIDE':
            coic.append({'SKU': d['sku'], 'Cantidad': d['cantidad_fisico']})
        elif t == 'SOBRANTE':
            sob.append({'SKU': d['sku'], 'Físico': d['cantidad_fisico'],
                        'Central': d['cantidad_central'], 'Diferencia': d['diferencia']})
        elif t == 'FALTANTE':
            falt.append({'SKU': d['sku'], 'Físico': d['cantidad_fisico'],
                         'Central': d['cantidad_central'], 'Diferencia': d['diferencia']})
        elif t == 'SOLO_FISICO':
            sf.append({'SKU': d['sku'], 'Cantidad Físico': d['cantidad_fisico']})
        elif t == 'SOLO_CENTRAL':
            sc.append({'SKU': d['sku'], 'Cantidad Central': d['cantidad_central']})

    if coic:
        tablas['coinciden'] = pd.DataFrame(coic)
    if sob:
        tablas['sobrantes'] = pd.DataFrame(sob)
    if falt:
        tablas['faltantes'] = pd.DataFrame(falt)
    if sf:
        tablas['solo_fisico'] = pd.DataFrame(sf)
    if sc:
        tablas['solo_central'] = pd.DataFrame(sc)

    return {'stats': stats, 'tablas': tablas}


# ─────────────────────────────────────────────
#  Generar CSVs de ejemplo
# ─────────────────────────────────────────────

@st.cache_data
def generar_ejemplo_fisico() -> str:
    data = {
        'sku': ['LAP-001', 'LAP-002', 'MON-001', 'TEC-001', 'TEC-002',
                'MOU-001', 'MOU-002', 'AUD-001', 'WEB-001', 'WEB-002',
                'CAB-001', 'DIS-001'],
        'cantidad': [5, 3, 12, 20, 15, 8, 6, 10, 4, 7, 3, 9],
    }
    return pd.DataFrame(data).to_csv(index=False)


@st.cache_data
def generar_ejemplo_central() -> str:
    data = {
        'sku': ['LAP-001', 'LAP-002', 'MON-001', 'TEC-001', 'TEC-002',
                'MOU-001', 'MOU-002', 'AUD-001', 'WEB-001', 'WEB-002',
                'CAB-001', 'CAB-002', 'DIS-001', 'DIS-002'],
        'cantidad': [5, 5, 12, 18, 15, 8, 4, 12, 4, 10, 3, 6, 10, 4],
    }
    return pd.DataFrame(data).to_csv(index=False)


# ─────────────────────────────────────────────
#  Sidebar
# ─────────────────────────────────────────────

with st.sidebar:
    st.markdown("### 🧾 ¿Cómo funciona?")
    st.markdown("""
1. **Subí los dos archivos CSV** — el conteo físico de la sucursal y el stock del sistema central.
2. **Confirmá las columnas** — SKU y cantidad se detectan solas, pero podés cambiarlas.
3. **Ejecutá la auditoría** — al instante ves el resultado.
4. **Consultá el historial** — todas las auditorías quedan guardadas.
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
        "Los ejemplos ya tienen diferencias preparadas.</p>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Estadísticas generales
    est = estadisticas_generales()
    if est['total_auditorias'] > 0:
        st.markdown("### 📊 Estadísticas generales")
        st.markdown(
            f"<p style='color: #6b7280; font-size: 0.85rem;'>"
            f"Auditorías: <b>{est['total_auditorias']}</b> &nbsp;·&nbsp; "
            f"SKU auditados: <b>{est['total_sku_auditados']:,}</b><br>"
            f"✅ {est['aprobadas']} · ⚠️ {est['observadas']} · 🔴 {est['rechazadas']}<br>"
            f"Promedio: <b>{est['promedio_coincidencia']:.1f}%</b></p>",
            unsafe_allow_html=True,
        )
        st.markdown("---")

    st.markdown(
        "<p style='color: #9ca3af; font-size: 0.8rem;'>"
        "v2.0 — Con memoria SQLite</p>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
#  Navegación principal
# ─────────────────────────────────────────────

# Inicializar session state
if 'pagina' not in st.session_state:
    st.session_state.pagina = 'nueva'
if 'audit_id_ver' not in st.session_state:
    st.session_state.audit_id_ver = None
if 'sucursal_ver' not in st.session_state:
    st.session_state.sucursal_ver = None

# Título
st.markdown(
    "<h1 style='display: flex; align-items: center; gap: 10px;'>"
    "📦 Auditoría de Inventarios</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='color: #6b7280; margin-top: -4px;'>"
    "Compará el conteo <b>físico</b> contra el <b>stock central</b>.</p>",
    unsafe_allow_html=True,
)

# ─── Pestañas de navegación ───
tabs = st.tabs(["➕ Nueva Auditoría", "📋 Historial"])

# ─────────────────────────────────────────────
#  TAB 1: Nueva Auditoría
# ─────────────────────────────────────────────

with tabs[0]:
    # Uploaders
    col1, col2 = st.columns(2)
    with col1:
        fisico_file = st.file_uploader(
            "📋 **Conteo FÍSICO**",
            type=['csv', 'txt'],
            key="fisico_uploader",
            help="CSV con el conteo real de la sucursal (SKU + cantidad)",
        )
    with col2:
        central_file = st.file_uploader(
            "💻 **Stock CENTRAL**",
            type=['csv', 'txt'],
            key="central_uploader",
            help="CSV con el stock del sistema central (SKU + cantidad)",
        )

    # Estado sin archivos
    if fisico_file is None or central_file is None:
        st.markdown("")
        st.info(
            "👆 Subí los dos archivos CSV para comenzar la auditoría.\n\n"
            "**Formato:** cada archivo debe tener al menos una columna de SKU "
            "y una columna de cantidad. El sistema detecta las columnas "
            "automáticamente."
        )

        # Botones de ejemplo en pantalla principal
        st.markdown("### 📥 ¿No tenés archivos a mano?")
        st.markdown(
            "<p style='color: #6b7280;'>"
            "Descargá estos archivos de ejemplo y probá la app:</p>",
            unsafe_allow_html=True,
        )
        col_ej1, col_ej2 = st.columns([1, 1])
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
        st.stop()

    # ─── Procesar archivos ───
    try:
        df_fisico = pd.read_csv(fisico_file, dtype=str)
        df_central = pd.read_csv(central_file, dtype=str)
    except Exception as e:
        st.error(f"❌ Error al leer los CSVs: {e}")
        st.stop()

    if df_fisico.empty:
        st.error("❌ El archivo de conteo físico está vacío.")
        st.stop()
    if df_central.empty:
        st.error("❌ El archivo de stock central está vacío.")
        st.stop()

    # Detectar columnas
    sku_col_f = detectar_columna(df_fisico, COL_SKU_CANDIDATES)
    qty_col_f = detectar_columna(df_fisico, COL_QTY_CANDIDATES, fallback_idx=1)
    sku_col_c = detectar_columna(df_central, COL_SKU_CANDIDATES)
    qty_col_c = detectar_columna(df_central, COL_QTY_CANDIDATES, fallback_idx=1)

    # Preview
    st.markdown("---")
    st.markdown("### 📋 Vistazo de los datos")

    tab1, tab2 = st.tabs(["📋 Conteo Físico", "💻 Stock Central"])
    with tab1:
        st.dataframe(df_fisico.head(10), use_container_width=True, hide_index=True)
        st.caption(f"{len(df_fisico)} filas • Columnas: {', '.join(df_fisico.columns)}")
    with tab2:
        st.dataframe(df_central.head(10), use_container_width=True, hide_index=True)
        st.caption(f"{len(df_central)} filas • Columnas: {', '.join(df_central.columns)}")

    # Columnas mapping
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

    # Sucursal
    st.markdown("### 🏪 Sucursal")
    sucursal = st.text_input(
        "Nombre de la sucursal (opcional, para el reporte)",
        placeholder="Ej: Sucursal Centro",
    )

    # ─── Botón ejecutar ───
    st.markdown("---")
    col_btn, _ = st.columns([1, 3])
    with col_btn:
        ejecutar = st.button("▶️  Ejecutar Auditoría", type="primary", use_container_width=True)

    if not ejecutar:
        st.stop()

    # ─── Ejecutar y guardar ───
    resultado = ejecutar_auditoria(
        df_fisico, df_central,
        sku_f, qty_f, sku_c, qty_c
    )

    s = resultado['stats']

    # Guardar en SQLite
    csv_fisico_raw = df_fisico.to_csv(index=False)
    csv_central_raw = df_central.to_csv(index=False)

    audit_id = guardar_auditoria(
        resultado, sucursal,
        fisico_file.name, central_file.name,
        csv_fisico_raw, csv_central_raw,
    )

    # Limpiar caché para que el historial se refresque
    st.cache_data.clear()

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
        <span style="float: right; color: #9ca3af; font-size: 0.85rem;">
            ID #{audit_id} · Guardado
        </span>
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
    tabs_res = resultado['tablas']

    if not tabs_res['faltantes'].empty:
        st.markdown("### 🔴 Faltantes (stock central > conteo físico)")
        st.dataframe(
            tabs_res['faltantes'].style.applymap(
                lambda _: 'color: #dc2626; font-weight: 600;',
                subset=['Diferencia'],
            ),
            use_container_width=True, hide_index=True,
        )

    if not tabs_res['sobrantes'].empty:
        st.markdown("### 🟡 Sobrantes (conteo físico > stock central)")
        st.dataframe(
            tabs_res['sobrantes'].style.applymap(
                lambda _: 'color: #d97706; font-weight: 600;',
                subset=['Diferencia'],
            ),
            use_container_width=True, hide_index=True,
        )

    if not tabs_res['solo_fisico'].empty:
        st.markdown("### ❓ En físico, no registrados en central")
        st.dataframe(tabs_res['solo_fisico'], use_container_width=True, hide_index=True)

    if not tabs_res['solo_central'].empty:
        st.markdown("### ❓ En central, no registrados en físico")
        st.dataframe(tabs_res['solo_central'], use_container_width=True, hide_index=True)

    if not tabs_res['coinciden'].empty:
        with st.expander(f"✅ Productos que coinciden ({len(tabs_res['coinciden'])})"):
            st.dataframe(tabs_res['coinciden'], use_container_width=True, hide_index=True)

    # ─── Exportación ───
    st.markdown("### 💾 Exportar resultados")

    reporte_txt = generar_reporte_txt(resultado, sucursal)

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
        df_difs_export = pd.concat([
            tabs_res['coinciden'].assign(Tipo='COINCIDE') if not tabs_res['coinciden'].empty else pd.DataFrame(),
            tabs_res['faltantes'].assign(Tipo='FALTANTE') if not tabs_res['faltantes'].empty else pd.DataFrame(),
            tabs_res['sobrantes'].assign(Tipo='SOBRANTE') if not tabs_res['sobrantes'].empty else pd.DataFrame(),
            tabs_res['solo_fisico'].assign(Tipo='SOLO_FISICO') if not tabs_res['solo_fisico'].empty else pd.DataFrame(),
            tabs_res['solo_central'].assign(Tipo='SOLO_CENTRAL') if not tabs_res['solo_central'].empty else pd.DataFrame(),
        ], ignore_index=True)
        if not df_difs_export.empty:
            st.download_button(
                "📋 Descargar Datos (.csv)",
                data=df_difs_export.to_csv(index=False),
                file_name=f"{base_name}_completo.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # ─── Nota final ───
    if s['veredicto'] == "APROBADA":
        st.success("✅ No se detectaron diferencias que requieran acción. "
                    "Podés firmar el reporte y archivar.")
    elif s['veredicto'] == "OBSERVADA":
        st.warning("⚠️ Revisá las diferencias marcadas. Si corresponden a errores "
                    "de carga o movimientos no registrados, ajustá el stock central.")
    else:
        st.error("🔴 Se detectaron diferencias significativas. Se recomienda "
                  "realizar un recuento físico de los productos conflictivos "
                  "antes de ajustar el sistema.")

    st.info(f"💾 Auditoría guardada con ID **#{audit_id}**. Podés consultarla "
            "desde la pestaña **📋 Historial** en cualquier momento.")

# ─────────────────────────────────────────────
#  TAB 2: Historial
# ─────────────────────────────────────────────

with tabs[1]:
    # ─── 3 niveles de navegación:
    #   Nivel 1 → auditoría específica (audit_id_ver)
    #   Nivel 2 → historial de sucursal  (sucursal_ver)
    #   Nivel 3 → panel de sucursales    (default)
    # ─────────────────────────────────────────────

    # ─── NIVEL 1: Ver auditoría específica ───
    if st.session_state.get('audit_id_ver'):
        audit_id_ver = st.session_state.audit_id_ver
        data = obtener_auditoria(audit_id_ver)
        if data is None:
            st.error("❌ Auditoría no encontrada. Puede haber sido eliminada.")
            st.session_state.audit_id_ver = None
            st.rerun()

        a = data['auditoria']
        diffs = data['diferencias']
        resultado_hist = reconstruir_resultado_desde_db(a, diffs)
        s_hist = resultado_hist['stats']
        tabs_hist = resultado_hist['tablas']

        # Botón volver — va a sucursal si venimos de ahí, si no al panel
        col_back, _ = st.columns([1, 4])
        with col_back:
            if st.button("← Volver", use_container_width=False):
                st.session_state.audit_id_ver = None
                st.rerun()

        st.markdown("---")

        # Veredicto
        ver_color = {"APROBADA": "green", "OBSERVADA": "orange", "RECHAZADA": "red"}
        vcolor = ver_color.get(s_hist['veredicto'], "gray")
        st.markdown(f"""
        <div style="background: white; border-radius: 12px; padding: 20px;
                    border-left: 5px solid {vcolor};
                    box-shadow: 0 1px 3px rgba(0,0,0,0.06); margin-bottom: 20px;">
            <span style="font-size: 1.5rem;">{s_hist['veredicto_icono']}</span>
            <span style="font-size: 1.3rem; font-weight: 700; color: {vcolor};">
                {s_hist['veredicto']}
            </span>
            <span style="color: #6b7280; margin-left: 8px;">— {s_hist['veredicto_msg']}</span>
            <div style="margin-top: 6px; color: #6b7280; font-size: 0.9rem;">
                🏪 {a['sucursal'] or 'Sin sucursal'} &nbsp;·&nbsp;
                🕐 {datetime.fromisoformat(a['fecha']).strftime('%d/%m/%Y %H:%M')} &nbsp;·&nbsp;
                📁 {a['archivo_fisico']} / {a['archivo_central']}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Métricas
        st.markdown("### 📊 Resumen")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("SKU Analizados", s_hist['total_sku'])
        m2.metric("Coinciden", f"{s_hist['coinciden']} ({s_hist['pct_coincidencia']}%)")
        m3.metric("Con Diferencias", s_hist['diferencias'])
        m4.metric("Diferencia Neta", s_hist['diferencia_neta'])

        # Tablas
        if not tabs_hist['faltantes'].empty:
            st.markdown("### 🔴 Faltantes")
            st.dataframe(tabs_hist['faltantes'], use_container_width=True, hide_index=True)
        if not tabs_hist['sobrantes'].empty:
            st.markdown("### 🟡 Sobrantes")
            st.dataframe(tabs_hist['sobrantes'], use_container_width=True, hide_index=True)
        if not tabs_hist['solo_fisico'].empty:
            st.markdown("### ❓ Solo en físico")
            st.dataframe(tabs_hist['solo_fisico'], use_container_width=True, hide_index=True)
        if not tabs_hist['solo_central'].empty:
            st.markdown("### ❓ Solo en central")
            st.dataframe(tabs_hist['solo_central'], use_container_width=True, hide_index=True)
        if not tabs_hist['coinciden'].empty:
            with st.expander(f"✅ Coinciden ({len(tabs_hist['coinciden'])})"):
                st.dataframe(tabs_hist['coinciden'], use_container_width=True, hide_index=True)

        # Exportar reporte desde historial
        st.markdown("### 💾 Exportar")
        reporte_hist = generar_reporte_txt(resultado_hist, a['sucursal'])
        st.download_button(
            "📄 Descargar Reporte (.txt)",
            data=reporte_hist,
            file_name=f"auditoria_#{audit_id_ver}_{a['sucursal'] or 'sucursal'}_{a['fecha'][:10]}.txt",
            mime="text/plain",
            use_container_width=False,
        )

        # Opción eliminar
        st.markdown("---")
        with st.expander("🗑️ Eliminar esta auditoría"):
            st.warning("⚠️ Esta acción no se puede deshacer.")
            col_del1, _ = st.columns([1, 3])
            with col_del1:
                if st.button("🗑️ Eliminar auditoría", use_container_width=True):
                    eliminar_auditoria(audit_id_ver)
                    st.success(f"✅ Auditoría #{audit_id_ver} eliminada.")
                    st.session_state.audit_id_ver = None
                    st.cache_data.clear()
                    st.rerun()

        st.stop()

    # ─── NIVEL 2: Ver historial de una sucursal ───
    if st.session_state.get('sucursal_ver'):
        sucursal_nombre = st.session_state.sucursal_ver

        col_back, _ = st.columns([1, 4])
        with col_back:
            if st.button("← Todas las sucursales", use_container_width=False):
                st.session_state.sucursal_ver = None
                st.rerun()

        st.markdown(f"### 🏪 {sucursal_nombre}")
        st.markdown(
            f"<p style='color: #6b7280;'>Todas las auditorías realizadas en esta sucursal.</p>",
            unsafe_allow_html=True,
        )

        auditorias_suc = auditorias_por_sucursal(sucursal_nombre)

        if not auditorias_suc:
            st.info("📭 No hay auditorías para esta sucursal.")
            st.stop()

        # Resumen de la sucursal
        total = len(auditorias_suc)
        aprob = sum(1 for a in auditorias_suc if a['veredicto'] == 'APROBADA')
        observ = sum(1 for a in auditorias_suc if a['veredicto'] == 'OBSERVADA')
        rechaz = sum(1 for a in auditorias_suc if a['veredicto'] == 'RECHAZADA')
        prom_pct = sum(a['pct_coincidencia'] for a in auditorias_suc) / total if total else 0
        ultima = datetime.fromisoformat(auditorias_suc[0]['fecha']).strftime('%d/%m/%Y')
        primera = datetime.fromisoformat(auditorias_suc[-1]['fecha']).strftime('%d/%m/%Y')

        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Auditorías", total)
        col_s2.metric("Promedio", f"{prom_pct:.1f}%")
        col_s3.metric("Período", f"{primera} — {ultima}")
        col_s4.metric("Resultados", f"✅ {aprob} · ⚠️ {observ} · 🔴 {rechaz}")

        # Evolución del % de coincidencia
        evol = []
        for a in reversed(auditorias_suc):
            evol.append({
                'Fecha': datetime.fromisoformat(a['fecha']).strftime('%d/%m'),
                '% Coincidencia': a['pct_coincidencia'],
                'Resultado': a['veredicto'],
            })
        df_evol = pd.DataFrame(evol)
        if len(df_evol) >= 2:
            st.markdown("### 📈 Evolución")
            st.line_chart(df_evol.set_index('Fecha')['% Coincidencia'])

        st.markdown("---")
        st.markdown("### 📋 Historial de auditorías")

        # Timeline
        for a in auditorias_suc:
            ver_color = {"APROBADA": "aprobada", "OBSERVADA": "observada", "RECHAZADA": "rechazada"}
            css_class = ver_color.get(a['veredicto'], "")
            icono = "✅" if a['veredicto'] == "APROBADA" else "⚠️" if a['veredicto'] == "OBSERVADA" else "🔴"
            fecha = datetime.fromisoformat(a['fecha']).strftime('%d/%m/%Y %H:%M')

            st.markdown(f"""
            <div class="timeline-item {css_class}">
                <div class="tl-header">
                    <span class="tl-fecha">{fecha} · ID #{a['id']}</span>
                    <span class="tl-veredicto">{icono} {a['veredicto']}</span>
                </div>
                <div class="tl-stats">
                    {a['coinciden']}/{a['total_sku']} OK ({a['pct_coincidencia']}%) ·
                    Falt: {a['faltantes']} · Sobr: {a['sobrantes']} ·
                    {a['archivo_fisico']} / {a['archivo_central']}
                </div>
                <div class="tl-actions">
            """, unsafe_allow_html=True)

            col_t1, col_t2 = st.columns([1, 8])
            with col_t1:
                if st.button("👁️ Ver", key=f"ver_{a['id']}", use_container_width=True):
                    st.session_state.audit_id_ver = a['id']
                    st.rerun()
            with col_t2:
                if st.button("🗑️ Eliminar", key=f"del_{a['id']}", use_container_width=True):
                    eliminar_auditoria(a['id'])
                    st.cache_data.clear()
                    st.rerun()

        st.stop()

    # ─── NIVEL 3: Panel de sucursales (default) ───
    st.markdown("### 🏪 Sucursales")

    sucursales = listar_sucursales()

    if not sucursales:
        st.info("📭 No hay auditorías guardadas todavía. Ejecutá una auditoría "
                "desde la pestaña **➕ Nueva Auditoría** y se guardará automáticamente.")
        st.stop()

    # Métrica global
    total_audits = sum(s['total_auditorias'] for s in sucursales)
    st.markdown(
        f"<p style='color: #6b7280;'>{total_audits} auditorías en {len(sucursales)} sucursales.</p>",
        unsafe_allow_html=True,
    )

    # Grilla de sucursales
    cols_grilla = st.columns(3)
    for i, s in enumerate(sucursales):
        with cols_grilla[i % 3]:
            nombre = s['sucursal'] if s['sucursal'] else '(Sin sucursal)'
            ultima = datetime.fromisoformat(s['ultima_fecha']).strftime('%d/%m/%Y') if s['ultima_fecha'] else '—'
            prom = s['promedio_coincidencia'] or 0
            icono = "✅" if prom >= 95 else "⚠️" if prom >= 80 else "🔴"

            st.markdown(f"""
            <div class="sucursal-card" onclick="this.querySelector('button').click()">
                <div class="nombre">
                    {icono} {nombre}
                    <span class="badge-count">{s['total_auditorias']}</span>
                </div>
                <div class="meta">Última: {ultima}</div>
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="num">{prom:.1f}%</div>
                        <div class="label">Promedio</div>
                    </div>
                    <div class="stat-item">
                        <div class="num aprobada">{s['aprobadas']}</div>
                        <div class="label">✅ OK</div>
                    </div>
                    <div class="stat-item">
                        <div class="num observada">{s['observadas']}</div>
                        <div class="label">⚠️ Obs</div>
                    </div>
                    <div class="stat-item">
                        <div class="num rechazada">{s['rechazadas']}</div>
                        <div class="label">🔴 Rech</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button(f"Ver historial", key=f"suc_{i}", use_container_width=True):
                st.session_state.sucursal_ver = s['sucursal']
                st.rerun()

# ─── Footer ───
st.markdown(
    '<div class="footer-badge">'
    'Agente de Auditoría de Inventarios v2.0 · Datos guardados en SQLite</div>',
    unsafe_allow_html=True,
)
