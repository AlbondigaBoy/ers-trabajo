import tkinter as tk
from tkinter import scrolledtext, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By


def obtener_populares():
    output.delete(1.0, tk.END)

    driver = webdriver.Chrome()
    driver.get("https://steamdb.info/")

    juegos = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    output.insert(tk.END, "Juegos más populares:\n\n")

    for i, juego in enumerate(juegos[:10], start=1):
        columnas = juego.find_elements(By.TAG_NAME, "td")

        if len(columnas) >= 3:
            nombre = columnas[1].text
            jugadores = columnas[2].text
            output.insert(tk.END, f"{i}. {nombre} - {jugadores}\n")

    driver.quit()


def obtener_tendencias():
    output.delete(1.0, tk.END)

    driver = webdriver.Chrome()
    driver.get("https://steamdb.info/graph/")

    juegos = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    output.insert(tk.END, "Tendencias:\n\n")

    for i, juego in enumerate(juegos[:10], start=1):
        columnas = juego.find_elements(By.TAG_NAME, "td")

        if len(columnas) >= 4:
            nombre = columnas[1].text
            crecimiento = columnas[3].text

            output.insert(tk.END, f"{i}. {nombre} - Crecimiento: {crecimiento}\n")

    driver.quit()


def obtener_valoraciones():
    output.delete(1.0, tk.END)

    año = combo_año.get()
    url = f"https://www.metacritic.com/browse/game/all/all/{año}/metascore/"

    driver = webdriver.Chrome()
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

    driver = webdriver.Chrome()
    driver.get("https://steamdb.info/")

    juegos = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    generos = {}

    for juego in juegos[:20]:
        columnas = juego.find_elements(By.TAG_NAME, "td")

        if len(columnas) >= 6:
            genero = columnas[5].text

            if genero in generos:
                generos[genero] += 1
            else:
                generos[genero] = 1

    output.insert(tk.END, "Géneros más jugados:\n\n")

    for genero, cantidad in generos.items():
        output.insert(tk.END, f"{genero}: {cantidad}\n")

    driver.quit()


def obtener_precios():
    output.delete(1.0, tk.END)

    driver = webdriver.Chrome()
    driver.get("https://steamdb.info/sales/")

    juegos = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    output.insert(tk.END, "Mejores ofertas:\n\n")

    for i, juego in enumerate(juegos[:10], start=1):
        columnas = juego.find_elements(By.TAG_NAME, "td")

        if len(columnas) >= 5:
            nombre = columnas[1].text
            precio = columnas[4].text

            output.insert(tk.END, f"{i}. {nombre} - {precio}\n")

    driver.quit()


# Interfaz
ventana = tk.Tk()
ventana.title("Game Trends Analyzer")
ventana.geometry("800x500")

frame_botones = tk.Frame(ventana)
frame_botones.pack(pady=10)

tk.Button(frame_botones, text="Populares", command=obtener_populares).grid(row=0, column=0, padx=5)
tk.Button(frame_botones, text="Valoraciones", command=obtener_valoraciones).grid(row=0, column=1, padx=5)
tk.Button(frame_botones, text="Géneros", command=obtener_generos).grid(row=0, column=2, padx=5)
tk.Button(frame_botones, text="Tendencias", command=obtener_tendencias).grid(row=0, column=3, padx=5)
tk.Button(frame_botones, text="Precios", command=obtener_precios).grid(row=0, column=4, padx=5)
frame_año = tk.Frame(ventana)
frame_año.pack()

tk.Label(frame_año, text="Año:").pack(side=tk.LEFT)

combo_año = ttk.Combobox(
    frame_año,
    values=[
        "2026","2025","2024","2023",
        "2022","2021","2020","2019",
        "2018","2017","2016"
    ],
    width=10
)

combo_año.current(0)
combo_año.pack(side=tk.LEFT)

output = scrolledtext.ScrolledText(ventana, wrap=tk.WORD, width=90, height=25)
output.pack(padx=10, pady=10)

ventana.mainloop()