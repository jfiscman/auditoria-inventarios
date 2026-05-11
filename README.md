# 📦 Auditoría de Inventarios

App para comparar el **conteo físico** de una sucursal contra el **stock del sistema central** y generar reportes de auditoría.

Hecho con Python + Streamlit. Sin base de datos, sin instalación compleja.

---

## 🚀 Cómo usarla

### Opción 1 — Streamlit App (recomendada)

```bash
# 1. Instalá Python 3 si no lo tenés
# 2. Instalá Streamlit
pip3 install streamlit pandas

# 3. Ejecutá la app
python3 -m streamlit run auditoria_app.py
```

Se abre sola en el navegador en `http://localhost:8501`.

> **En macOS** también podés hacer doble-click en `Auditoria Inventarios.command`

### Opción 2 — Script CLI

```bash
python3 agente_auditor_inventario.py
```

Modo interactivo por terminal. También admite argumentos directos:

```bash
python3 agente_auditor_inventario.py fisico.csv central.csv -s "Sucursal Centro"
```

---

## 📋 Cómo funciona

| Paso | Acción |
|------|--------|
| 1 | Abrí la app en el navegador |
| 2 | Arrastrá los 2 CSVs (físico y central) |
| 3 | Verificá que las columnas SKU y cantidad se detectaron bien |
| 4 | Apretá **Ejecutar Auditoría** |
| 5 | Revisá el reporte y descargalo |

### Datos de ejemplo

La app incluye **archivos de ejemplo descargables**. Apretá los botones que dicen "Descargar ejemplo" para probar sin tener datos reales.

---

## 📊 Qué genera

- ✅ **Veredicto** — Aprobada (≥95%), Observada (≥80%), Rechazada (<80%)
- 🔴 **Faltantes** — productos con menos stock físico que en central
- 🟡 **Sobrantes** — productos con más stock físico que en central
- ❓ **No registrados** — productos que están en un lado pero no en el otro
- 📄 **Reporte .txt** descargable para firmar
- 📊 **CSV de diferencias** descargable para procesar

---

## 🧪 Ejemplo

Si descargás los archivos de ejemplo desde la app y los ejecutás, vas a ver un resultado como este:

| SKU | Físico | Central | Diferencia | Tipo |
|-----|--------|---------|-----------|------|
| LAP-002 | 3 | 5 | -2 | Faltante 🔴 |
| TEC-001 | 20 | 18 | +2 | Sobrante 🟡 |
| CAB-002 | — | 6 | — | Solo en central ❓ |
| AUD-001 | 10 | 12 | -2 | Faltante 🔴 |

---

## 📁 Archivos del proyecto

| Archivo | Qué es |
|---------|--------|
| `auditoria_app.py` | App Streamlit (interfaz web) |
| `agente_auditor_inventario.py` | Script CLI (terminal) |
| `Auditoria Inventarios.command` | Accesso directo macOS (doble-click) |
| `README.md` | Este archivo |

---

## 🛠️ Requisitos

- Python 3.8+
- streamlit
- pandas

```bash
pip3 install streamlit pandas
```
