import re
import subprocess
import sys
import time
from collections import Counter

import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

options = webdriver.FirefoxOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-extensions")
options.set_preference("browser.cache.disk.enable", False)
options.set_preference("browser.cache.memory.enable", False)
options.set_preference("network.http.use-cache", False)

RATIO_CHART = 7
RATIO_TABLE = 3

def asegurar_streamlit():
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is None:
            subprocess.run([sys.executable, "-m", "streamlit", "run", __file__], check=False)
            sys.exit(0)
    except Exception:
        pass

asegurar_streamlit()

st.set_page_config(
    page_title="Game Trends",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def nuevo_driver(intentos=3):
    for i in range(intentos):
        try:
            driver = webdriver.Firefox(options=options)
            driver.set_page_load_timeout(30)
            return driver
        except Exception:
            if i == intentos - 1:
                raise
            time.sleep(2)

def saltar_edad(driver):
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "ageYear")))
        Select(driver.find_element(By.ID, "ageYear")).select_by_value("2000")
        driver.find_element(By.ID, "view_product_page_btn").click()
        time.sleep(5)
    except Exception:
        pass

def scrapear_populares(max_items=10):
    driver = nuevo_driver()
    resultados = []
    try:
        try:
            driver.get("https://steamdb.info/")
        except Exception:
            driver.quit()
            driver = nuevo_driver()
            driver.get("https://steamdb.info/")
        juegos = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        for juego in juegos[:max_items]:
            columnas = juego.find_elements(By.TAG_NAME, "td")
            if len(columnas) < 2:
                continue
            enlace = None
            try:
                enlace = juego.find_element(By.CSS_SELECTOR, "a[href*='/app/']")
            except Exception:
                enlace = None
            nombre = enlace.text.strip() if enlace is not None else ""
            if not nombre:
                for celda in columnas:
                    texto = celda.text.strip()
                    if texto and not re.fullmatch(r"[\d,.]+[kKmM]?", texto):
                        nombre = texto
                        break
            jugadores = ""
            for celda in reversed(columnas):
                texto = celda.text.strip()
                if re.fullmatch(r"[\d,.]+[kKmM]?", texto):
                    jugadores = texto
                    break
            app_id = ""
            if enlace is not None:
                id_juego = re.search(r"/app/(\d+)/", enlace.get_attribute("href") or "")
                if id_juego:
                    app_id = id_juego.group(1)
            if nombre:
                resultados.append({"nombre": nombre, "jugadores": jugadores, "app_id": app_id})
    finally:
        driver.quit()
    return resultados

def obtener_tendencias():
    driver = nuevo_driver()
    nombres, valores, ids = [], [], []
    try:
        try:
            driver.get("https://steamdb.info/")
        except Exception:
            driver.quit()
            driver = nuevo_driver()
            driver.get("https://steamdb.info/")
        trending_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'trendingfollowers')]"))
        )
        table = trending_link.find_element(By.XPATH, "./ancestor::table")
        juegos = table.find_elements(By.CSS_SELECTOR, "tr.app[data-appid]")
        for i, juego in enumerate(juegos[:10], start=1):
            try:
                nombre = juego.find_element(By.CSS_SELECTOR, "td:nth-child(3) a").text
                jugadores = juego.find_elements(By.TAG_NAME, "td")[-1].text
                app_id = juego.get_attribute("data-appid")                            
                
                nombres.append(nombre)
                valores.append(parsear_jugadores(jugadores))
                ids.append(app_id)                  
            except Exception:
                pass
    finally:
        driver.quit()
    return nombres, valores, ids

def scrapear_valoraciones(anio, max_items=10):
    url = f"https://www.metacritic.com/browse/game/all/all/{anio}/metascore/"
    driver = nuevo_driver()
    resultados = []
    try:
        try:
            driver.get(url)
        except Exception:
            driver.quit()
            driver = nuevo_driver()
            driver.get(url)
        juegos = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="filter-results"]')
        for juego in juegos[:max_items]:
            try:
                nombre = juego.find_element(By.CSS_SELECTOR, "h3").text
                nota = juego.find_element(By.CSS_SELECTOR, ".c-siteReviewScore span").text
                resultados.append({"nombre": nombre, "nota": nota})
            except Exception:
                continue
    finally:
        driver.quit()
    return resultados

def obtener_conteo_generos(ids):
    driver = nuevo_driver()
    conteo = Counter()
    try:
        for id_juego in ids:
            driver.get(f"https://store.steampowered.com/app/{id_juego}/")
            saltar_edad(driver)
            try:
                tags = driver.find_elements(By.CSS_SELECTOR, ".app_tag")
                for tag in tags[:4]:
                    genero = tag.text.strip()
                    if genero:
                        conteo[genero] += 1
            except Exception:
                continue
    finally:
        driver.quit()
    return conteo

