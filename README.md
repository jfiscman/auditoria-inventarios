# 📦 Auditoría de Inventarios

> **App para auditar inventarios** — compará el conteo **físico** de una sucursal contra el **stock del sistema central** y obtené reportes de auditoría listos para firmar.

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.50+-red?logo=streamlit&logoColor=white)
![License](https://img.shields.io/badge/Licencia-MIT-green)

Hecho con Python + Streamlit. **Con memoria persistente**: todas las auditorías se guardan automáticamente y podés consultarlas cuando quieras.

---

## 📑 Índice

- [¿Qué hace esta herramienta?](#-qué-hace-esta-herramienta)
- [¿Qué necesito para usarla?](#-qué-necesito-para-usarla)
- [Descargar la herramienta](#-descargar-la-herramienta)
- [Instalación paso a paso](#-instalación-paso-a-paso)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Cómo usar la app](#-cómo-usar-la-app)
  - [Nueva auditoría](#-nueva-auditoría)
  - [Historial](#-historial-de-auditorías)
  - [Ver una auditoría guardada](#-ver-una-auditoría-guardada)
- [Entender los resultados](#-entender-los-resultados)
- [Formato de los archivos CSV](#-formato-de-los-archivos-csv)
- [Ejemplo completo](#-ejemplo-completo)
- [Solución de problemas](#-solución-de-problemas)
- [Archivos del proyecto](#-archivos-del-proyecto)

---

## 🎯 ¿Qué hace esta herramienta?

Esta app compara **dos listas de inventario** y te muestra las diferencias al instante:

| De un lado | Del otro |
|------------|----------|
| 📋 **Conteo físico** — lo que realmente hay en la sucursal (lo contás a mano) | 💻 **Stock central** — lo que dice el sistema que debería haber |

### ¿Para qué sirve?

- ✅ **Auditar sucursales** — verificá que el stock físico coincida con el del sistema
- 🔍 **Detectar faltantes** — productos que faltan en la sucursal (posible robo, pérdida o error)
- 🔍 **Detectar sobrantes** — productos de más (posible error de carga o movimiento no registrado)
- 📄 **Generar reportes** — obtené un documento listo para presentar y firmar

---

## 💻 ¿Qué necesito para usarla?

| Requisito | Detalle |
|-----------|---------|
| **Una computadora** | Windows, macOS o Linux |
| **Python 3.8 o superior** | [Descargar Python](https://www.python.org/downloads/) |
| **Conexión a internet** | Solo para la instalación inicial |
| **Tus archivos CSV** | El conteo físico y el stock del sistema |

> **No necesitas saber programar.** Seguí estos pasos y lo tenés funcionando en 5 minutos.

---

## 📥 Descargar la herramienta

Tenés dos formas de obtener los archivos:

### Opción 1 — ZIP (recomendada para el analista)

1. Entrá a [github.com/jfiscman/auditoria-inventarios](https://github.com/jfiscman/auditoria-inventarios)
2. Apretá el botón verde **`<> Code`** ▸ **`Download ZIP`**
3. Descomprimí el archivo en una carpeta (ej: `Escritorio/auditoria-inventarios`)

![Botón Code en GitHub](https://docs.github.com/assets/cb-20363/images/help/repository/code-button.png)

### Opción 2 — Git (si sabés usarlo)

```bash
git clone https://github.com/jfiscman/auditoria-inventarios.git
cd auditoria-inventarios
```

---

## 🔧 Instalación paso a paso

### Antes de empezar: ¿ya tenés Python?

Abrí una terminal y ejecutá este comando para ver si ya tenés Python instalado:

**Windows:**
```cmd
python --version
```

**macOS / Linux:**
```bash
python3 --version
```

**Si ves algo como** `Python 3.8.5` o superior → ya lo tenés. Saltá directo a la sección de tu sistema operativo para instalar Streamlit y ejecutar la app.

**Si ves** `'python' no se reconoce como un comando` o `command not found` → tenés que instalarlo. Seguí los pasos de abajo según tu sistema.

---

### Windows

#### 1. Instalar Python

1. Andá a [python.org/downloads](https://www.python.org/downloads/)
2. Apretá el botón amarillo **Download Python** (se descarga solo)
3. Ejecutá el archivo descargado (`.exe`)
4. **⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜**
   **☑️ IMPORTANTE: marcá "Add Python to PATH"** (en la PRIMERA pantalla)
   **⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜**
   Mirá bien: es un cuadrito en la PARTE DE ABAJO del instalador. Si no lo marcás, después los comandos no van a funcionar.
5. Apretá **Install Now**
6. Esperá a que termine y apretá **Close**

✅ **Verificá que quedó bien instalado:**
1. Abrí una terminal nueva (apretá `Windows + R`, escribí `cmd`, Enter)
2. Escribí `python --version`
3. **Tiene que aparecer** `Python 3.x.x` — si ves eso, está listo.

#### 2. Ir a la carpeta del proyecto

En la terminal (la ventana negra), escribí:

```cmd
cd Desktop\auditoria-inventarios
```

> 📝 Si la carpeta descomprimida está en otro lugar (ej: `Descargas`), escribí esa ruta. Por ejemplo: `cd C:\Users\tuusuario\Downloads\auditoria-inventarios`

#### 3. Instalar Streamlit y Pandas (un solo paso)

```cmd
pip install streamlit pandas
```

Esperá a que termine. Al final no debería mostrar errores.

#### 4. Ejecutar la app

```cmd
python -m streamlit run auditoria_app.py
```

Se va a abrir el navegador solo con la app lista para usar.

---

### macOS

#### 1. Verificar si ya tenés Python

Abrí la Terminal (buscá "Terminal" en la lupa arriba a la derecha) y ejecutá:

```bash
python3 --version
```

- ✅ Si ves `Python 3.8.x` o superior → ya lo tenés, saltá al paso 3.
- ❌ Si ves `command not found` → seguí con el paso 2.

#### 2. Instalar Python

**Opción recomendada — Instalador oficial (la más fácil):**

1. Andá a [python.org/downloads](https://www.python.org/downloads/)
2. Apretá **Download Python** (se descarga solo)
3. Ejecutá el archivo `.pkg` descargado
4. Seguí los pasos del instalador (todo siguiente-siguiente)
5. ✅ **Verificá:** abrí una Terminal NUEVA y ejecutá `python3 --version`. Tiene que mostrar la versión.

**Opción alternativa — Con Homebrew (si ya lo tenés instalado):**

```bash
brew install python@3.12
```

#### 3. Ir a la carpeta del proyecto

```bash
cd ~/Desktop/auditoria-inventarios
```

> 💡 **Tip:** si moviste la carpeta a otro lado, escribí `cd ` (con espacio al final) y arrastrá la carpeta desde el Finder a la terminal — se completa la ruta sola.

#### 4. Instalar Streamlit y Pandas (un solo paso)

```bash
pip3 install streamlit pandas
```

#### 5. Ejecutar la app

```bash
python3 -m streamlit run auditoria_app.py
```

Se abre el navegador automáticamente en `http://localhost:8501`. La app queda corriendo mientras la uses. Cuando termines, apretá `Ctrl + C` en la terminal para cerrarla.

#### 6. (Alternativa) Doble-click en el archivo .command

En la carpeta del proyecto hay un archivo llamado **`Auditoria Inventarios.command`**. Hacé doble-click y se abre todo solo (sin necesidad de escribir comandos).

> 💡 **Tip:** si al hacer doble-click no se abre, abrí Terminal y ejecutá esto una sola vez:
> ```bash
> chmod +x "Auditoria Inventarios.command"
> ```

---

### Linux

```bash
# 1. Instalar Python y pip (solo si no lo tenés)
# Debian / Ubuntu / Linux Mint
sudo apt update
sudo apt install python3 python3-pip -y

# Fedora / CentOS / RHEL
# sudo dnf install python3 python3-pip -y

# 2. Verificar que quedó bien
python3 --version
# Debería mostrar: Python 3.x.x

# 3. Ir a la carpeta del proyecto
cd ~/Descargas/auditoria-inventarios

# 4. Instalar Streamlit y Pandas
pip3 install streamlit pandas

# 5. Ejecutar la app
python3 -m streamlit run auditoria_app.py
```

---

## 📖 Cómo usar la app

### Pantalla principal

Cuando abras la app vas a ver:

```
┌─────────────────────────────────────────────┐
│  📦 Auditoría de Inventarios               │
│  Subí los dos archivos CSV para empezar     │
│                                             │
│  [📋 Conteo FÍSICO]  [💻 Stock CENTRAL]    │
│  (arrastrá el archivo)  (arrastrá el arch.)│
│                                             │
│  📥 ¿No tenés archivos a mano?             │
│  [Descargar ejemplo FÍSICO] [Central]      │
└─────────────────────────────────────────────┘
```

### Paso a paso

#### 1️⃣ Descargar los ejemplos (opcional)

Si es la primera vez que usás la app, apretá los botones **"Descargar ejemplo"** que aparecen en la pantalla. Se van a bajar dos archivos:

| Archivo | Contenido |
|---------|-----------|
| `ejemplo_conteo_fisico.csv` | Lo que contó el analista en la sucursal |
| `ejemplo_stock_central.csv` | Lo que dice el sistema central |

#### 2️⃣ Subir los archivos

Arrastrá cada archivo CSV a su recuadro correspondiente:

- **Conteo FÍSICO** → el archivo con lo que contaste en la sucursal
- **Stock CENTRAL** → el archivo con lo que dice el sistema

Podés hacer click en el recuadro para buscar el archivo, o arrastrarlo directamente.

#### 3️⃣ Verificar las columnas

La app detecta automáticamente qué columna es el **SKU** (código del producto) y cuál es la **cantidad**. Si no son las correctas, las podés cambiar con los selectores:

```
⚙️ Columnas para la comparación

SKU (físico)    ┌──────────┐   Cantidad (físico) ┌──────────┐
                │   sku    │                      │ cantidad │
                └──────────┘                      └──────────┘

SKU (central)   ┌──────────┐   Cantidad (central) ┌──────────┐
                │   sku    │                      │ cantidad │
                └──────────┘                      └──────────┘
```

#### 4️⃣ Nombrar la sucursal (opcional)

Escribí el nombre de la sucursal que estás auditando. Aparecerá en el reporte y en el historial para que después puedas encontrar esta auditoría fácilmente.

#### 5️⃣ Ejecutar la auditoría

Apretá el botón **▶️ Ejecutar Auditoría**. En segundos ves los resultados.

> 💾 **La auditoría se guarda automáticamente** con todos los datos. Podés cerrar la app, volver a abrirla después y consultar esta auditoría desde el **historial**.

---

### 📋 Historial de auditorías

Todas las auditorías que ejecutes quedan guardadas automáticamente en una base de datos. Para consultarlas:

1. Andá a la pestaña **📋 Historial** (arriba a la izquierda)
2. Usá los filtros para buscar por **sucursal** o por **resultado** (Aprobada/Observada/Rechazada)
3. Cada auditoría se muestra como una tarjeta con su resultado y fecha

```
┌──────────────────────────────────────────────────┐
│  📋 Auditorías guardadas                         │
│                                                   │
│  🔍 Filtrar por sucursal: [Sucursal Centro     ] │
│  Filtrar por resultado: [Todas                ▼] │
│                                                   │
│  ┌────────────────────────────────────────────────┐│
│  │ ✅ Sucursal Centro          [👁️ Ver] [🗑️]  ││
│  │   15/01/2025 10:30 · ID #1                    ││
│  │   8/12 OK (66.7%) · Falt: 2 · Sobr: 1        ││
│  └────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────┐│
│  │ 🔴 Sucursal Norte             [👁️ Ver] [🗑️] ││
│  │   14/01/2025 16:45 · ID #2                    ││
│  │   5/10 OK (50%) · Falt: 3 · Sobr: 1          ││
│  └────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────┘
```

Las tarjetas tienen un color en el borde izquierdo que indica el resultado:
- **Verde** ✅ → Aprobada
- **Naranja** ⚠️ → Observada
- **Rojo** 🔴 → Rechazada

> 💡 **Tip:** si tenés muchas auditorías, usá el filtro por sucursal para encontrar rápidamente una en particular.

### 👁️ Ver una auditoría guardada

Apretá el botón **👁️ Ver** en cualquier tarjeta del historial para ver el detalle completo:

- ✅ **Veredicto** igual que cuando la ejecutaste
- 📊 **Métricas** completas
- 🔴 **Faltantes** y **sobrantes** con sus cantidades
- 🧾 **Exportar** el reporte de nuevo
- 🗑️ **Eliminar** la auditoría si ya no la necesitás

Para volver al listado general, apretá **← Volver al historial**.

---

## 📊 Entender los resultados

### Veredicto general

Arriba de todo aparece un cartel con el resultado general:

| Veredicto | Color | Coincidencia | Qué significa |
|-----------|-------|--------------|---------------|
| ✅ **APROBADA** | Verde | ≥ 95% | Está todo bien, diferencias mínimas |
| ⚠️ **OBSERVADA** | Naranja | 80% – 94% | Hay diferencias que revisar |
| 🔴 **RECHAZADA** | Rojo | < 80% | Hay que investigar, muchas diferencias |

### Métricas principales

```
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ SKU Anal.│  │Coinciden │  │Con Diff. │  │Diff Neta │
│    12    │  │  6 (50%) │  │    6     │  │    -3    │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

- **SKU Analizados:** cantidad de productos distintos encontrados
- **Coinciden:** cuántos productos tienen el mismo stock en físico y central
- **Con Diferencias:** cuántos productos no coinciden (sobrantes + faltantes)
- **Diferencia Neta:** total de unidades de diferencia (físico − central)

### Tablas de detalle

#### 🔴 Faltantes
Productos que **faltan** en la sucursal (el sistema dice que hay más de lo que contaste).

| SKU | Físico | Central | Diferencia |
|-----|--------|---------|-----------|
| LAP-002 | 3 | 5 | **-2** |

> **Posibles causas:** robo, pérdida, extravío, error al cargar el sistema, error al contar.

#### 🟡 Sobrantes
Productos que **sobran** en la sucursal (contaste más de lo que dice el sistema).

| SKU | Físico | Central | Diferencia |
|-----|--------|---------|-----------|
| TEC-001 | 20 | 18 | **+2** |

> **Posibles causas:** reposición no registrada, devolución no cargada, error al contar.

#### ❓ En físico, no registrados en central
Productos que **existen físicamente** pero no aparecen en el sistema central.

| SKU | Cantidad Físico |
|-----|----------------|
| MOU-003 | 3 |

> **Posibles causas:** producto nuevo no cargado, error de carga, código mal registrado.

#### ❓ En central, no registrados en físico
Productos que **están en el sistema** pero no aparecieron en el conteo físico.

| SKU | Cantidad Central |
|-----|----------------|
| CAB-002 | 6 |

> **Posibles causas:** no se contó ese producto, se agotó y no se actualizó, está en otra ubicación.

### Exportar resultados

Al final de la página hay botones para descargar:

| Botón | Formato | Contenido |
|-------|---------|-----------|
| 📄 **Reporte** | `.txt` | Reporte completo listo para firmar en papel |
| 📊 **Diferencias** | `.csv` | Solo los productos con diferencias (para Excel) |
| 📋 **Datos completos** | `.csv` | Todos los productos con su clasificación |

---

## 📋 Formato de los archivos CSV

### Estructura básica

Cada archivo debe tener **al menos dos columnas**:

| Columna | Contenido | Ejemplo |
|---------|-----------|---------|
| **SKU** | Código único del producto | `LAP-001`, `ABC-123`, `PROD-0456` |
| **Cantidad** | Unidades existentes | `5`, `12`, `0` |

### Ejemplo de archivo válido

```csv
sku,cantidad
LAP-001,10
LAP-002,5
MON-001,12
TEC-001,20
```

> 📝 El separador debe ser **coma** (`,`). Si tu sistema genera archivos con punto y coma (`;`), abrí el CSV en un editor de texto y reemplazá `;` por `,`.

### Columnas que la app reconoce automáticamente

**Para SKU:**
`sku`, `codigo`, `código`, `cod`, `producto`, `id`, `codigo_producto`, `código_producto`, `articulo`, `artículo`, `sku_producto`

**Para cantidad:**
`cantidad`, `stock`, `existencia`, `existencias`, `unidades`, `qty`, `cant`, `inv`, `inventario`, `saldo`, `cantidad_existente`

### Columnas adicionales

Los archivos pueden tener **más columnas** de las necesarias (ej: precio, categoría, ubicación). La app solo usa SKU y cantidad, el resto las ignora.

### Formatos especiales soportados

| Formato | Original | Lo interpreta como |
|---------|----------|-------------------|
| Puntos de miles | `1.234` | `1234` |
| Coma decimal | `1,5` | `1.5` → redondea a `2` |
| Celdas vacías | `""` | `0` |

> 💡 **Para sacar del sistema central:** exportá el listado de stock a CSV. La mayoría de los sistemas tienen una opción "Exportar a Excel" o "Exportar a CSV". Si te da un Excel (.xlsx), abrilo y guardalo como CSV.

---

## 🧪 Ejemplo completo

### Descargar los ejemplos

1. Abrí la app
2. En la pantalla principal, apretá los botones **"Descargar ejemplo"**
3. Se descargan dos archivos: `ejemplo_conteo_fisico.csv` y `ejemplo_stock_central.csv`

### Subirlos a la app

Arrastrá cada uno a su recuadro correspondiente y apretá **Ejecutar Auditoría**.

### Resultado esperado

```
✅ APROBADA — Sin diferencias significativas.

📊 Resumen
  SKU analizados:      14
  Coinciden:            9  (64.3%)
  Con diferencias:      5
  
🔴 Faltantes:
  LAP-002  → Físico: 3  / Central: 5   → Faltan 2
  AUD-001  → Físico: 10 / Central: 12  → Faltan 2
  WEB-002  → Físico: 7  / Central: 10  → Faltan 3

🟡 Sobrantes:
  TEC-001  → Físico: 20 / Central: 18  → Sobran 2

❓ En central, no en físico:
  CAB-002  → 6 unidades
  DIS-002  → 4 unidades
```

---

## 🔧 Solución de problemas

### ❌ "No se encuentra el comando streamlit"

**Causa:** Streamlit no está instalado.

**Solución:**
```bash
pip3 install streamlit pandas
```

Si usás Windows:
```cmd
pip install streamlit pandas
```

---

### ❌ "pip no se reconoce como un comando" (Windows)

**Causa:** Python no está en el PATH.

**Solución:** Reinstalá Python y asegurate de marcar **"Add Python to PATH"** durante la instalación.

---

### ❌ "Permission denied" o "No puedes escribir"

**Causa:** Falta permiso para instalar paquetes.

**Solución:** Agregá `--user` al final:
```bash
pip3 install --user streamlit pandas
```

---

### ❌ "El archivo no tiene las columnas que esperaba"

**Causa:** Las columnas se llaman distinto o el separador no es coma.

**Solución:** En la app, usá los selectores para elegir manualmente qué columna es SKU y cuál es cantidad.

---

### ❌ "Error al leer el CSV"

**Causa:** El archivo no es un CSV válido (quizás es un Excel `.xlsx`).

**Solución:**
1. Abrí el archivo en Excel
2. Andá a **Archivo** ▸ **Guardar como**
3. Elegí **CSV (delimitado por comas)** (*.csv)
4. Probá de nuevo

---

### ❌ "La app no se abre en el navegador"

**Causa:** Streamlit arrancó pero no abrió el navegador automáticamente.

**Solución:** Abrí el navegador manualmente y andá a:
```
http://localhost:8501
```

---

### ❌ "Puerto 8501 en uso"

**Causa:** Ya hay una instancia de Streamlit corriendo.

**Solución:** Cerrala con `Ctrl + C` en la terminal donde la ejecutaste, o usá otro puerto:
```bash
python3 -m streamlit run auditoria_app.py --server.port 8502
```

---

### ❌ "Error de sintaxis en la terminal" (Windows)

**Causa:** Usar `python3` en vez de `python`.

**Solución:** En Windows siempre usá `python` (sin el 3):
```cmd
python -m streamlit run auditoria_app.py
```

---

## 📁 Archivos del proyecto

| Archivo | Qué es |
|---------|--------|
| `auditoria_app.py` | 🖥️ **App principal** — interfaz web con Streamlit (modo recomendado) |
| `agente_auditor_inventario.py` | ⌨️ **Script por terminal** — alternativa sin interfaz gráfica |
| `Auditoria Inventarios.command` | 🖱️ **Accesso directo macOS** — doble-click para abrir la app |
| `README.md` | 📖 **Este archivo** — instrucciones completas |

> 💡 **Usá siempre `auditoria_app.py`** (la app web). El script de terminal es solo para casos donde no haya navegador disponible.

---

## 🛠️ Requisitos técnicos

| Requisito | Versión mínima |
|-----------|---------------|
| Python | 3.8 |
| streamlit | 1.28 |
| pandas | 1.5 |

### Instalación limpia (opcional)

Si querés evitar conflictos con otros programas, podés crear un entorno virtual:

```bash
# Crear el entorno
python3 -m venv venv

# Activarlo
source venv/bin/activate        # macOS / Linux
# o
venv\Scripts\activate           # Windows

# Instalar dependencias
pip3 install streamlit pandas

# Ejecutar
python3 -m streamlit run auditoria_app.py
```

---

## 📄 Licencia

MIT — podés usar, modificar y distribuir libremente.

---

<div align="center">
Hecho con ❤️ para equipos de auditoría · Reportá problemas en <a href="https://github.com/jfiscman/auditoria-inventarios/issues">GitHub Issues</a>
</div>
