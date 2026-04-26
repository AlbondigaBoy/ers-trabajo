import re
import time
import tkinter as tk
from tkinter import scrolledtext, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.ticker as mticker

options = webdriver.FirefoxOptions()
options.add_argument("-headless")


def saltar_edad(driver):
    try:
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.ID, "ageYear"))
        )
        Select(driver.find_element(By.ID, "ageYear")).select_by_value("2000")
        driver.find_element(By.ID, "view_product_page_btn").click()
        time.sleep(5)
    except:
        pass


def obtener_populares():
    output.delete(1.0, tk.END)

    driver = webdriver.Firefox(options=options)
    driver.get("https://steamdb.info/")

    juegos = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    output.insert(tk.END, "Juegos más populares:\n\n")

    ids = []

    for i, juego in enumerate(juegos[:10], start=1):
        columnas = juego.find_elements(By.TAG_NAME, "td")

        if len(columnas) >= 3:
            nombre = columnas[1].text
            jugadores = columnas[2].text

            link = juego.find_element(By.TAG_NAME, "a").get_attribute("href")
            id_juego = re.search(r'/app/(\d+)/', link)

            if id_juego:
                ids.append(id_juego.group(1))

            output.insert(tk.END, f"{i}. {nombre} - {jugadores}\n")

    driver.quit()
    return ids


def obtener_tendencias():
    output.delete(1.0, tk.END)

    driver = webdriver.Firefox(options=options)
    driver.get("https://steamdb.info/")

    trending_link = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, "//a[contains(@href,'trendingfollowers')]")
        )
    )

    table = trending_link.find_element(By.XPATH, "./ancestor::table")
    juegos = table.find_elements(By.CSS_SELECTOR, "tr.app[data-appid]")

    output.insert(tk.END, "Trending Games (SteamDB)\n\n")

    for i, juego in enumerate(juegos[:10], start=1):
        try:
            nombre = juego.find_element(
                By.CSS_SELECTOR,
                "td:nth-child(3) a"
            ).text

            jugadores = juego.find_elements(By.TAG_NAME, "td")[-1].text

            output.insert(
                tk.END,
                f"{i}. {nombre} - {jugadores}\n"
            )

        except Exception as e:
            output.insert(tk.END, f"Error fila {i}: {e}\n")

    driver.quit()


def obtener_valoraciones():
    output.delete(1.0, tk.END)

    año = combo_año.get()
    url = f"https://www.metacritic.com/browse/game/all/all/{año}/metascore/"

    driver = webdriver.Firefox(options=options)
    driver.get(url)

    juegos = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="filter-results"]')

    output.insert(tk.END, f"Mejores juegos de {año}\n\n")

    for i, juego in enumerate(juegos[:10], start=1):
        try:
            nombre = juego.find_element(By.CSS_SELECTOR, "h3").text
            nota = juego.find_element(By.CSS_SELECTOR, ".c-siteReviewScore span").text

            output.insert(
                tk.END,
                f"{nombre}\n"
                f"Nota: {nota}\n"
            )

        except:
            continue

    driver.quit()


def obtener_generos():
    output.delete(1.0, tk.END)
    ids = obtener_populares()

    driver = webdriver.Firefox(options=options)

    generos = set()

    for id_juego in ids:
        url = f"https://store.steampowered.com/app/{id_juego}/"
        driver.get(url)

        saltar_edad(driver)

        try:
            tags = driver.find_elements(By.CSS_SELECTOR, ".app_tag")

            for tag in tags[:4]:
                genero = tag.text.strip()

                if genero:
                    generos.add(genero)

        except:
            continue

    driver.quit()

    output.insert(tk.END, "Géneros más jugados:\n\n")

    for genero in sorted(generos):
        output.insert(tk.END, f"- {genero}\n")


def obtener_precios():
    output.delete(1.0, tk.END)

    driver = webdriver.Firefox(options=options)
    driver.get("https://steamdb.info/sales/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.app"))
    )

    juegos = driver.find_elements(By.CSS_SELECTOR, "tr.app")

    output.insert(tk.END, "Mejores ofertas (SteamDB)\n\n")

    for i, juego in enumerate(juegos[:10], start=1):
        try:
            nombre = juego.find_element(By.CSS_SELECTOR, "td a.b").text

            columnas = juego.find_elements(By.TAG_NAME, "td")
            precio = columnas[4].text

            output.insert(
                tk.END,
                f"{i}. {nombre} - {precio}\n"
            )

        except Exception as e:
            continue

    driver.quit()


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


