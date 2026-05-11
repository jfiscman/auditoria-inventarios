#!/usr/bin/env python3
"""
Agente de Auditoría de Inventarios
===================================
Compara el inventario físico de una sucursal (conteo real)
contra el stock registrado en el sistema central.

Uso:
  python agente_auditor_inventario.py
    → Modo interactivo con menú paso a paso

  python agente_auditor_inventario.py fisico.csv central.csv
    → Comparación directa, exporta reporte automáticamente

  python agente_auditor_inventario.py fisico.csv central.csv --output reporte.xlsx
    → Especifica archivo de salida

  python agente_auditor_inventario.py fisico.csv central.csv --sku-col "codigo" --qty-col "stock"
    → Columnas personalizadas si no se llaman "sku" / "cantidad"
"""

import csv
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime


# ─────────────────────────────────────────────
#  Núcleo de comparación
# ─────────────────────────────────────────────

def leer_csv(ruta: str, cols=None) -> tuple[list[dict], list[str]]:
    """Lee un CSV y devuelve (filas, nombres_de_columnas)."""
    with open(ruta, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            print(f"❌ Error: el archivo '{ruta}' está vacío o no tiene encabezados.")
            sys.exit(1)
        filas = list(reader)
    if not filas:
        print(f"⚠️  Advertencia: '{ruta}' no tiene filas de datos.")
    return filas, reader.fieldnames


def detectar_columnas(filas: list[dict], columnas: list[str],
                      clave: str, cantidad: str, etiqueta: str):
    """
    Detecta / valida las columnas de SKU y cantidad.
    Si el usuario no las pasa explícitamente, intenta inferirlas.
    """
    cols_lower = {c.lower().strip() for c in columnas}

    # ── Columna SKU ──
    sku_col = clave
    if not sku_col:
        candidatos_sku = [c for c in columnas
                          if c.lower().strip() in ('sku', 'codigo', 'código',
                                                   'cod', 'producto', 'id',
                                                   'codigo_producto', 'código_producto',
                                                   'articulo', 'artículo')]
        if not candidatos_sku:
            # Usar la primera columna como fallback
            sku_col = columnas[0]
            print(f"  ⚠️  No se detectó columna de SKU en {etiqueta}. "
                  f"Usando '{sku_col}' como clave.")
        else:
            sku_col = candidatos_sku[0]

    if sku_col not in columnas:
        print(f"❌ Error: columna '{sku_col}' no encontrada en {etiqueta}.\n"
              f"   Columnas disponibles: {', '.join(columnas)}")
        sys.exit(1)

    # ── Columna cantidad ──
    qty_col = cantidad
    if not qty_col:
        candidatos_qty = [c for c in columnas
                          if c.lower().strip() in ('cantidad', 'stock', 'existencia',
                                                   'existencias', 'unidades', 'qty',
                                                   'cant', 'inv', 'inventario',
                                                   'cantidad_existente', 'saldo')]
        if not candidatos_qty:
            qty_col = [c for c in columnas if c != sku_col][0]
            print(f"  ⚠️  No se detectó columna de cantidad en {etiqueta}. "
                  f"Usando '{qty_col}'.")
        else:
            qty_col = candidatos_qty[0]

    if qty_col not in columnas:
        print(f"❌ Error: columna '{qty_col}' no encontrada en {etiqueta}.\n"
             f"   Columnas disponibles: {', '.join(columnas)}")
        sys.exit(1)

    return sku_col, qty_col


def parse_cantidad(valor) -> int:
    """Convierte string a entero, tolerando puntos, comas y espacios."""
    if valor is None:
        return 0
    v = str(valor).strip()
    if not v:
        return 0
    # Sacar puntos de miles (ej. 1.234 → 1234)
    v = v.replace('.', '').replace(',', '.')
    try:
        return int(float(v))
    except ValueError:
        return 0


def comparar(fisico: list[dict], central: list[dict],
             sku_col_f: str, qty_col_f: str,
             sku_col_c: str, qty_col_c: str
             ) -> dict:
    """
    Compara físico vs central y devuelve un dict estructurado.
    """
    # Indexar central por SKU
    central_idx = {}
    for row in central:
        sku = str(row.get(sku_col_c, '')).strip()
        if not sku:
            continue
        if sku not in central_idx:
            central_idx[sku] = 0
        central_idx[sku] += parse_cantidad(row.get(qty_col_c))

    # Indexar físico por SKU
    fisico_idx = {}
    for row in fisico:
        sku = str(row.get(sku_col_f, '')).strip()
        if not sku:
            continue
        if sku not in fisico_idx:
            fisico_idx[sku] = 0
        fisico_idx[sku] += parse_cantidad(row.get(qty_col_f))

    # Comparar
    todos_skus = set(fisico_idx) | set(central_idx)

    coinciden = []
    diferencias = []
    solo_fisico = []   # están en físico pero no en sistema
    solo_central = []  # están en sistema pero no en físico
    total_fisico = 0
    total_central = 0

    for sku in sorted(todos_skus):
        q_fisico = fisico_idx.get(sku, 0)
        q_central = central_idx.get(sku, 0)
        total_fisico += q_fisico
        total_central += q_central
        diff = q_fisico - q_central

        if not sku in central_idx:
            solo_fisico.append((sku, q_fisico))
        elif not sku in fisico_idx:
            solo_central.append((sku, q_central))
        elif diff == 0:
            coinciden.append((sku, q_fisico))
        else:
            diferencias.append((sku, q_fisico, q_central, diff))

    # Clasificar diferencias
    sobrantes = [(s, f, c, d) for s, f, c, d in diferencias if d > 0]
    faltantes = [(s, f, c, d) for s, f, c, d in diferencias if d < 0]

    stats = {
        'total_sku_unicos': len(todos_skus),
        'coinciden': len(coinciden),
        'diferencias': len(diferencias),
        'solo_fisico': len(solo_fisico),
        'solo_central': len(solo_central),
        'sobrantes_count': len(sobrantes),
        'faltantes_count': len(faltantes),
        'total_fisico': total_fisico,
        'total_central': total_central,
        'diferencia_total': total_fisico - total_central,
        'pct_coincidencia': (len(coinciden) / len(todos_skus) * 100)
                            if todos_skus else 0,
    }

    return {
        'stats': stats,
        'coinciden': coinciden,
        'sobrantes': sobrantes,
        'faltantes': faltantes,
        'solo_fisico': solo_fisico,
        'solo_central': solo_central,
    }


# ─────────────────────────────────────────────
#  Reportes
# ─────────────────────────────────────────────

def generar_reporte_texto(resultado: dict, nombre_sucursal: str = "") -> str:
    """Genera un reporte de auditoría en texto plano."""
    s = resultado['stats']
    lines = []
    lines.append("=" * 64)
    lines.append("  REPORTE DE AUDITORÍA DE INVENTARIO")
    if nombre_sucursal:
        lines.append(f"  Sucursal: {nombre_sucursal}")
    lines.append(f"  Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 64)
    lines.append("")
    lines.append("📊  RESUMEN")
    lines.append("-" * 40)
    lines.append(f"  SKU únicos analizados:    {s['total_sku_unicos']:>6}")
    lines.append(f"  Coinciden (sin diff):     {s['coinciden']:>6}  ({s['pct_coincidencia']:.1f}%)")
    lines.append(f"  Con diferencias:           {s['diferencias']:>6}")
    lines.append(f"  → Sobrantes (físico > central): {s['sobrantes_count']:>6}")
    lines.append(f"  → Faltantes (central > físico): {s['faltantes_count']:>6}")
    lines.append(f"  No encontrados en central:      {s['solo_central']:>6}")
    lines.append(f"  No encontrados en físico:       {s['solo_fisico']:>6}")
    lines.append("")
    lines.append(f"  Total unidades físicas:    {s['total_fisico']:>8}")
    lines.append(f"  Total unidades central:    {s['total_central']:>8}")
    lines.append(f"  Diferencia neta:           {s['diferencia_total']:>8}")
    lines.append("")

    if resultado['faltantes']:
        lines.append("🔴  FALTANTES  (stock central > conteo físico)")
        lines.append("-" * 64)
        lines.append(f"  {'SKU':<25} {'Físico':>8} {'Central':>8} {'Diferencia':>10}")
        lines.append("  " + "-" * 55)
        for sku, fisico, central, diff in resultado['faltantes']:
            lines.append(f"  {sku:<25} {fisico:>8} {central:>8} {diff:>10}")
        lines.append("")

    if resultado['sobrantes']:
        lines.append("🟡  SOBRANTES  (conteo físico > stock central)")
        lines.append("-" * 64)
        lines.append(f"  {'SKU':<25} {'Físico':>8} {'Central':>8} {'Diferencia':>10}")
        lines.append("  " + "-" * 55)
        for sku, fisico, central, diff in resultado['sobrantes']:
            lines.append(f"  {sku:<25} {fisico:>8} {central:>8} {diff:>10}")
        lines.append("")

    if resultado['solo_fisico']:
        lines.append("❓  EN FÍSICO NO REGISTRADOS EN CENTRAL")
        lines.append("-" * 40)
        lines.append(f"  {'SKU':<25} {'Cantidad':>8}")
        lines.append("  " + "-" * 35)
        for sku, qty in resultado['solo_fisico']:
            lines.append(f"  {sku:<25} {qty:>8}")
        lines.append("")

    if resultado['solo_central']:
        lines.append("❓  EN CENTRAL NO REGISTRADOS EN FÍSICO")
        lines.append("-" * 40)
        lines.append(f"  {'SKU':<25} {'Cantidad':>8}")
        lines.append("  " + "-" * 35)
        for sku, qty in resultado['solo_central']:
            lines.append(f"  {sku:<25} {qty:>8}")
        lines.append("")

    # Marcas para aprobación
    if s['diferencias'] == 0 and s['solo_fisico'] == 0 and s['solo_central'] == 0:
        lines.append("✅  AUDITORÍA APROBADA — Sin diferencias detectadas.")
    elif s['pct_coincidencia'] >= 95:
        lines.append("✅  AUDITORÍA APROBADA (≥95% coincidencia)")
    elif s['pct_coincidencia'] >= 80:
        lines.append("⚠️  AUDITORÍA OBSERVADA (≥80% coincidencia — revisar diferencias)")
    else:
        lines.append("🔴  AUDITORÍA RECHAZADA (<80% coincidencia — requiere investigación)")

    lines.append("")
    lines.append("=" * 64)
    # Firmas
    lines.append("")
    lines.append("  Auditor: ___________________________")
    lines.append("  Fecha:   ___________________________")
    lines.append("")
    return "\n".join(lines)


def exportar_csv(resultado: dict, ruta_salida: str):
    """Exporta las diferencias a un CSV consolidado."""
    fieldnames = ['SKU', 'cantidad_fisico', 'cantidad_central',
                  'diferencia', 'tipo']
    with open(ruta_salida, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for sku, fisico, central, diff in resultado['faltantes']:
            writer.writerow({
                'SKU': sku,
                'cantidad_fisico': fisico,
                'cantidad_central': central,
                'diferencia': diff,
                'tipo': 'FALTANTE',
            })
        for sku, fisico, central, diff in resultado['sobrantes']:
            writer.writerow({
                'SKU': sku,
                'cantidad_fisico': fisico,
                'cantidad_central': central,
                'diferencia': diff,
                'tipo': 'SOBRANTE',
            })
        for sku, qty in resultado['solo_fisico']:
            writer.writerow({
                'SKU': sku,
                'cantidad_fisico': qty,
                'cantidad_central': 0,
                'diferencia': qty,
                'tipo': 'SOLO_FISICO',
            })
        for sku, qty in resultado['solo_central']:
            writer.writerow({
                'SKU': sku,
                'cantidad_fisico': 0,
                'cantidad_central': qty,
                'diferencia': -qty,
                'tipo': 'SOLO_CENTRAL',
            })


# ─────────────────────────────────────────────
#  Modo interactivo (menú)
# ─────────────────────────────────────────────

def modo_interactivo():
    print("")
    print("╔══════════════════════════════════════════════╗")
    print("║   🧾  AGENTE DE AUDITORÍA DE INVENTARIO     ║")
    print("║   Comparación Físico vs. Sistema Central    ║")
    print("╚══════════════════════════════════════════════╝")
    print("")

    # ── Archivos ──
    fisico_path = input("📁  Ruta del CSV de conteo FÍSICO: ").strip().strip('"\'')
    while not os.path.isfile(fisico_path):
        print("  ❌ Archivo no encontrado.")
        fisico_path = input("📁  Ruta del CSV de conteo FÍSICO: ").strip().strip('"\'')

    central_path = input("📁  Ruta del CSV de STOCK CENTRAL: ").strip().strip('"\'')
    while not os.path.isfile(central_path):
        print("  ❌ Archivo no encontrado.")
        central_path = input("📁  Ruta del CSV de STOCK CENTRAL: ").strip().strip('"\'')

    # ── Sucursal ──
    sucursal = input("🏪  Nombre de la sucursal (opcional): ").strip()

    print("")
    print("📋  Leyendo archivos...")

    # Leer ambos CSVs
    fisico, cols_f = leer_csv(fisico_path)
    central, cols_c = leer_csv(central_path)

    print(f"\n  ✓ Físico:   {len(fisico)} filas | Columnas: {', '.join(cols_f)}")
    print(f"  ✓ Central:  {len(central)} filas | Columnas: {', '.join(cols_c)}")
    print("")

    # ── Columnas ──
    print("🔍  Detectar columnas automáticamente? (s/N): ", end="")
    auto = input().strip().lower() in ('s', 'si', 'sí', 'y', 'yes')

    sku_col_f, qty_col_f = None, None
    sku_col_c, qty_col_c = None, None

    if not auto:
        sku_col_f = input(f"  Columna SKU en físico     (default: detectar): ").strip() or None
        qty_col_f = input(f"  Columna cantidad en físico (default: detectar): ").strip() or None
        sku_col_c = input(f"  Columna SKU en central    (default: detectar): ").strip() or None
        qty_col_c = input(f"  Columna cantidad en central (default: detectar): ").strip() or None

    print("\n🔎  Analizando...\n")

    sku_col_f, qty_col_f = detectar_columnas(fisico, cols_f, sku_col_f, qty_col_f, "físico")
    sku_col_c, qty_col_c = detectar_columnas(central, cols_c, sku_col_c, qty_col_c, "central")

    print(f"\n  SKU → físico:   '{sku_col_f}'   |   central:   '{sku_col_c}'")
    print(f"  Cant → físico:  '{qty_col_f}'   |   central:   '{qty_col_c}'")
    print("")

    # ── Comparar ──
    resultado = comparar(fisico, central, sku_col_f, qty_col_f, sku_col_c, qty_col_c)

    # ── Mostrar reporte ──
    reporte = generar_reporte_texto(resultado, sucursal)
    print(reporte)

    # ── Exportar ──
    print("\n💾  Exportar resultados?")
    print("     1) Reporte de texto (.txt)")
    print("     2) Diferencias en CSV (.csv)")
    print("     3) Ambos")
    print("     0) No exportar")
    opc = input("  Opción: ").strip()

    base = f"auditoria_{sucursal or 'sucursal'}_{datetime.now():%Y%m%d_%H%M%S}"

    if opc in ('1', '3'):
        ruta_txt = f"{base}.txt"
        with open(ruta_txt, 'w', encoding='utf-8') as f:
            f.write(reporte)
        print(f"  ✅ Reporte guardado: {ruta_txt}")

    if opc in ('2', '3'):
        ruta_csv = f"{base}_diferencias.csv"
        exportar_csv(resultado, ruta_csv)
        print(f"  ✅ Diferencias exportadas: {ruta_csv}")

    print("\n✅  Auditoría completa.")


# ─────────────────────────────────────────────
#  Modo CLI (argumentos directos)
# ─────────────────────────────────────────────

def modo_cli(args):
    print("")
    print("🔎  AUDITORÍA DE INVENTARIO (modo directo)")
    print("")

    fisico, cols_f = leer_csv(args.fisico)
    central, cols_c = leer_csv(args.central)

    print(f"  Físico:  '{args.fisico}' → {len(fisico)} filas | {', '.join(cols_f)}")
    print(f"  Central: '{args.central}' → {len(central)} filas | {', '.join(cols_c)}")
    print("")

    sku_col_f, qty_col_f = detectar_columnas(fisico, cols_f,
                                              args.sku_col, args.qty_col, "físico")
    sku_col_c, qty_col_c = detectar_columnas(central, cols_c,
                                              args.sku_col, args.qty_col, "central")

    resultado = comparar(fisico, central, sku_col_f, qty_col_f, sku_col_c, qty_col_c)
    reporte = generar_reporte_texto(resultado, args.sucursal)
    print(reporte)

    # Exportar
    base = args.output or f"auditoria_{args.sucursal or 'sucursal'}_{datetime.now():%Y%m%d_%H%M%S}"
    ruta_txt = f"{base}.txt"
    with open(ruta_txt, 'w', encoding='utf-8') as f:
        f.write(reporte)
    print(f"  ✅ Reporte guardado: {ruta_txt}")

    ruta_csv = f"{base}_diferencias.csv"
    exportar_csv(resultado, ruta_csv)
    print(f"  ✅ Diferencias exportadas: {ruta_csv}")
    print("")


# ─────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Agente de Auditoría de Inventarios — compara conteo físico vs. stock central",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                                   → Modo interactivo
  %(prog)s fisico.csv central.csv            → Comparación directa
  %(prog)s fisico.csv central.csv -s Suc01   → Con nombre de sucursal
  %(prog)s fisico.csv central.csv --sku-col codigo --qty-col stock
        """,
    )
    parser.add_argument('fisico', nargs='?', help='CSV con conteo físico de la sucursal')
    parser.add_argument('central', nargs='?', help='CSV con stock del sistema central')
    parser.add_argument('-s', '--sucursal', default='', help='Nombre de la sucursal')
    parser.add_argument('--sku-col', default='', help='Nombre de la columna SKU (en ambos CSVs)')
    parser.add_argument('--qty-col', default='', help='Nombre de la columna de cantidad (en ambos CSVs)')
    parser.add_argument('-o', '--output', default='', help='Nombre base para archivos de salida (sin extensión)')

    args = parser.parse_args()

    if args.fisico and args.central:
        modo_cli(args)
    else:
        modo_interactivo()


if __name__ == '__main__':
    main()