def scrapear_precios(max_items=12):
    driver = nuevo_driver()
    resultados = []
    try:
        try:
            driver.get("https://steamdb.info/sales/")
        except Exception:
            driver.quit()
            driver = nuevo_driver()
            driver.get("https://steamdb.info/sales/")
        WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.app")))
        juegos = driver.find_elements(By.CSS_SELECTOR, "tr.app")
        for juego in juegos[:max_items]:
            try:
                nombre = juego.find_element(By.CSS_SELECTOR, "td a.b").text.strip()
                columnas = juego.find_elements(By.TAG_NAME, "td")
                descuento_txt = columnas[3].text.strip() if len(columnas) > 3 else ""
                precio_txt = columnas[4].text.strip() if len(columnas) > 4 else ""
                precio_limpio = precio_txt.replace("€", "").replace("$", "").replace(",", ".").replace("\xa0", "").strip()
                precio_val = 0.0 if precio_limpio.lower() in ("free", "gratis", "") else float(precio_limpio)
                desc_limpio = descuento_txt.replace("-", "").replace("%", "").strip()
                desc_val = int(desc_limpio) if desc_limpio.isdigit() else 0
                app_id = juego.get_attribute("data-appid")                  
                
                if nombre:
                    resultados.append({
                        "nombre": nombre,
                        "precio_txt": precio_txt,
                        "descuento_txt": descuento_txt,
                        "precio_val": precio_val,
                        "descuento_val": desc_val,
                        "app_id": app_id                                 
                    })
            except Exception:
                continue
    finally:
        driver.quit()
    return resultados

def parsear_jugadores(texto):
    texto = texto.strip().replace(",", "").replace(".", "")
    multiplicador = 1
    if texto.lower().endswith("k"):
        multiplicador = 1_000
        texto = texto[:-1]
    elif texto.lower().endswith("m"):
        multiplicador = 1_000_000
        texto = texto[:-1]
    try:
        return int(float(texto) * multiplicador)
    except ValueError:
        return 0

@st.cache_data(ttl=3600, show_spinner=False)
def cargar_steam():
    populares = scrapear_populares(10)
    ids = [j["app_id"] for j in populares if j.get("app_id")]
    tendencia_nombres, tendencia_valores, tendencia_ids = obtener_tendencias()
    conteo_generos = obtener_conteo_generos(ids)
    precios = scrapear_precios(12)
    return {
        "populares": populares,
        "ids": ids,
        "tendencia_nombres": tendencia_nombres,
        "tendencia_valores": tendencia_valores,
        "tendencia_ids": tendencia_ids,
        "conteo_generos": conteo_generos,
        "precios": precios,
    }

@st.cache_data(ttl=3600, show_spinner=False)
def cargar_metacritic(anio):
    return scrapear_valoraciones(anio, 10)

PALETTE = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e",
           "#8b5cf6", "#06b6d4", "#84cc16", "#ec4899", "#fb923c"]

def plot_colors(dark):
    if dark:
        return {"bg": "#0d1117", "text": "#e2e8f0", "grid": "#1e293b",
                "sub": "#64748b", "spine": "#1e293b"}
    return {"bg": "#ffffff", "text": "#0f172a", "grid": "#e2e8f0",
            "sub": "#64748b", "spine": "#e2e8f0"}

