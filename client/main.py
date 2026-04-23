import re
import time
import tkinter as tk
from tkinter import scrolledtext, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.FirefoxOptions()
options.add_argument("-headless")

def saltar_edad(driver):
    try:
        # esperar si aparece el selector de edad
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

            # extraer link
            link = juego.find_element(By.TAG_NAME, "a").get_attribute("href")

            # extraer id
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

            # coger solo los 4 primeros
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


# Interfaz
ventana = tk.Tk()
ventana.title("Game Trends Analyzer")
ventana.geometry("1000x600")

main = tk.Frame(ventana)
main.pack(fill="both", expand=True)

frame_botones = tk.Frame(main)
frame_botones.grid(row=0, column=0, rowspan=2, sticky="ns", padx=10, pady=10)

tk.Button(frame_botones, text="Populares", command=obtener_populares).pack(fill="x", pady=3)
tk.Button(frame_botones, text="Géneros", command=obtener_generos).pack(fill="x", pady=3)
tk.Button(frame_botones, text="Tendencias", command=obtener_tendencias).pack(fill="x", pady=3)
tk.Button(frame_botones, text="Precios", command=obtener_precios).pack(fill="x", pady=3)

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