def mostrar_grafico_barras(nombres, valores, titulo, etiqueta_y="Jugadores actuales"):
    if not nombres or not valores:
        output.insert(tk.END, "\n⚠️  No hay datos suficientes para generar el gráfico.\n")
        return

    ventana_grafico = tk.Toplevel(ventana)
    ventana_grafico.title(titulo)
    ventana_grafico.geometry("900x520")
    ventana_grafico.configure(bg="#1b2838")

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("#1b2838")
    ax.set_facecolor("#1b2838")

    colores = [
        "#66c0f4", "#4fa3d1", "#3a8ebf", "#2d79ac", "#226699",
        "#1a5580", "#144466", "#0e334d", "#092233", "#04111a"
    ]
    colores = (colores * 2)[:len(nombres)]

    nombres_inv = nombres[::-1]
    valores_inv = valores[::-1]
    colores_inv = colores[::-1]

    barras = ax.barh(nombres_inv, valores_inv, color=colores_inv,
                     height=0.6, edgecolor="none")

    max_val = max(valores_inv) if valores_inv else 1
    for barra, val in zip(barras, valores_inv):
        label = f"{val:,}" if val >= 1000 else str(val)
        ax.text(
            barra.get_width() + max_val * 0.01,
            barra.get_y() + barra.get_height() / 2,
            label,
            va="center", ha="left",
            color="#c6d4df", fontsize=9, fontweight="bold"
        )

    ax.set_title(titulo, color="#c6d4df", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel(etiqueta_y, color="#8f98a0", fontsize=10)
    ax.tick_params(axis="y", colors="#c6d4df", labelsize=9)
    ax.tick_params(axis="x", colors="#8f98a0", labelsize=8)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{int(x):,}"
    ))
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#2a475e")
    ax.spines["bottom"].set_color("#2a475e")
    ax.set_xlim(0, max_val * 1.18)

    fig.tight_layout(pad=1.5)

    canvas = FigureCanvasTkAgg(fig, master=ventana_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    tk.Button(
        ventana_grafico,
        text="Cerrar",
        command=ventana_grafico.destroy,
        bg="#2a475e", fg="#c6d4df",
        relief="flat", padx=10, pady=4
    ).pack(pady=(0, 8))


def grafico_tendencias():
    obtener_tendencias()

    texto = output.get(1.0, tk.END)
    lineas = texto.strip().splitlines()

    nombres, valores = [], []
    patron = re.compile(r'^\d+\.\s+(.+?)\s+-\s+([\d,\.]+[kKmM]?)$')

    for linea in lineas:
        m = patron.match(linea.strip())
        if m:
            nombre = m.group(1).strip()
            jugadores_str = m.group(2).strip()
            val = parsear_jugadores(jugadores_str)
            nombres.append(nombre)
            valores.append(val)

    mostrar_grafico_barras(
        nombres, valores,
        titulo="Top Juegos Más Jugados — Trending",
        etiqueta_y="Seguidores / jugadores"
    )


def grafico_generos():
    from collections import Counter

    output.delete(1.0, tk.END)
    ids = obtener_populares()

    driver = webdriver.Firefox(options=options)
    conteo = Counter()

    for id_juego in ids:
        url = f"https://store.steampowered.com/app/{id_juego}/"
        driver.get(url)
        saltar_edad(driver)

        try:
            tags = driver.find_elements(By.CSS_SELECTOR, ".app_tag")
            for tag in tags[:4]:
                genero = tag.text.strip()
                if genero:
                    conteo[genero] += 1
        except:
            continue

    driver.quit()

    output.insert(tk.END, "Géneros más jugados:\n\n")
    for genero in sorted(conteo.keys()):
        output.insert(tk.END, f"- {genero} ({conteo[genero]})\n")

    if not conteo:
        output.insert(tk.END, "\n⚠️  No hay datos de géneros para graficar.\n")
        return

    top_n = 8
    mas_comunes = conteo.most_common(top_n)
    resto = sum(v for _, v in conteo.most_common()[top_n:])

    etiquetas = [g for g, _ in mas_comunes]
    valores   = [v for _, v in mas_comunes]

    if resto > 0:
        etiquetas.append("Otros")
        valores.append(resto)

    ventana_grafico = tk.Toplevel(ventana)
    ventana_grafico.title("🥧 Distribución de Géneros")
    ventana_grafico.geometry("820x540")
    ventana_grafico.configure(bg="#1b2838")

    fig, ax = plt.subplots(figsize=(8, 5))
    fig.patch.set_facecolor("#1b2838")
    ax.set_facecolor("#1b2838")

    paleta = [
        "#66c0f4", "#4fa3d1", "#3a8ebf", "#f4a460", "#e07b39",
        "#c0392b", "#8e44ad", "#27ae60", "#95a5a6"
    ]
    colores = (paleta * 3)[:len(etiquetas)]

    explode = [0.05 if v == max(valores) else 0 for v in valores]

    wedges, texts, autotexts = ax.pie(
        valores,
        labels=None,
        autopct="%1.1f%%",
        colors=colores,
        explode=explode,
        startangle=140,
        wedgeprops={"edgecolor": "#1b2838", "linewidth": 1.5},
        pctdistance=0.78
    )

    for at in autotexts:
        at.set_color("#1b2838")
        at.set_fontsize(8.5)
        at.set_fontweight("bold")

    ax.legend(
        wedges, etiquetas,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        frameon=False,
        labelcolor="#c6d4df",
        fontsize=9
    )

    ax.set_title(
        "Distribución de Géneros\n(top juegos populares)",
        color="#c6d4df", fontsize=12, fontweight="bold", pad=14
    )

    fig.tight_layout(pad=1.5)

    canvas = FigureCanvasTkAgg(fig, master=ventana_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    tk.Button(
        ventana_grafico,
        text="Cerrar",
        command=ventana_grafico.destroy,
        bg="#2a475e", fg="#c6d4df",
        relief="flat", padx=10, pady=4
    ).pack(pady=(0, 8))


def grafico_precios():
    output.delete(1.0, tk.END)

    driver = webdriver.Firefox(options=options)
    driver.get("https://steamdb.info/sales/")

    WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tr.app"))
    )

    juegos = driver.find_elements(By.CSS_SELECTOR, "tr.app")

    output.insert(tk.END, "Mejores ofertas (SteamDB) — Gráfico de precios\n\n")

    nombres, precios, descuentos = [], [], []

    for juego in juegos[:12]:
        try:
            nombre = juego.find_element(By.CSS_SELECTOR, "td a.b").text.strip()
            columnas = juego.find_elements(By.TAG_NAME, "td")

            descuento_txt = columnas[3].text.strip() if len(columnas) > 3 else ""
            precio_txt    = columnas[4].text.strip() if len(columnas) > 4 else ""

            precio_limpio = (
                precio_txt
                .replace("€", "").replace("$", "")
                .replace(",", ".").replace("\xa0", "").strip()
            )
            if precio_limpio.lower() in ("free", "gratis", ""):
                precio_val = 0.0
            else:
                precio_val = float(precio_limpio)

            desc_limpio = descuento_txt.replace("-", "").replace("%", "").strip()
            desc_val = int(desc_limpio) if desc_limpio.isdigit() else 0

            if nombre:
                label = nombre[:26] + ("…" if len(nombre) > 26 else "")
                nombres.append(label)
                precios.append(precio_val)
                descuentos.append(desc_val)
                output.insert(tk.END, f"  {nombre} — {precio_txt}  ({descuento_txt})\n")

        except Exception:
            continue

    driver.quit()

    if not nombres:
        output.insert(tk.END, "\n⚠️  No se pudieron obtener datos de precios.\n")
        return

    datos = sorted(zip(precios, descuentos, nombres), key=lambda x: x[1])
    precios_ord    = [d[0] for d in datos]
    descuentos_ord = [d[1] for d in datos]
    nombres_ord    = [d[2] for d in datos]

    ventana_grafico = tk.Toplevel(ventana)
    ventana_grafico.title("💰 Análisis de Precios — Ofertas Steam")
    ventana_grafico.geometry("1060x580")
    ventana_grafico.configure(bg="#1b2838")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5.5))
    fig.patch.set_facecolor("#1b2838")

    paleta_azul = [
        "#66c0f4", "#4fa3d1", "#3a8ebf", "#2d79ac", "#226699",
        "#1a5580", "#144466", "#0e334d", "#092233", "#04111a",
        "#66c0f4", "#4fa3d1"
    ]
    paleta_naranja = [
        "#f4a460", "#e07b39", "#c0392b", "#f39c12", "#d35400",
        "#8e44ad", "#27ae60", "#16a085", "#2980b9", "#e74c3c",
        "#f4a460", "#e07b39"
    ]

    colores_p = (paleta_azul    * 2)[:len(nombres_ord)]
    colores_d = (paleta_naranja * 2)[:len(nombres_ord)]

    ax1.set_facecolor("#1b2838")
    barras1 = ax1.barh(nombres_ord, precios_ord, color=colores_p,
                        height=0.6, edgecolor="none")

    max_p = max(precios_ord) if max(precios_ord) > 0 else 1
    for barra, val in zip(barras1, precios_ord):
        lbl = "Free" if val == 0 else f"{val:.2f} €"
        ax1.text(
            barra.get_width() + max_p * 0.02,
            barra.get_y() + barra.get_height() / 2,
            lbl, va="center", ha="left",
            color="#c6d4df", fontsize=8.5, fontweight="bold"
        )

    ax1.set_title("Precio con descuento (€)", color="#c6d4df",
                   fontsize=11, fontweight="bold", pad=10)
    ax1.set_xlabel("Precio (€)", color="#8f98a0", fontsize=9)
    ax1.tick_params(axis="y", colors="#c6d4df", labelsize=8)
    ax1.tick_params(axis="x", colors="#8f98a0", labelsize=8)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_color("#2a475e")
    ax1.spines["bottom"].set_color("#2a475e")
    ax1.set_xlim(0, max_p * 1.25)

    ax2.set_facecolor("#1b2838")
    barras2 = ax2.barh(nombres_ord, descuentos_ord, color=colores_d,
                        height=0.6, edgecolor="none")

    max_d = max(descuentos_ord) if max(descuentos_ord) > 0 else 1
    for barra, val in zip(barras2, descuentos_ord):
        ax2.text(
            barra.get_width() + max_d * 0.02,
            barra.get_y() + barra.get_height() / 2,
            f"-{val}%", va="center", ha="left",
            color="#c6d4df", fontsize=8.5, fontweight="bold"
        )

    ax2.set_title("Descuento aplicado (%)", color="#c6d4df",
                   fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("Descuento (%)", color="#8f98a0", fontsize=9)
    ax2.tick_params(axis="y", colors="#c6d4df", labelsize=8)
    ax2.tick_params(axis="x", colors="#8f98a0", labelsize=8)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    ax2.spines["left"].set_color("#2a475e")
    ax2.spines["bottom"].set_color("#2a475e")
    ax2.set_xlim(0, max_d * 1.25)
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}%"))

    fig.suptitle("💰 Ofertas Steam — Precio vs Descuento",
                  color="#c6d4df", fontsize=13, fontweight="bold", y=1.01)
    fig.tight_layout(pad=2.0)

    canvas = FigureCanvasTkAgg(fig, master=ventana_grafico)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=8, pady=8)

    tk.Button(
        ventana_grafico,
        text="Cerrar",
        command=ventana_grafico.destroy,
        bg="#2a475e", fg="#c6d4df",
        relief="flat", padx=10, pady=4
    ).pack(pady=(0, 8))