def make_hbar(nombres, valores, titulo, etiqueta_x, dark):
    if not nombres or not valores:
        return None
    c = plot_colors(dark)
    fig, ax = plt.subplots(figsize=(9, max(4, len(nombres) * 0.52)))
    fig.patch.set_facecolor(c["bg"])
    ax.set_facecolor(c["bg"])
    colores = (PALETTE * 3)[:len(nombres)]
    bars = ax.barh(nombres[::-1], valores[::-1], color=colores[::-1],
                   height=0.55, edgecolor="none")
    max_v = max(valores) if valores else 1
    for bar, val in zip(bars, valores[::-1]):
        label = f"{val:,}" if val >= 1000 else str(val)
        ax.text(bar.get_width() + max_v * 0.012, bar.get_y() + bar.get_height() / 2,
                label, va="center", ha="left", color=c["sub"], fontsize=8.5)
    ax.set_title(titulo, color=c["text"], fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel(etiqueta_x, color=c["sub"], fontsize=9)
    ax.tick_params(axis="y", colors=c["text"], labelsize=8.5)
    ax.tick_params(axis="x", colors=c["sub"], labelsize=8)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(c["spine"])
    ax.spines["bottom"].set_color(c["spine"])
    ax.set_xlim(0, max_v * 1.20)
    fig.tight_layout(pad=1.2)
    return fig

def make_donut(conteo, dark):
    if not conteo:
        return None
    c = plot_colors(dark)
    mas = conteo.most_common(8)
    resto = sum(v for _, v in conteo.most_common()[8:])
    labels = [g for g, _ in mas]
    vals = [v for _, v in mas]
    if resto:
        labels.append("Otros")
        vals.append(resto)
        
    fig, ax = plt.subplots(figsize=(3.0, 2.4)) 
    fig.patch.set_facecolor(c["bg"])
    ax.set_facecolor(c["bg"])
    
    colores = (PALETTE * 3)[:len(labels)]
    wedges, _, autotexts = ax.pie(
        vals, labels=None, autopct="%1.0f%%", colors=colores,
        startangle=140, pctdistance=0.75,
        wedgeprops={"edgecolor": c["bg"], "linewidth": 2, "width": 0.65},
    )
    
    for at in autotexts:
        at.set_color("#ffffff")
        at.set_fontsize(7.5)
        at.set_fontweight("bold")
        
                                                                                    
    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(0.95, 0.5),
              frameon=False, labelcolor=c["text"], fontsize=8)
              
    ax.set_title("Géneros más comunes", color=c["text"], fontsize=11, fontweight="bold", pad=8)
    
    fig.tight_layout(pad=1.2)
    return fig

def make_precios(precios, dark):
    if not precios:
        return None
    c = plot_colors(dark)
    precios_ordenados = sorted(precios, key=lambda j: j["precio_val"], reverse=True)
    descuentos_ordenados = sorted(precios, key=lambda j: j["descuento_val"], reverse=True)

    nombres_p = [j["nombre"][:22] + ("…" if len(j["nombre"]) > 22 else "") for j in precios_ordenados]
    p_vals = [j["precio_val"] for j in precios_ordenados]

    nombres_d = [j["nombre"][:22] + ("…" if len(j["nombre"]) > 22 else "") for j in descuentos_ordenados]
    d_vals = [j["descuento_val"] for j in descuentos_ordenados]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, max(4, len(precios) * 0.45)))
    fig.patch.set_facecolor(c["bg"])
    for ax, nombres, vals, titulo, pal, fmt in [
        (ax1, nombres_p, p_vals, "Precio (EUR)", ["#6366f1", "#818cf8", "#a5b4fc"] * 5,
         lambda v: "FREE" if v == 0 else f"{v:.2f}€"),
        (ax2, nombres_d, d_vals, "Descuento (%)", ["#f59e0b", "#fbbf24", "#fcd34d"] * 5,
         lambda v: f"-{v}%"),
    ]:
        ax.set_facecolor(c["bg"])
        bars = ax.barh(nombres, vals, color=pal[:len(nombres)], height=0.55, edgecolor="none")
        mx = max(vals) if vals and max(vals) > 0 else 1
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width() + mx * 0.02, bar.get_y() + bar.get_height() / 2,
                    fmt(val), va="center", ha="left", color=c["sub"], fontsize=8)
        ax.invert_yaxis()
        ax.set_title(titulo, color=c["text"], fontsize=10, fontweight="bold", pad=8)
        ax.tick_params(axis="y", colors=c["text"], labelsize=7.5)
        ax.tick_params(axis="x", colors=c["sub"], labelsize=7.5)
        for sp in ["top", "right"]:
            ax.spines[sp].set_visible(False)
        ax.spines["left"].set_color(c["spine"])
        ax.spines["bottom"].set_color(c["spine"])
        ax.set_xlim(0, mx * 1.28)
    fig.suptitle("Ofertas Steam", color=c["text"], fontsize=12, fontweight="bold")
    fig.tight_layout(pad=1.5)
    return fig

def render_styled_table(rows, compact=False):
    if not rows:
        return
    cell_pad = "8px 10px" if compact else "10px 12px"
    cell_font = "0.90rem" if compact else "0.98rem"
    header_font = "0.72rem" if compact else "0.78rem"
    table_max_width = "560px" if compact else "100%"
    df = pd.DataFrame(rows)
    styler = (
        df.style
        .hide(axis="index")
        .set_table_styles([
            {"selector": "table", "props": [
                ("width", "auto"),
                ("max-width", table_max_width),
                ("margin", "0 auto"),
                ("border-collapse", "collapse"),
                ("border", f"1px solid {DF_BORDER}"),
                ("border-radius", "12px"),
                ("overflow", "hidden"),
                ("background", DF_BG),
            ]},
            {"selector": "thead th", "props": [
                ("background", DF_BG_HEADER),
                ("color", DF_TEXT_MUTED),
                ("font-size", header_font),
                ("font-weight", "700"),
                ("text-transform", "uppercase"),
                ("letter-spacing", "0.06em"),
                ("border", f"1px solid {DF_BORDER}"),
                ("padding", cell_pad),
                ("text-align", "left"),
            ]},
            {"selector": "tbody td", "props": [
                ("background", DF_BG),
                ("color", DF_TEXT),
                ("border", f"1px solid {DF_BORDER}"),
                ("padding", cell_pad),
                ("font-size", cell_font),
            ]},
            {"selector": "tbody tr:nth-child(even) td", "props": [
                ("background", DF_BG_ALT),
            ]},
        ], overwrite=True)
    )
    table_html = styler.to_html()
    st.markdown(
        f'<div class="table-shell" style="width:100%;display:flex;justify-content:center;">'
        f'<div style="display:inline-block;max-width:100%;overflow-x:auto;">{table_html}</div>'
        '</div>',
        unsafe_allow_html=True,
    )

