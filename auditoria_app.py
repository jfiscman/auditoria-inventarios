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
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Estilo personalizado (light mode, cream bg) ───
st.markdown("""
<style>
    /* ── Global ── */
    .stApp { background-color: #f7f6f3; }
    .main > div { background-color: #f7f6f3; }

    /* ── Cards white ── */
    .card {
        background: white;
        border-radius: 14px;
        padding: 24px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        border: 1px solid #eae9e6;
        margin-bottom: 16px;
    }
    .card-flat {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: none;
        border: 1px solid #eae9e6;
        margin-bottom: 8px;
    }

    /* ── Metrics ── */
    [data-testid="stMetric"] {
        background: white;
        border-radius: 12px;
        padding: 18px 14px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        border: 1px solid #eae9e6;
    }
    [data-testid="stMetric"] label {
        color: #6b7280;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: #111827;
        font-size: 1.6rem;
        font-weight: 700;
    }
    [data-testid="stMetric"] [data-testid="stMetricDelta"] {
        font-size: 0.82rem;
    }

    /* ── Buttons: primary (indigo) ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.55rem 1.8rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s;
        box-shadow: 0 2px 8px rgba(79,70,229,0.18);
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 16px rgba(79,70,229,0.30);
        transform: translateY(-1px);
        color: white;
    }
    .stButton > button[kind="primary"]:active {
        transform: translateY(0);
    }

    /* ── Buttons: secondary (outline) ── */
    .stButton > button[kind="secondary"] {
        background: transparent;
        color: #4f46e5;
        border: 1.5px solid #c7d2fe;
        border-radius: 10px;
        padding: 0.45rem 1.4rem;
        font-weight: 600;
        font-size: 0.88rem;
        transition: all 0.15s;
    }
    .stButton > button[kind="secondary"]:hover {
        border-color: #4f46e5;
        background: #eef2ff;
        color: #4338ca;
    }

    /* ── Buttons: tertiary (ghost) ── */
    .stButton > button[kind="tertiary"] {
        background: transparent;
        color: #6b7280;
        border: none;
        border-radius: 8px;
        padding: 0.35rem 1rem;
        font-weight: 500;
        font-size: 0.85rem;
        transition: all 0.15s;
    }
    .stButton > button[kind="tertiary"]:hover {
        background: #f3f4f6;
        color: #111827;
    }

    /* ── Danger buttons ── */
    .btn-danger-row button {
        background: transparent !important;
        color: #ef4444 !important;
        border: 1.5px solid #fecaca !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.15s !important;
    }
    .btn-danger-row button:hover {
        background: #fef2f2 !important;
        border-color: #ef4444 !important;
    }

    /* ── File Uploader ── */
    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 14px;
        padding: 12px;
        border: 2px dashed #d4d2cc;
        transition: all 0.2s;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: #4f46e5;
        background: #faf9ff;
    }

    /* ── Headings ── */
    h1, h2, h3 { color: #111827; }
    h1 { font-size: 1.6rem; font-weight: 800; margin-bottom: 0.1rem; }
    h2 { font-size: 1.2rem; font-weight: 700; margin-top: 1.2rem; }
    h3 { font-size: 1.05rem; font-weight: 600; margin-top: 1rem; }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab"] {
        font-weight: 500;
        color: #9ca3af;
        font-size: 0.95rem;
        padding: 8px 20px;
        border-radius: 10px 10px 0 0;
        transition: color 0.15s;
    }
    .stTabs [aria-selected="true"] {
        color: #4f46e5;
        font-weight: 700;
    }
    .stTabs [data-baseweb="tab"]:hover:not([aria-selected="true"]) {
        color: #6b7280;
    }

    /* ── DataFrames ── */
    [data-testid="stDataFrame"] {
        background: white;
        border-radius: 12px;
        padding: 4px;
        border: 1px solid #eae9e6;
    }

    /* ── Expanders ── */
    div[data-testid="stExpander"] {
        background: white;
        border-radius: 12px;
        border: 1px solid #eae9e6;
    }

    /* ── Alerts ── */
    div.stAlert { border-radius: 12px; }

    /* ── HR ── */
    hr { border-color: #e8e7e4; margin: 1.2rem 0; }

    /* ── Breadcrumb nav ── */
    .breadcrumb {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 0.88rem;
        color: #9ca3af;
        margin-bottom: 16px;
    }
    .breadcrumb a, .breadcrumb .bc-link {
        color: #4f46e5;
        cursor: pointer;
        font-weight: 500;
        text-decoration: none;
        transition: color 0.15s;
    }
    .breadcrumb a:hover, .breadcrumb .bc-link:hover {
        color: #4338ca;
        text-decoration: underline;
    }
    .breadcrumb .bc-sep { color: #d1d5db; }
    .breadcrumb .bc-current { color: #111827; font-weight: 600; }

    /* ── Veredicto hero ── */
    .veredicto-hero {
        background: white;
        border-radius: 16px;
        padding: 28px 32px;
        border-left: 6px solid;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 24px;
    }
    .veredicto-hero .v-icon {
        font-size: 2.2rem;
        margin-right: 12px;
    }
    .veredicto-hero .v-title {
        font-size: 1.5rem;
        font-weight: 800;
    }
    .veredicto-hero .v-sub {
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: 4px;
    }
    .veredicto-hero .v-id {
        float: right;
        color: #9ca3af;
        font-size: 0.82rem;
        font-weight: 500;
    }

    /* ── Sucursal cards ── */
    .sucursal-card {
        background: white;
        border-radius: 16px;
        padding: 22px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
        border: 1px solid #eae9e6;
        cursor: pointer;
        transition: all 0.2s;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .sucursal-card:hover {
        box-shadow: 0 6px 24px rgba(0,0,0,0.08);
        border-color: #c7d2fe;
        transform: translateY(-2px);
    }
    .sucursal-card .sc-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 4px;
    }
    .sucursal-card .sc-icon {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        font-weight: 700;
        flex-shrink: 0;
    }
    .sucursal-card .sc-icon.green { background: #dcfce7; color: #16a34a; }
    .sucursal-card .sc-icon.yellow { background: #fef3c7; color: #d97706; }
    .sucursal-card .sc-icon.red { background: #fee2e2; color: #dc2626; }
    .sucursal-card .sc-name {
        font-size: 1.05rem;
        font-weight: 700;
        color: #111827;
        flex: 1;
    }
    .sucursal-card .sc-badge {
        background: #4f46e5;
        color: white;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 20px;
    }
    .sucursal-card .sc-meta {
        color: #9ca3af;
        font-size: 0.8rem;
        margin-bottom: 12px;
        padding-left: 46px;
    }
    .sucursal-card .sc-stats {
        display: flex;
        gap: 8px;
        margin-top: auto;
        padding-top: 12px;
        border-top: 1px solid #f0efec;
    }
    .sucursal-card .sc-stat {
        text-align: center;
        flex: 1;
        padding: 4px 0;
    }
    .sucursal-card .sc-stat .val {
        font-size: 1.15rem;
        font-weight: 700;
        color: #111827;
    }
    .sucursal-card .sc-stat .lbl {
        font-size: 0.65rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-weight: 600;
    }
    .sucursal-card .sc-stat .val.ok { color: #16a34a; }
    .sucursal-card .sc-stat .val.warn { color: #d97706; }
    .sucursal-card .sc-stat .val.bad { color: #dc2626; }

    /* ── Timeline items ── */
    .timeline-item {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        border: 1px solid #eae9e6;
        margin-bottom: 10px;
        border-left: 4px solid #d1d5db;
        transition: all 0.15s;
    }
    .timeline-item:hover {
        box-shadow: 0 3px 12px rgba(0,0,0,0.07);
    }
    .timeline-item.aprobada { border-left-color: #16a34a; }
    .timeline-item.observada { border-left-color: #d97706; }
    .timeline-item.rechazada { border-left-color: #dc2626; }
    .tl-header { display: flex; justify-content: space-between; align-items: center; }
    .tl-fecha { color: #9ca3af; font-size: 0.82rem; }
    .tl-veredicto { font-weight: 700; font-size: 0.9rem; }
    .tl-stats { color: #6b7280; font-size: 0.85rem; margin-top: 4px; }

    /* ── Action bar ── */
    .action-bar {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        align-items: center;
    }

    /* ── Download buttons ── */
    .stDownloadButton > button {
        background: white !important;
        color: #4f46e5 !important;
        border: 1.5px solid #c7d2fe !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
        transition: all 0.15s !important;
    }
    .stDownloadButton > button:hover {
        background: #eef2ff !important;
        border-color: #4f46e5 !important;
        box-shadow: 0 2px 8px rgba(79,70,229,0.12) !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"] {
        background: #faf9f7;
        border-right: 1px solid #e8e7e4;
    }
    section[data-testid="stSidebar"] .stMarkdown { color: #374151; }

    /* ── Footer ── */
    .footer-badge {
        text-align: center;
        color: #9ca3af;
        font-size: 0.75rem;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e2e1dd;
    }

    /* ── Section labels ── */
    .section-label {
        color: #6b7280;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 8px;
    }

    /* ── Pill tag ── */
    .pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .pill-green { background: #dcfce7; color: #16a34a; }
    .pill-yellow { background: #fef3c7; color: #d97706; }
    .pill-red { background: #fee2e2; color: #dc2626; }
    .pill-gray { background: #f3f4f6; color: #6b7280; }
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


def eliminar_auditoria(audit_id: int):
    """Elimina una auditoría y sus diferencias asociadas."""
    conn = get_db()
    conn.execute("DELETE FROM diferencias WHERE audit_id = ?", (audit_id,))
    conn.execute("DELETE FROM auditorias WHERE id = ?", (audit_id,))
    conn.commit()
    conn.close()


def obtener_auditoria(audit_id: int):
    """Devuelve auditoría + diferencias por ID."""
    conn = get_db()
    a = conn.execute("SELECT * FROM auditorias WHERE id = ?", (audit_id,)).fetchone()
    if a is None:
        conn.close()
        return None
    diffs = conn.execute(
        "SELECT * FROM diferencias WHERE audit_id = ? ORDER BY tipo, sku",
        (audit_id,),
    ).fetchall()
    conn.close()
    return {'auditoria': dict(a), 'diferencias': [dict(d) for d in diffs]}


@st.cache_data
def listar_auditorias(limit: int = 50, offset: int = 0) -> list:
    """Lista las últimas N auditorías."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM auditorias ORDER BY fecha DESC LIMIT ? OFFSET ?",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@st.cache_data
def estadisticas_generales() -> dict:
    """Resumen global de todas las auditorías."""
    conn = get_db()
    r = conn.execute("""
        SELECT COUNT(*) as total_auditorias,
               COALESCE(SUM(total_sku), 0) as total_sku_auditados,
               COALESCE(SUM(CASE WHEN veredicto='APROBADA' THEN 1 ELSE 0 END), 0) as aprobadas,
               COALESCE(SUM(CASE WHEN veredicto='OBSERVADA' THEN 1 ELSE 0 END), 0) as observadas,
               COALESCE(SUM(CASE WHEN veredicto='RECHAZADA' THEN 1 ELSE 0 END), 0) as rechazadas,
               COALESCE(AVG(pct_coincidencia), 0) as promedio_coincidencia
        FROM auditorias
    """).fetchone()
    conn.close()
    return dict(r)


@st.cache_data
def listar_sucursales() -> list:
    """Devuelve lista de sucursales con estadísticas resumidas."""
    conn = get_db()
    rows = conn.execute("""
        SELECT sucursal,
               COUNT(*) as total_auditorias,
               ROUND(AVG(pct_coincidencia), 1) as promedio_coincidencia,
               MAX(fecha) as ultima_fecha,
               SUM(CASE WHEN veredicto='APROBADA' THEN 1 ELSE 0 END) as aprobadas,
               SUM(CASE WHEN veredicto='OBSERVADA' THEN 1 ELSE 0 END) as observadas,
               SUM(CASE WHEN veredicto='RECHAZADA' THEN 1 ELSE 0 END) as rechazadas
        FROM auditorias
        WHERE sucursal != ''
        GROUP BY sucursal
        ORDER BY promedio_coincidencia DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@st.cache_data
def auditorias_por_sucursal(sucursal: str) -> list:
    """Lista auditorías de una sucursal, las más recientes primero."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM auditorias WHERE sucursal = ? ORDER BY fecha DESC",
        (sucursal,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def sembrar_datos_ejemplo():
    """Carga datos de ejemplo en la DB para demostración (sin borrar datos existentes)."""
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) as c FROM auditorias").fetchone()
    if existing['c'] > 0:
        conn.close()
        return

    import random
    random.seed(42)
    from datetime import timedelta

    productos_base = [
        ('LAP-001', 'LAP-002', 'MON-001', 'TEC-001', 'TEC-002'),
        ('MOU-001', 'MOU-002', 'AUD-001', 'WEB-001', 'WEB-002'),
        ('CAB-001', 'CAB-002', 'DIS-001', 'DIS-002', 'TAB-001'),
        ('TAB-002', 'CHA-001', 'CHA-002', 'CBL-001', 'CBL-002'),
    ]
    todos_productos = [p for grupo in productos_base for p in grupo]

    sucursales_data = [
        ('Sucursal Centro', 0.92, 0.05),
        ('Sucursal Norte',  0.78, 0.12),
        ('Sucursal Oeste',  0.88, 0.08),
        ('Sucursal Este',   0.65, 0.18),
    ]

    base_date = datetime.now() - timedelta(days=90)
    audit_id = 0

    for suc_nombre, base_accuracy, noise in sucursales_data:
        num_audits = random.randint(3, 5)
        for i in range(num_audits):
            audit_date = base_date + timedelta(days=i * random.randint(15, 30))
            fecha_str = audit_date.isoformat()

            fisico_dict = {}
            central_dict = {}
            for sku in todos_productos:
                q_central = random.randint(0, 30)
                if random.random() < base_accuracy:
                    q_fisico = q_central
                else:
                    variacion = int(random.gauss(0, q_central * noise + 1))
                    q_fisico = max(0, q_central + variacion)
                central_dict[sku] = q_central
                fisico_dict[sku] = q_fisico

            todos_skus = sorted(set(fisico_dict) | set(central_dict))
            coinc, falt, sob, sf, sc = [], [], [], [], []
            total_f, total_c = 0, 0

            for sku in todos_skus:
                qf = fisico_dict.get(sku, 0)
                qc = central_dict.get(sku, 0)
                total_f += qf
                total_c += qc
                diff = qf - qc
                if sku not in central_dict:
                    sf.append((sku, qf, 0, qf))
                elif sku not in fisico_dict:
                    sc.append((sku, 0, qc, -qc))
                elif diff == 0:
                    coinc.append((sku, qf, qc, 0))
                elif diff > 0:
                    sob.append((sku, qf, qc, diff))
                else:
                    falt.append((sku, qf, qc, diff))

            n_total = len(todos_skus)
            n_ok = len(coinc)
            pct = (n_ok / n_total * 100) if n_total else 0
            if pct >= 95:
                veredicto = 'APROBADA'
            elif pct >= 80:
                veredicto = 'OBSERVADA'
            else:
                veredicto = 'RECHAZADA'

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
                fecha_str, suc_nombre,
                f'ejemplo_fisico_{i+1}.csv',
                f'ejemplo_central_{i+1}.csv',
                n_total, n_ok, len(falt) + len(sob),
                len(sob), len(falt),
                len(sf), len(sc),
                total_f, total_c, total_f - total_c,
                round(pct, 1), veredicto,
                '', '',
            ))
            audit_id = cur.lastrowid

            rows = []
            for sku, fis, cen, dif in falt:
                rows.append((audit_id, sku, 'FALTANTE', fis, cen, dif))
            for sku, fis, cen, dif in sob:
                rows.append((audit_id, sku, 'SOBRANTE', fis, cen, dif))
            for sku, fis, cen, dif in sf:
                rows.append((audit_id, sku, 'SOLO_FISICO', fis, cen, dif))
            for sku, fis, cen, dif in sc:
                rows.append((audit_id, sku, 'SOLO_CENTRAL', fis, cen, dif))
            for sku, fis, cen, dif in coinc:
                rows.append((audit_id, sku, 'COINCIDE', fis, cen, dif))
            if rows:
                conn.executemany("""
                    INSERT INTO diferencias
                        (audit_id, sku, tipo, cantidad_fisico, cantidad_central, diferencia)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, rows)

    conn.commit()
    conn.close()
    if audit_id:
        st.cache_data.clear()


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
    """Reconstruye el dict 'resultado' desde los datos de la DB."""
    s = audit
    pct = s['pct_coincidencia']
    if pct >= 95:
        icono, texto, msg = "✅", "APROBADA", "Sin diferencias significativas."
    elif pct >= 80:
        icono, texto, msg = "⚠️", "OBSERVADA", "Revisar diferencias detectadas."
    else:
        icono, texto, msg = "🔴", "RECHAZADA", "Requiere investigación."

    stats = {
        'total_sku': s['total_sku'], 'coinciden': s['coinciden'],
        'diferencias': s['diferencias'], 'sobrantes': s['sobrantes'],
        'faltantes': s['faltantes'], 'solo_fisico': s['solo_fisico'],
        'solo_central': s['solo_central'], 'total_fisico': s['total_unid_fis'],
        'total_central': s['total_unid_cen'], 'diferencia_neta': s['diferencia_neta'],
        'pct_coincidencia': pct, 'veredicto_icono': icono,
        'veredicto': texto, 'veredicto_msg': msg,
    }

    tablas = {k: pd.DataFrame() for k in
              ['coinciden', 'sobrantes', 'faltantes', 'solo_fisico', 'solo_central']}

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

    if coic: tablas['coinciden'] = pd.DataFrame(coic)
    if sob: tablas['sobrantes'] = pd.DataFrame(sob)
    if falt: tablas['faltantes'] = pd.DataFrame(falt)
    if sf: tablas['solo_fisico'] = pd.DataFrame(sf)
    if sc: tablas['solo_central'] = pd.DataFrame(sc)

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
1. **Subí los dos archivos CSV** — el conteo físico y el stock central.
2. **Confirmá las columnas** — SKU y cantidad se detectan solas.
3. **Ejecutá la auditoría** — al instante ves el resultado.
4. **Consultá el historial** — todas las auditorías quedan guardadas.
    """)

    st.markdown("---")

    # Estadísticas generales
    est = estadisticas_generales()
    if est['total_auditorias'] > 0:
        st.markdown("### 📊 Resumen global")
        col_sg1, col_sg2 = st.columns(2)
        with col_sg1:
            st.metric("Auditorías", est['total_auditorias'])
        with col_sg2:
            st.metric("Promedio", f"{est['promedio_coincidencia']:.1f}%")
        st.markdown(
            f"<div style='font-size:0.85rem; color:#6b7280; text-align:center;'>"
            f"✅ {est['aprobadas']} &nbsp;⚠️ {est['observadas']} &nbsp;🔴 {est['rechazadas']}"
            f"</div>",
            unsafe_allow_html=True,
        )
    else:
        st.info("📭 Ejecutá una auditoría o cargá ejemplos.")

    st.markdown("---")

    # Descargar ejemplos
    st.markdown('<div class="section-label">Descargar ejemplos</div>', unsafe_allow_html=True)
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

    st.markdown("---")

    # Mantenimiento
    st.markdown('<div class="section-label">Mantenimiento</div>', unsafe_allow_html=True)
    if st.button("🎲 Cargar datos de ejemplo", use_container_width=True, type="secondary"):
        sembrar_datos_ejemplo()
        st.cache_data.clear()
        st.rerun()
    if st.button("🔄 Refrescar datos", use_container_width=True, type="tertiary"):
        st.cache_data.clear()
        st.rerun()

    st.markdown(
        "<p style='color: #9ca3af; font-size: 0.72rem; text-align: center; margin-top: 16px;'>"
        "v3.0 · Auditoría de Inventarios</p>",
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
            "📋 Conteo FÍSICO",
            type=['csv', 'txt'],
            key="fisico_uploader",
            help="CSV con el conteo real de la sucursal (SKU + cantidad)",
        )
    with col2:
        central_file = st.file_uploader(
            "💻 Stock CENTRAL",
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
    st.markdown('<div class="section-label">Vistazo de los datos</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📋 Conteo Físico", "💻 Stock Central"])
    with tab1:
        st.dataframe(df_fisico.head(10), use_container_width=True, hide_index=True)
        st.caption(f"{len(df_fisico)} filas · Columnas: {', '.join(df_fisico.columns)}")
    with tab2:
        st.dataframe(df_central.head(10), use_container_width=True, hide_index=True)
        st.caption(f"{len(df_central)} filas · Columnas: {', '.join(df_central.columns)}")

    # Columnas mapping
    st.markdown('<div class="section-label">Columnas para la comparación</div>', unsafe_allow_html=True)
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
    sucursal = st.text_input(
        "🏪 Sucursal (opcional, para el reporte)",
        placeholder="Ej: Sucursal Centro",
    )

    # ─── Botón ejecutar ───
    st.markdown("")
    col_btn, _ = st.columns([2, 5])
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

    st.cache_data.clear()

    # ─── VEREDICTO HERO ───
    ver_colors = {"APROBADA": "#16a34a", "OBSERVADA": "#d97706", "RECHAZADA": "#dc2626"}
    vcolor = ver_colors.get(s['veredicto'], "gray")
    pill_cls = {"APROBADA": "pill-green", "OBSERVADA": "pill-yellow", "RECHAZADA": "pill-red"}
    st.markdown(f"""
    <div class="veredicto-hero" style="border-left-color: {vcolor};">
        <span class="v-id">ID #{audit_id} · Guardado</span>
        <span class="v-icon">{s['veredicto_icono']}</span>
        <span class="v-title" style="color: {vcolor};">{s['veredicto']}</span>
        <span class="pill {pill_cls.get(s['veredicto'], '')}">{s['pct_coincidencia']}%</span>
        <div class="v-sub">{s['veredicto_msg']}</div>
    </div>
    """, unsafe_allow_html=True)

    # ─── Métricas principales ───
    st.markdown('<div class="section-label">Resumen</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("SKU Analizados", s['total_sku'])
    m2.metric("Coinciden", f"{s['coinciden']} ({s['pct_coincidencia']}%)")
    m3.metric("Con Diferencias", s['diferencias'],
              delta=f"+{s['sobrantes']} sobr / -{s['faltantes']} falt")
    m4.metric("Diferencia Neta", f"{s['diferencia_neta']:+,} uds")

    m5, m6, m7, m8 = st.columns(4)
    m5.metric("Unid. Físico", f"{s['total_fisico']:,}")
    m6.metric("Unid. Central", f"{s['total_central']:,}")
    m7.metric("Solo en Físico", s['solo_fisico'])
    m8.metric("Solo en Central", s['solo_central'])

    # ─── Tablas de detalle ───
    tabs_res = resultado['tablas']

    if not tabs_res['faltantes'].empty:
        st.markdown("### 🔴 Faltantes (stock central > conteo físico)")
        st.dataframe(
            tabs_res['faltantes'].style.map(
                lambda _: 'color: #dc2626; font-weight: 600;',
                subset=['Diferencia'],
            ),
            use_container_width=True, hide_index=True,
        )

    if not tabs_res['sobrantes'].empty:
        st.markdown("### 🟡 Sobrantes (conteo físico > stock central)")
        st.dataframe(
            tabs_res['sobrantes'].style.map(
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

    # ─── Métricas avanzadas ───
    st.markdown("---")
    st.markdown("### 📈 Métricas de la auditoría")

    tabs_metricas = st.tabs(["📊 Distribución", "🎯 Precisión", "⚠️ Impacto"])

    # Construir df_unificado para métricas
    df_metricas = pd.DataFrame()
    for tipo in ['COINCIDE', 'FALTANTE', 'SOBRANTE', 'SOLO_FISICO', 'SOLO_CENTRAL']:
        key = {'COINCIDE': 'coinciden', 'FALTANTE': 'faltantes',
               'SOBRANTE': 'sobrantes', 'SOLO_FISICO': 'solo_fisico',
               'SOLO_CENTRAL': 'solo_central'}[tipo]
        tdf = resultado['tablas'].get(key, pd.DataFrame())
        if not tdf.empty:
            tdf = tdf.copy()
            tdf['Tipo'] = tipo
            if tipo == 'COINCIDE':
                tdf['Diferencia'] = 0
                tdf['Físico'] = tdf['Cantidad']
                tdf['Central'] = tdf['Cantidad']
            elif tipo == 'SOLO_FISICO':
                tdf['Diferencia'] = tdf['Cantidad Físico']
                tdf['Físico'] = tdf['Cantidad Físico']
                tdf['Central'] = 0
            elif tipo == 'SOLO_CENTRAL':
                tdf['Diferencia'] = -tdf['Cantidad Central']
                tdf['Físico'] = 0
                tdf['Central'] = tdf['Cantidad Central']
            df_metricas = pd.concat([df_metricas, tdf], ignore_index=True)

    with tabs_metricas[0]:
        st.markdown("**Distribución de diferencias**")

        if not df_metricas.empty:
            def cat_diff(d):
                d = int(d)
                if d == 0: return '0 (Coincide)'
                elif abs(d) == 1: return '±1'
                elif abs(d) <= 3: return '±2 a 3'
                elif abs(d) <= 10: return '±4 a 10'
                else: return '> ±10'

            df_metricas['Categoría'] = df_metricas['Diferencia'].apply(cat_diff)
            dist = df_metricas['Categoría'].value_counts().reindex(
                ['0 (Coincide)', '±1', '±2 a 3', '±4 a 10', '> ±10'],
                fill_value=0
            )

            col_dist1, col_dist2 = st.columns([1, 1])
            with col_dist1:
                st.bar_chart(dist)
            with col_dist2:
                st.markdown("**Resumen por categoría**")
                for cat, count in dist.items():
                    pct = count / len(df_metricas) * 100
                    icon = "✅" if cat == '0 (Coincide)' else "⚠️"
                    st.markdown(f"{icon} **{cat}:** {count} productos ({pct:.1f}%)")

            st.caption("Productos con diferencia 0 = stock correcto. "
                       "Diferencias > ±10 requieren investigación urgente.")

    with tabs_metricas[1]:
        st.markdown("**Indicadores de precisión**")

        if not df_metricas.empty:
            total_items = len(df_metricas)
            correctos = len(df_metricas[df_metricas['Diferencia'] == 0])
            incorrectos = total_items - correctos
            total_unidades_fisico = df_metricas['Físico'].sum()
            total_unidades_central = df_metricas['Central'].sum()

            iar_count = (correctos / total_items * 100) if total_items else 0
            iar_value = 100 - (abs(df_metricas['Diferencia']).sum() / max(total_unidades_central, 1) * 100)
            iar_value = max(0, min(100, iar_value))

            col_p1, col_p2, col_p3 = st.columns(3)
            col_p1.metric("📊 Precisión (SKU)", f"{iar_count:.1f}%",
                          help="Porcentaje de SKU que coinciden exactamente")
            col_p2.metric("📦 Precisión (volumen)", f"{iar_value:.1f}%",
                          help="Qué % del volumen total de stock está correcto")
            col_p3.metric("🔢 Error promedio", f"{abs(df_metricas['Diferencia']).mean():.1f} uds",
                          help="Promedio de unidades de error por producto")

            st.markdown("**Resumen de la auditoría**")
            resumen_data = {
                'Indicador': [
                    'Total SKU analizados', 'SKU correctos', 'SKU con diferencias',
                    'Total unidades físicas', 'Total unidades central',
                    'Diferencia neta (uds)',
                    'Tasa de precisión (SKU)', 'Tasa de precisión (volumen)',
                    'Error promedio por SKU',
                ],
                'Valor': [
                    f'{total_items}', f'{correctos}', f'{incorrectos}',
                    f'{total_unidades_fisico:,.0f}', f'{total_unidades_central:,.0f}',
                    f'{total_unidades_fisico - total_unidades_central:+,.0f}',
                    f'{iar_count:.1f}%', f'{iar_value:.1f}%',
                    f'{abs(df_metricas["Diferencia"]).mean():.1f}',
                ],
                'Evaluación': [
                    '—',
                    '✅ Bueno' if iar_count >= 95 else '⚠️ Regular' if iar_count >= 80 else '🔴 Malo',
                    '—', '—', '—',
                    '✅ OK' if abs(total_unidades_fisico - total_unidades_central) < 10
                    else '⚠️ Revisar' if abs(total_unidades_fisico - total_unidades_central) < 50
                    else '🔴 Alta',
                    '✅ Bueno' if iar_count >= 95 else '⚠️ Regular' if iar_count >= 80 else '🔴 Malo',
                    '✅ Bueno' if iar_value >= 95 else '⚠️ Regular' if iar_value >= 80 else '🔴 Malo',
                    '✅ Bajo' if abs(df_metricas['Diferencia']).mean() < 2
                    else '⚠️ Medio' if abs(df_metricas['Diferencia']).mean() < 5
                    else '🔴 Alto',
                ],
            }
            st.dataframe(pd.DataFrame(resumen_data), use_container_width=True, hide_index=True)

    with tabs_metricas[2]:
        st.markdown("**Productos con mayor impacto**")

        if not df_metricas.empty:
            top_falt = df_metricas[df_metricas['Diferencia'] < 0].copy()
            top_falt['Impacto'] = top_falt['Diferencia'].abs()
            top_falt = top_falt.nlargest(5, 'Impacto')[['SKU', 'Físico', 'Central', 'Diferencia', 'Impacto']]

            top_sob = df_metricas[df_metricas['Diferencia'] > 0].copy()
            top_sob['Impacto'] = top_sob['Diferencia']
            top_sob = top_sob.nlargest(5, 'Impacto')[['SKU', 'Físico', 'Central', 'Diferencia', 'Impacto']]

            col_i1, col_i2 = st.columns(2)
            with col_i1:
                st.markdown("**🔴 Top faltantes**")
                if not top_falt.empty:
                    st.dataframe(top_falt, use_container_width=True, hide_index=True)
                else:
                    st.success("No hay faltantes.")
            with col_i2:
                st.markdown("**🟡 Top sobrantes**")
                if not top_sob.empty:
                    st.dataframe(top_sob, use_container_width=True, hide_index=True)
                else:
                    st.success("No hay sobrantes.")

            # Comparativa con histórico
            if sucursal:
                historial_suc = auditorias_por_sucursal(sucursal)
                historial_suc = [h for h in historial_suc
                                 if h['fecha'] < datetime.now().isoformat()]
                if len(historial_suc) >= 1:
                    st.markdown("---")
                    st.markdown("**📊 Comparativa con auditorías anteriores**")
                    st.caption(f"Evolución histórica de la sucursal '{sucursal}'")

                    data_hist = []
                    for h in historial_suc:
                        data_hist.append({
                            'Fecha': datetime.fromisoformat(h['fecha']).strftime('%d/%m'),
                            '% Coincidencia': h['pct_coincidencia'],
                        })
                    data_hist.append({
                        'Fecha': 'Actual',
                        '% Coincidencia': s['pct_coincidencia'],
                    })
                    df_hist = pd.DataFrame(data_hist)
                    if len(df_hist) >= 2:
                        st.line_chart(df_hist.set_index('Fecha')['% Coincidencia'])

                    prom_hist = sum(h['pct_coincidencia'] for h in historial_suc) / len(historial_suc)
                    diff_hist = s['pct_coincidencia'] - prom_hist
                    delta_str = f"+{diff_hist:.1f}%" if diff_hist > 0 else f"{diff_hist:.1f}%"
                    delta_color = "#16a34a" if diff_hist >= 0 else "#dc2626"

                    st.markdown(
                        f"<div style='color: #6b7280;'>"
                        f"Promedio histórico: <b>{prom_hist:.1f}%</b> &nbsp;·&nbsp; "
                        f"Actual: <b>{s['pct_coincidencia']}%</b> &nbsp;·&nbsp; "
                        f"<span style='color: {delta_color}; font-weight: 600;'>{delta_str}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("📭 No hay auditorías anteriores de esta sucursal para comparar.")
            else:
                st.info("💡 Usá el campo **Sucursal** al ejecutar una auditoría "
                        "para habilitar la comparativa histórica.")

    # ─── Exportación ───
    st.markdown("---")
    st.markdown("### 💾 Exportar resultados")

    reporte_txt = generar_reporte_txt(resultado, sucursal)
    base_name = f"auditoria_{sucursal or 'sucursal'}_{datetime.now():%Y%m%d_%H%M%S}"

    col_d1, col_d2, col_d3 = st.columns(3)
    with col_d1:
        st.download_button(
            "📄 Reporte (.txt)",
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
                "📋 Datos (.csv)",
                data=df_difs_export.to_csv(index=False),
                file_name=f"{base_name}_completo.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # ─── Nota final ───
    st.markdown("")
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

    st.info(f"💾 Auditoría guardada con ID **#{audit_id}**. Consultala desde "
            "la pestaña **📋 Historial**.")

# ─────────────────────────────────────────────
#  TAB 2: Historial
# ─────────────────────────────────────────────

with tabs[1]:
    # ─── 3 niveles de navegación con breadcrumbs ───

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

        # Breadcrumb
        suc_name = a['sucursal'] or '(sin sucursal)'
        st.markdown(f"""
        <div class="breadcrumb">
            <span class="bc-link" onclick="window.streamlit.setComponentValue('bc_panel')">🏪 Sucursales</span>
            <span class="bc-sep">›</span>
            <span class="bc-link" onclick="window.streamlit.setComponentValue('bc_suc')">{suc_name}</span>
            <span class="bc-sep">›</span>
            <span class="bc-current">#{audit_id_ver}</span>
        </div>
        """, unsafe_allow_html=True)

        # Navigation buttons
        col_bc1, col_bc2, _ = st.columns([1, 1, 4])
        with col_bc1:
            if st.button("← Sucursal", type="secondary", use_container_width=True):
                st.session_state.audit_id_ver = None
                st.rerun()
        with col_bc2:
            if st.button("← Panel", type="tertiary", use_container_width=True):
                st.session_state.audit_id_ver = None
                st.session_state.sucursal_ver = None
                st.rerun()

        st.markdown("---")

        # Veredicto hero
        ver_colors = {"APROBADA": "#16a34a", "OBSERVADA": "#d97706", "RECHAZADA": "#dc2626"}
        vcolor = ver_colors.get(s_hist['veredicto'], "gray")
        pill_cls = {"APROBADA": "pill-green", "OBSERVADA": "pill-yellow", "RECHAZADA": "pill-red"}
        st.markdown(f"""
        <div class="veredicto-hero" style="border-left-color: {vcolor};">
            <span class="v-id">#{audit_id_ver}</span>
            <span class="v-icon">{s_hist['veredicto_icono']}</span>
            <span class="v-title" style="color: {vcolor};">{s_hist['veredicto']}</span>
            <span class="pill {pill_cls.get(s_hist['veredicto'], '')}">{s_hist['pct_coincidencia']}%</span>
            <div class="v-sub">
                🏪 {suc_name} &nbsp;·&nbsp;
                🕐 {datetime.fromisoformat(a['fecha']).strftime('%d/%m/%Y %H:%M')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Métricas
        st.markdown('<div class="section-label">Resumen</div>', unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("SKU Analizados", s_hist['total_sku'])
        m2.metric("Coinciden", f"{s_hist['coinciden']} ({s_hist['pct_coincidencia']}%)")
        m3.metric("Con Diferencias", s_hist['diferencias'])
        m4.metric("Diferencia Neta", f"{s_hist['diferencia_neta']:+,}")

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

        # Exportar + Eliminar
        st.markdown("---")
        col_exp, col_danger = st.columns([3, 1])
        with col_exp:
            st.markdown("### 💾 Exportar")
            reporte_hist = generar_reporte_txt(resultado_hist, a['sucursal'])
            st.download_button(
                "📄 Descargar Reporte (.txt)",
                data=reporte_hist,
                file_name=f"auditoria_#{audit_id_ver}_{a['sucursal'] or 'sucursal'}_{a['fecha'][:10]}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        with col_danger:
            st.markdown("### &nbsp;")
            with st.expander("🗑️ Eliminar"):
                st.warning("⚠️ No se puede deshacer.")
                if st.button("🗑️ Eliminar auditoría", use_container_width=True, type="primary"):
                    eliminar_auditoria(audit_id_ver)
                    st.session_state.audit_id_ver = None
                    st.cache_data.clear()
                    st.rerun()

        st.stop()

    # ─── NIVEL 2: Ver historial de una sucursal ───
    if st.session_state.get('sucursal_ver'):
        sucursal_nombre = st.session_state.sucursal_ver

        # Breadcrumb
        st.markdown(f"""
        <div class="breadcrumb">
            <span class="bc-link">🏪 Sucursales</span>
            <span class="bc-sep">›</span>
            <span class="bc-current">{sucursal_nombre}</span>
        </div>
        """, unsafe_allow_html=True)

        col_bc, _ = st.columns([1, 5])
        with col_bc:
            if st.button("← Todas las sucursales", type="secondary", use_container_width=True):
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

        # Resumen
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
        col_s4.metric("Resultados", f"✅{aprob} ⚠️{observ} 🔴{rechaz}")

        # Evolución
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

        # Timeline con botones estilizados
        for a in auditorias_suc:
            ver_cls = {"APROBADA": "aprobada", "OBSERVADA": "observada", "RECHAZADA": "rechazada"}
            css_class = ver_cls.get(a['veredicto'], "")
            icono = "✅" if a['veredicto'] == "APROBADA" else "⚠️" if a['veredicto'] == "OBSERVADA" else "🔴"
            pill_cls_v = {"APROBADA": "pill-green", "OBSERVADA": "pill-yellow", "RECHAZADA": "pill-red"}
            fecha = datetime.fromisoformat(a['fecha']).strftime('%d/%m/%Y %H:%M')

            st.markdown(f"""
            <div class="timeline-item {css_class}">
                <div class="tl-header">
                    <span class="tl-fecha">{fecha} · ID #{a['id']}</span>
                    <span class="tl-veredicto">{icono} {a['veredicto']}</span>
                    <span class="pill {pill_cls_v.get(a['veredicto'], '')}">{a['pct_coincidencia']}%</span>
                </div>
                <div class="tl-stats">
                    {a['coinciden']}/{a['total_sku']} OK ·
                    Falt: {a['faltantes']} · Sobr: {a['sobrantes']}
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_t1, col_t2 = st.columns([1, 1])
            with col_t1:
                if st.button("👁️ Ver detalle", key=f"ver_{a['id']}", type="primary",
                             use_container_width=True):
                    st.session_state.audit_id_ver = a['id']
                    st.rerun()
            with col_t2:
                if st.button("🗑️ Eliminar", key=f"del_{a['id']}", type="tertiary",
                             use_container_width=True):
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

        st.markdown("---")
        st.markdown("### 🎲 ¿Querés probar la app?")
        st.markdown(
            "<p style='color: #6b7280;'>Cargá datos de ejemplo para ver "
            "cómo funciona el panel de sucursales.</p>",
            unsafe_allow_html=True,
        )
        col_se1, col_se2 = st.columns([1, 1])
        with col_se1:
            if st.button("🎲 Cargar datos de ejemplo", type="primary", use_container_width=True):
                sembrar_datos_ejemplo()
                st.cache_data.clear()
                st.rerun()
        with col_se2:
            if st.button("🔄 Refrescar", type="secondary", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        st.stop()

    # Métrica global
    total_audits = sum(s['total_auditorias'] for s in sucursales)
    st.markdown(
        f"<p style='color: #6b7280;'>{total_audits} auditorías en "
        f"{len(sucursales)} sucursales</p>",
        unsafe_allow_html=True,
    )

    # Action bar
    col_r1, col_r2, col_r3 = st.columns([1, 1, 3])
    with col_r1:
        if st.button("🔄 Refrescar", type="secondary", use_container_width=True):
            st.cache_data.clear()
            st.session_state.audit_id_ver = None
            st.session_state.sucursal_ver = None
            st.rerun()
    with col_r2:
        if st.button("🗑️ Resetear DB", type="tertiary", use_container_width=True,
                     help="Borra todos los datos y recarga ejemplos"):
            conn = get_db()
            conn.execute("DELETE FROM diferencias")
            conn.execute("DELETE FROM auditorias")
            conn.commit()
            conn.close()
            st.cache_data.clear()
            st.session_state.audit_id_ver = None
            st.session_state.sucursal_ver = None
            sembrar_datos_ejemplo()
            st.rerun()

    st.markdown("---")

    # Grilla de sucursales — 2 o 3 cols según cantidad
    n_cols = min(3, max(2, len(sucursales)))
    cols_grilla = st.columns(n_cols)
    for i, s in enumerate(sucursales):
        with cols_grilla[i % n_cols]:
            nombre = s['sucursal'] if s['sucursal'] else '(Sin sucursal)'
            ultima = datetime.fromisoformat(s['ultima_fecha']).strftime('%d/%m/%Y') if s['ultima_fecha'] else '—'
            prom = s['promedio_coincidencia'] or 0

            # Icon class based on prom
            if prom >= 95:
                icon_cls, icon_letter = "green", "✓"
            elif prom >= 80:
                icon_cls, icon_letter = "yellow", "!"
            else:
                icon_cls, icon_letter = "red", "✗"

            st.markdown(f"""
            <div class="sucursal-card">
                <div class="sc-header">
                    <div class="sc-icon {icon_cls}">{icon_letter}</div>
                    <span class="sc-name">{nombre}</span>
                    <span class="sc-badge">{s['total_auditorias']}</span>
                </div>
                <div class="sc-meta">Última: {ultima}</div>
                <div class="sc-stats">
                    <div class="sc-stat">
                        <div class="val">{prom:.0f}%</div>
                        <div class="lbl">Promedio</div>
                    </div>
                    <div class="sc-stat">
                        <div class="val ok">{s['aprobadas']}</div>
                        <div class="lbl">✅ OK</div>
                    </div>
                    <div class="sc-stat">
                        <div class="val warn">{s['observadas']}</div>
                        <div class="lbl">⚠️ Obs</div>
                    </div>
                    <div class="sc-stat">
                        <div class="val bad">{s['rechazadas']}</div>
                        <div class="lbl">🔴 Rech</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Ver historial →", key=f"suc_{i}", type="primary",
                         use_container_width=True):
                st.session_state.sucursal_ver = s['sucursal']
                st.rerun()

# ─── Footer ───
st.markdown(
    '<div class="footer-badge">'
    'Agente de Auditoría de Inventarios v3.0 · Datos guardados en SQLite</div>',
    unsafe_allow_html=True,
)