ventana = tk.Tk()
ventana.title("Game Trends Analyzer")
ventana.geometry("1000x600")

main = tk.Frame(ventana)
main.pack(fill="both", expand=True)

frame_botones = tk.Frame(main)
frame_botones.grid(row=0, column=0, rowspan=2, sticky="ns", padx=10, pady=10)

tk.Button(frame_botones, text="Populares",  command=obtener_populares).pack(fill="x", pady=3)
tk.Button(frame_botones, text="Géneros",    command=obtener_generos).pack(fill="x", pady=3)
tk.Button(frame_botones, text="Tendencias", command=obtener_tendencias).pack(fill="x", pady=3)
tk.Button(frame_botones, text="Precios",    command=obtener_precios).pack(fill="x", pady=3)

ttk.Separator(frame_botones, orient="horizontal").pack(fill="x", pady=8)
tk.Label(frame_botones, text="── Analíticas ──", fg="gray", font=("", 8)).pack()

tk.Button(
    frame_botones,
    text="📊 Gráfico Tendencias",
    command=grafico_tendencias
).pack(fill="x", pady=3)

tk.Button(
    frame_botones,
    text="📊 Gráfico Géneros",
    command=grafico_generos
).pack(fill="x", pady=3)

tk.Button(
    frame_botones,
    text="💰 Gráfico Precios",
    command=grafico_precios
).pack(fill="x", pady=3)


frame_top = tk.Frame(main)
frame_top.grid(row=0, column=1, sticky="w", padx=10, pady=10)

btn_valoraciones = tk.Button(
    frame_top,
    text="Valoraciones",
    command=obtener_valoraciones
)
btn_valoraciones.grid(row=0, column=0, padx=5)

tk.Label(frame_top, text="Año:").grid(row=0, column=1, padx=5)

combo_año = ttk.Combobox(
    frame_top,
    values=[
        "2026","2025","2024","2023",
        "2022","2021","2020","2019",
        "2018","2017","2016"
    ],
    width=10
)
combo_año.current(0)
combo_año.grid(row=0, column=2, padx=5)


output = scrolledtext.ScrolledText(main, wrap=tk.WORD, width=90, height=30)
output.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

main.grid_columnconfigure(1, weight=1)
main.grid_rowconfigure(1, weight=1)

ventana.mainloop()