if "dark" not in st.session_state:
    st.session_state.dark = True
if "anio" not in st.session_state:
    st.session_state.anio = "2025"

dark = st.session_state.dark

if dark:
    BG           = "#0d1117"
    SURFACE      = "#161b22"
    SURFACE2     = "#1c2333"
    BORDER       = "rgba(99,102,241,0.25)"
    TEXT         = "#e2e8f0"
    MUTED        = "#cacfd7"
    ACCENT       = "#6366f1"
    ACCENT2      = "#22d3ee"
    ACCENT3      = "#f59e0b"
    SIDEBAR_BG   = "#0a0e17"
    SIDEBAR_TEXT = "#e2e8f0"
    SIDEBAR_MUTED = "#94a3b8"
    SIDEBAR_LABEL = "#475569"
    SIDEBAR_SELECT_BG = "rgba(255,255,255,0.05)"
    SIDEBAR_SELECT_BORDER = "rgba(99,102,241,0.25)"
    HEADER_GRAD  = "linear-gradient(135deg,#0d1117 0%,#1a1040 100%)"
    CARD_HOVER   = "rgba(99,102,241,0.08)"
    TAG_BG       = "rgba(99,102,241,0.15)"
    TAG_TEXT     = "#818cf8"
    INPUT_BG     = "#161b22"
    SHADOW       = "0 4px 24px rgba(0,0,0,0.45)"
    BTN_BG       = "linear-gradient(135deg, #6366f1, #8b5cf6)"
    BTN_BG_HOVER = "linear-gradient(135deg, #4f46e5, #7c3aed)"
    BTN_TEXT     = "#ffffff"
    BTN_BORDER   = "rgba(99,102,241,0.30)"
    DF_BG        = "#141b2a"
    DF_BG_ALT    = "#1a2234"
    DF_BG_HEADER = "#0f172a"
    DF_TEXT      = "#e2e8f0"
    DF_TEXT_MUTED = "#94a3b8"
    DF_BORDER    = "rgba(99,102,241,0.24)"
else:
    BG           = "#f8fafc"
    SURFACE      = "#ffffff"
    SURFACE2     = "#f1f5f9"
    BORDER       = "rgba(99,102,241,0.18)"
    TEXT         = "#0f172a"
    MUTED        = "#64748b"
    ACCENT       = "#4f46e5"
    ACCENT2      = "#0891b2"
    ACCENT3      = "#d97706"
    SIDEBAR_BG   = "#eef2ff"
    SIDEBAR_TEXT = "#0f172a"
    SIDEBAR_MUTED = "#475569"
    SIDEBAR_LABEL = "#64748b"
    SIDEBAR_SELECT_BG = "#ffffff"
    SIDEBAR_SELECT_BORDER = "rgba(79,70,229,0.22)"
    HEADER_GRAD  = "linear-gradient(135deg,#eef2ff 0%,#faf5ff 100%)"
    CARD_HOVER   = "rgba(99,102,241,0.05)"
    TAG_BG       = "rgba(79,70,229,0.10)"
    TAG_TEXT     = "#4f46e5"
    INPUT_BG     = "#f8fafc"
    SHADOW       = "0 4px 24px rgba(15,23,42,0.10)"
    BTN_BG       = "linear-gradient(135deg, #4f46e5, #0891b2)"
    BTN_BG_HOVER = "linear-gradient(135deg, #4338ca, #0e7490)"
    BTN_TEXT     = "#ffffff"
    BTN_BORDER   = "rgba(79,70,229,0.30)"
    DF_BG        = "#ffffff"
    DF_BG_ALT    = "#f8fafc"
    DF_BG_HEADER = "#eef2ff"
    DF_TEXT      = "#0f172a"
    DF_TEXT_MUTED = "#64748b"
    DF_BORDER    = "rgba(79,70,229,0.20)"

                                                                               

                                                                               

                                                                              

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0&display=swap');

