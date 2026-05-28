import flet as ft
from bs4 import BeautifulSoup
import uuid
import json
import tkinter as tk
from tkinter import filedialog

def main(page: ft.Page):
    page.title = "Tonika Converter"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 30
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    # Usamos page.data para guardar temporalmente la información extraída
    page.data = {"extraidos": None}

    texto_estado = ft.Text("Esperando archivo .htm / .html...", color=ft.Colors.GREY_400)
    texto_detalles = ft.Text("", size=14, color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)

    # --- LÓGICA DE EXTRACCIÓN ---
    def extraer_datos(ruta_archivo):
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        # Buscamos el Título y el Artista
        titulo_tag = soup.find("h1", class_="t1")
        titulo = titulo_tag.text.strip() if titulo_tag else "Sin título"

        artista_tag = soup.find("h2", class_="t3")
        artista = artista_tag.text.strip() if artista_tag else "Desconocido"

        # Buscamos la Tonalidad
        tono_tag = soup.find("span", id="cifra_tom")
        tonalidad = ""
        if tono_tag and tono_tag.find("a"):
            tonalidad = tono_tag.find("a").text.strip()

        # Extraemos la letra y reemplazamos las etiquetas <b> por corchetes []
        pre_tag = soup.find("pre")
        letra_y_acordes = ""
        if pre_tag:
            for b_tag in pre_tag.find_all("b"):
                acorde = b_tag.text.strip()
                b_tag.replace_with(f"[{acorde}]")
            letra_y_acordes = pre_tag.get_text()

        return {
            "titulo": titulo,
            "artista": artista,
            "bpm": 0,
            "genero": "",
            "tonalidad": tonalidad,
            "letra_y_acordes": letra_y_acordes,
            "id": str(uuid.uuid4())
        }

    # --- EXPLORADORES NATIVOS CON TKINTER ---
    def abrir_archivo_web(e):
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        
        ruta_html = filedialog.askopenfilename(
            title="Seleccionar archivo web de Cifra Club",
            filetypes=[("Archivos Web", "*.htm *.html")]
        )
        root.destroy()
        
        if ruta_html:
            try:
                datos = extraer_datos(ruta_html)
                page.data["extraidos"] = datos
                texto_estado.value = "¡Archivo analizado con éxito!"
                texto_estado.color = ft.Colors.GREEN_400
                texto_detalles.value = f"♫ {datos['titulo']} - {datos['artista']}"
                btn_guardar.disabled = False
            except Exception as ex:
                texto_estado.value = "Error al leer el archivo web."
                texto_estado.color = ft.Colors.ERROR
                texto_detalles.value = str(ex)
                btn_guardar.disabled = True
            page.update()

    def guardar_archivo_tnk(e):
        datos = page.data.get("extraidos")
        if not datos:
            return

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)

        nombre_sugerido = f"{datos['titulo'].replace(' ', '_')}_{datos['artista'].replace(' ', '_')}.tnk"

        ruta_guardado = filedialog.asksaveasfilename(
            title="Exportar canción Tonika",
            initialfile=nombre_sugerido,
            defaultextension=".tnk",
            filetypes=[("Archivos Tonika", "*.tnk")]
        )
        root.destroy()

        if ruta_guardado:
            try:
                if not ruta_guardado.endswith('.tnk'):
                    ruta_guardado += '.tnk'
                
                with open(ruta_guardado, "w", encoding="utf-8") as f:
                    json.dump(datos, f, indent=4, ensure_ascii=False)

                texto_estado.value = "¡Archivo .tnk exportado exitosamente!"
                texto_estado.color = ft.Colors.GREEN_400
                texto_detalles.value = "Ya puedes importarlo a tu biblioteca en Tonika."
                btn_guardar.disabled = True # Bloqueamos el botón para evitar doble guardado
            except Exception as ex:
                texto_estado.value = "Error al guardar el archivo."
                texto_estado.color = ft.Colors.ERROR
                texto_detalles.value = str(ex)
            page.update()

    # --- INTERFAZ GRÁFICA ---
    btn_abrir = ft.FilledButton(
        "1. Cargar archivo web (.htm)",
        icon=ft.Icons.UPLOAD_FILE,
        height=50,
        on_click=abrir_archivo_web
    )

    btn_guardar = ft.FilledButton(
        "2. Exportar para Tonika (.tnk)",
        icon=ft.Icons.SAVE,
        height=50,
        disabled=True, 
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600),
        on_click=guardar_archivo_tnk
    )

    page.add(
        ft.Icon(ft.Icons.AUTO_FIX_HIGH, size=80, color=ft.Colors.PRIMARY),
        ft.Text("Tonika Converter", size=28, weight=ft.FontWeight.BOLD),
        ft.Text("Extrae letra y acordes de páginas descargadas y los empaqueta para Tonika.", text_align=ft.TextAlign.CENTER, color=ft.Colors.GREY_400),
        ft.Divider(height=30, color=ft.Colors.TRANSPARENT),
        btn_abrir,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        texto_estado,
        texto_detalles,
        ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
        btn_guardar
    )

if __name__ == "__main__":
    # Actualizado al método recomendado de Flet 0.85.2+
    ft.run(main)