/* ── RESET & BASE ── */
html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif !important;
}}

.stApp {{
    background: {BG} !important;
    color: {TEXT};
}}

/* ── BOTONES DE NAVEGACIÓN (Píldoras Verdes) ── */
div[data-testid="stButton"] > button[kind="secondary"] {{
    background-color: transparent !important;
    border: 1px solid rgba(150, 150, 160, 0.3) !important;
    color: #94a3b8 !important;
    border-radius: 999px !important;
    transition: all 0.2s ease !important;
}}

div[data-testid="stButton"] > button[kind="secondary"]:hover {{
    border-color: #10b981 !important;
    background-color: rgba(16, 185, 129, 0.1) !important;
    color: #ffffff !important;
}}

div[data-testid="stButton"] > button[kind="primary"],
div[data-testid="stButton"] > button[data-testid="baseButton-primary"] {{
    background-color: #10b981 !important;
    border: 1px solid #10b981 !important;
    color: #ffffff !important;
    border-radius: 999px !important;
    font-weight: 800 !important;
    box-shadow: 0 4px 14px rgba(16, 185, 129, 0.4) !important;
}}

div[data-testid="stButton"] > button p {{
    color: inherit !important;
}}

/* 1. Ocultar la línea de colores superior, el footer y el estado */
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
footer {{
    display: none !important;
}}

/* 2. Hacer que la barra superior sea totalmente transparente */
header[data-testid="stHeader"],
.stAppHeader {{
    background: transparent !important;
    background-color: transparent !important;
    box-shadow: none !important;
}}

/* 3. Ocultar solo la parte derecha */
header[data-testid="stHeader"] > div:last-child,
.stAppHeader > div:last-child,
.stToolbar {{
    display: none !important;
}}

/* ── METRIC CARDS (Alineación para Imágenes) ── */
.metric-card {{
    background: {SURFACE};
    border: 1px solid {BORDER};
    border-radius: 14px;
    padding: 0.8rem 1rem;
    display: flex;
    align-items: center;
    justify-content: flex-start; /* Alineado a la izquierda para la foto */
    text-align: left;
    box-shadow: {SHADOW};
    overflow: hidden;
    width: 100%;
}}

.metric-body {{
    min-width: 0; 
    width: 100%;
}}

.metric-lbl {{
    font-size: 0.72rem; 
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: {MUTED};
    margin-bottom: 0.2rem;
    display: block;
}}

.metric-name {{
    font-family: 'DM Sans', sans-serif;
    font-size: 1.1rem; 
    font-weight: 700; 
    color: {TEXT};
    line-height: 1.2;
    display: block;
    white-space: nowrap; 
    overflow: hidden; 
    text-overflow: ellipsis; 
}}

/* ── DATA FRAME & TABLAS ── */
[data-testid="stVerticalBlockBorderWrapper"] > div {{
    background: {SURFACE} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 16px !important;
    box-shadow: {SHADOW} !important;
    padding: 1rem 1.2rem !important;
}}

/* ── SELECTBOX ── */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    background-color: {INPUT_BG} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
    color: {TEXT} !important;
}}
[data-testid="stSelectbox"] div[data-baseweb="select"] span,
[data-testid="stSelectbox"] div[data-baseweb="select"] div {{
    color: {TEXT} !important;
    background-color: transparent !important;
}}
[data-testid="stSelectbox"] svg {{
    fill: {MUTED} !important;
}}
[data-baseweb="popover"] ul {{
    background-color: {SURFACE2} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 10px !important;
}}
[data-baseweb="popover"] li {{
    background-color: {SURFACE2} !important;
    color: {TEXT} !important;
}}
[data-baseweb="popover"] li:hover {{
    background-color: {SURFACE} !important;
}}

/* ── LABEL DEL SELECTBOX Y TOGGLE ── */
[data-testid="stSelectbox"] label,
[data-testid="stToggle"] label {{
    color: {MUTED} !important;
    font-size: 0.78rem !important;
}}

/* ── BOTÓN ACTUALIZAR (ctrl_col) ── */
[data-testid="stButton"] > button[kind="secondary"] {{
    background-color: {SURFACE2} !important;
    border: 1px solid {BORDER} !important;
    color: {TEXT} !important;
    border-radius: 10px !important;
}}
[data-testid="stButton"] > button[kind="secondary"]:hover {{
    border-color: {ACCENT} !important;
    background-color: {INPUT_BG} !important;
    color: {TEXT} !important;
}}

</style>
""", unsafe_allow_html=True)

with st.spinner("Cargando datos desde SteamDB…"):
    d = cargar_steam()

with st.spinner(f"Cargando Metacritic {st.session_state.anio}…"):
    valoraciones = cargar_metacritic(st.session_state.anio)

populars        = d["populares"]
tend_nombres    = d["tendencia_nombres"]
tend_valores    = d["tendencia_valores"]
tend_ids        = d["tendencia_ids"]
conteo_generos  = d["conteo_generos"]
precios         = d["precios"]

pop_vals = [parsear_jugadores(j["jugadores"]) for j in populars]

pop_sorted   = sorted(zip(pop_vals, [j["nombre"] for j in populars]), reverse=True)
pop_vals_s   = [v for v, _ in pop_sorted]
pop_names_s  = [n for _, n in pop_sorted]

                                                                      
tend_sorted  = sorted(zip(tend_valores, tend_nombres, tend_ids), reverse=True)
tend_vals_s  = [v for v, _, _ in tend_sorted]
tend_names_s = [n for _, n, _ in tend_sorted]
tend_ids_s   = [i for _, _, i in tend_sorted]

fig_pop  = make_hbar(pop_names_s,  pop_vals_s,  "Juegos más jugados",   "Jugadores simultáneos", dark)
fig_tend = make_hbar(tend_names_s, tend_vals_s, "Trending en SteamDB",  "Seguidores / jugadores", dark)
fig_gen  = make_donut(conteo_generos, dark)
fig_off  = make_precios(precios, dark)

hero_col, ctrl_col = st.columns([7, 3], gap="small")

with hero_col:
    st.markdown(f"""
    <div class="hero">
        <div class="hero-left">
            <h1 class="hero-title">Game Trends Dashboard</h1>
            <p class="hero-sub">Datos automáticos desde SteamDB y Metacritic · Año {st.session_state.anio}</p>
            <div class="hero-bar"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with ctrl_col:
    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)
    anios = ["2026", "2025", "2024", "2023", "2022", "2021", "2020", "2019", "2018", "2017"]
    st.selectbox("Año Metacritic", options=anios, key="anio", label_visibility="visible")

    c1, c2 = st.columns([1, 1], gap="small")
    with c1:
        nuevo_dark = st.toggle("🌙 Oscuro", value=st.session_state.dark)
        if nuevo_dark != st.session_state.dark:
            st.session_state.dark = nuevo_dark
            st.rerun()
    with c2:
        if st.button("↻ Actualizar", use_container_width=True):
            cargar_steam.clear()
            cargar_metacritic.clear()
            st.rerun()

top_pop_nombre  = pop_names_s[0] if pop_names_s else "—"
top_tend_nombre = tend_names_s[0] if tend_names_s else "—"
top_oferta = precios[0]["nombre"] if precios else "—"

            
top_pop_id = populars[0]["app_id"] if populars and populars[0].get("app_id") else None
top_tend_id = tend_ids_s[0] if tend_ids_s else None
top_oferta_id = precios[0]["app_id"] if precios and precios[0].get("app_id") else None

                     
FALLBACK_SVG = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='60' height='38' "
    "viewBox='0 0 60 38'%3E%3Crect width='60' height='38' rx='4' fill='%231e293b'/%3E"
    "%3Crect x='8' y='10' width='28' height='18' rx='2' fill='none' stroke='%236366f1' stroke-width='1.5'/%3E"
    "%3Cline x1='14' y1='19' x2='20' y2='19' stroke='%236366f1' stroke-width='1.5' stroke-linecap='round'/%3E"
    "%3Cline x1='17' y1='16' x2='17' y2='22' stroke='%236366f1' stroke-width='1.5' stroke-linecap='round'/%3E"
    "%3Ccircle cx='25' cy='17' r='1.2' fill='%2322d3ee'/%3E"
    "%3Ccircle cx='28' cy='20' r='1.2' fill='%2322d3ee'/%3E"
    "%3Crect x='40' y='12' width='12' height='8' rx='1.5' fill='%236366f1' opacity='0.7'/%3E"
    "%3Crect x='38' y='22' width='16' height='2' rx='1' fill='%236366f1' opacity='0.4'/%3E"
    "%3Crect x='40' y='26' width='12' height='2' rx='1' fill='%236366f1' opacity='0.3'/%3E"
    "%3C/svg%3E"
)

@st.cache_data(ttl=3600, show_spinner=False)
def verificar_img(url):
    """Verifica desde Python si la URL carga; si no, devuelve el SVG fallback."""
    if not url:
        return FALLBACK_SVG
    try:
        r = requests.head(url, timeout=3, allow_redirects=True)
        if r.status_code == 200:
            return url
    except Exception:
        pass
    return FALLBACK_SVG

img_pop  = verificar_img(f"https://cdn.akamai.steamstatic.com/steam/apps/{top_pop_id}/header.jpg" if top_pop_id else None)
img_tend = verificar_img(f"https://cdn.akamai.steamstatic.com/steam/apps/{top_tend_id}/header.jpg" if top_tend_id else None)
img_off  = verificar_img(f"https://cdn.akamai.steamstatic.com/steam/apps/{top_oferta_id}/header.jpg" if top_oferta_id else None)
img_gen  = "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?w=150&h=100&fit=crop&q=80" if conteo_generos else None

metric_data = [
    ("POPULARES",  top_pop_nombre, img_pop),
    ("TRENDING",   top_tend_nombre, img_tend),
    ("GÉNEROS",    conteo_generos.most_common(1)[0][0] if conteo_generos else "—", img_gen),
    ("OFERTA TOP", top_oferta, img_off),
]

        
cols_m = st.columns(4, gap="small")

for col, (lbl, nombre, img_url) in zip(cols_m, metric_data):
    with col:
        html_imagen = ""
        if img_url:
            html_imagen = (
                f'<div style="min-width:60px;height:38px;margin-right:12px;border-radius:6px;'
                f'overflow:hidden;border:1px solid rgba(255,255,255,0.1);flex-shrink:0;'
                f'background:linear-gradient(135deg,#1e293b,#0f172a);">'
                f'<img src="{img_url}" style="width:100%;height:100%;object-fit:cover;display:block;">'
                f'</div>'
            )

                                                               
        html_card = f"""<div class="metric-card" style="justify-content: flex-start; text-align: left; padding: 0.8rem 1rem;">
{html_imagen}
<div class="metric-body" style="min-width: 0; width: 100%;">
<span class="metric-lbl">{lbl}</span>
<span class="metric-name" title="{nombre}">{nombre}</span>
</div>
</div>"""
        
        st.markdown(html_card, unsafe_allow_html=True)

if "vista" not in st.session_state:
    st.session_state.vista = "pop"

VISTAS = [
    ("pop",  "Populares"),
    ("tend", "Tendencias"),
    ("gen",  "Géneros"),
    ("off",  "Ofertas"),
    ("val",  "Valoraciones"),
]

st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

st.markdown(f"""
<style>
.nav-bar {{
    display: flex;
    gap: 0.5rem;
    margin-bottom: 1rem;
    flex-wrap: wrap;
}}
            

.nav-btn {{
... (Y TODO LO DEMÁS HASTA AQUÍ ABAJO) ...
.nav-btn-all.active {{
    background: {ACCENT3};
    color: #ffffff;
    box-shadow: 0 4px 16px rgba(245,158,11,0.3);
}}
</style>
""", unsafe_allow_html=True)

                                                                              
st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

nav_cols = st.columns(6, gap="small")

for col, (key, label) in zip(nav_cols[:5], VISTAS):
    with col:
                                                                   
        btn_type = "primary" if st.session_state.vista == key else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_type):
            st.session_state.vista = key
            st.rerun()

with nav_cols[5]:
    btn_type = "primary" if st.session_state.vista == "all" else "secondary"
    if st.button("Ver todos", key="nav_all", use_container_width=True, type=btn_type):
        st.session_state.vista = "all"
        st.rerun()

st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

def render_populares():
    with st.container(border=True):
        st.markdown("""<div class="section-title">
            <span class="stitle-accent"></span> Top populares
        </div>""", unsafe_allow_html=True)
        
        chart_col, table_col = st.columns([RATIO_CHART, RATIO_TABLE], gap="large")
        with chart_col:
            if fig_pop is not None:
                st.pyplot(fig_pop, clear_figure=True)
                plt.close(fig_pop)
        with table_col:
            if populars:
                render_styled_table(
                    [{"#": i+1, "Juego": j["nombre"], "Jugadores": j["jugadores"], "App ID": j["app_id"]}
                     for i, j in enumerate(populars[:10])],
                    compact=True,
                )

def render_tendencias():
    with st.container(border=True):
        st.markdown("""<div class="section-title">
            <span class="stitle-accent"></span> Tendencias SteamDB
        </div>""", unsafe_allow_html=True)
        
        chart_col, table_col = st.columns([RATIO_CHART, RATIO_TABLE], gap="large")
        with chart_col:
            if fig_tend is not None:
                st.pyplot(fig_tend, clear_figure=True)
                plt.close(fig_tend)
        with table_col:
            if tend_nombres:
                render_styled_table(
                    [{"#": i+1, "Juego": n, "Seguidores": f"{v:,}"}
                     for i, (n, v) in enumerate(zip(tend_nombres[:10], tend_valores[:10]))],
                    compact=True,
                )

def render_generos():
    with st.container(border=True):
        st.markdown("""<div class="section-title">
            <span class="stitle-accent"></span> Géneros más comunes
        </div>""", unsafe_allow_html=True)
        
        chart_col, table_col = st.columns([5, 5], gap="large")
        with chart_col:
            if fig_gen is not None:
                st.pyplot(fig_gen, use_container_width=False, clear_figure=True)
                plt.close(fig_gen)
        with table_col:
            if conteo_generos:
                render_styled_table(
                    [{"Género": g, "Apariciones": c}
                     for g, c in conteo_generos.most_common(10)],
                    compact=True,
                )

def render_ofertas():
    with st.container(border=True):
        st.markdown("""<div class="section-title">
            <span class="stitle-accent"></span> Mejores ofertas
        </div>""", unsafe_allow_html=True)
        
        chart_col, table_col = st.columns([RATIO_CHART, RATIO_TABLE], gap="large")
        with chart_col:
            if fig_off is not None:
                st.pyplot(fig_off, clear_figure=True)
                plt.close(fig_off)
        with table_col:
            if precios:
                render_styled_table(
                    [{"Juego": j["nombre"], "Precio": j["precio_txt"], "Descuento": j["descuento_txt"]}
                     for j in precios[:12]],
                    compact=True,
                )

def make_metascore(valoraciones, dark):
    if not valoraciones:
        return None
    c = plot_colors(dark)
    nombres = [v["nombre"][:28] + ("…" if len(v["nombre"]) > 28 else "") for v in valoraciones]
    notas = []
    for v in valoraciones:
        try:
            notas.append(int(v["nota"]))
        except (ValueError, TypeError):
            notas.append(0)

                               
    def score_color(n):
        if n >= 90: return "#10b981"
        if n >= 75: return "#6366f1"
        if n >= 60: return "#f59e0b"
        return "#f43f5e"

    colores = [score_color(n) for n in notas]

    fig, ax = plt.subplots(figsize=(9, max(4, len(nombres) * 0.52)))
    fig.patch.set_facecolor(c["bg"])
    ax.set_facecolor(c["bg"])

    bars = ax.barh(nombres[::-1], notas[::-1], color=colores[::-1], height=0.55, edgecolor="none")
    for bar, val in zip(bars, notas[::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", ha="left", color=c["sub"], fontsize=9, fontweight="bold")

    ax.set_title(f"Metascore · {st.session_state.anio}", color=c["text"], fontsize=12, fontweight="bold", pad=10)
    ax.set_xlabel("Metascore", color=c["sub"], fontsize=9)
    ax.tick_params(axis="y", colors=c["text"], labelsize=8.5)
    ax.tick_params(axis="x", colors=c["sub"], labelsize=8)
    ax.set_xlim(0, 105)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color(c["spine"])
    ax.spines["bottom"].set_color(c["spine"])
    fig.tight_layout(pad=1.2)
    return fig

def render_valoraciones():
    
    with st.container(border=True):
        st.markdown(f"""<div class="section-title">
            <span class="stitle-accent"></span> Valoraciones Metacritic · {st.session_state.anio}
        </div>""", unsafe_allow_html=True)
        if valoraciones:
            fig_val = make_metascore(valoraciones, dark)
            chart_col, table_col = st.columns([RATIO_CHART, RATIO_TABLE], gap="large")
            with chart_col:
                if fig_val is not None:
                    st.pyplot(fig_val, clear_figure=True)
                    plt.close(fig_val)
            with table_col:
                render_styled_table(
                    [{"#": i+1, "Juego": v["nombre"], "Metascore": v["nota"]}
                     for i, v in enumerate(valoraciones)],
                    compact=True,
                )
        else:
            st.info("Sin datos de valoraciones para este año.")

def render_todas_las_vistas():
    render_populares()
    st.markdown("<div style='height:0.45rem'></div>", unsafe_allow_html=True)
    render_tendencias()
    st.markdown("<div style='height:0.45rem'></div>", unsafe_allow_html=True)
    render_generos()
    st.markdown("<div style='height:0.45rem'></div>", unsafe_allow_html=True)
    render_ofertas()
    st.markdown("<div style='height:0.45rem'></div>", unsafe_allow_html=True)
    render_valoraciones()

rutas = {
    "pop": render_populares,
    "tend": render_tendencias,
    "gen": render_generos,
    "off": render_ofertas,
    "val": render_valoraciones,
    "all": render_todas_las_vistas
}

                                                          
                                                                                          
vista_actual = st.session_state.get("vista", "pop")

                                               
funcion_a_ejecutar = rutas.get(vista_actual, render_populares)

                       
funcion_a_ejecutar()