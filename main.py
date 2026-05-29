import flet as ft
from bs4 import BeautifulSoup, NavigableString
import uuid
import json
import os # <-- Añadido necesario para manejar las carpetas en Android

def main(page: ft.Page):
    page.title = "Tonika Converter"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 30
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    
    page.data = {"extraidos": None}

    texto_estado = ft.Text("Esperando archivo .htm / .html...", color=ft.Colors.GREY_400)
    texto_detalles = ft.Text("Versión Unificada Multiplataforma", size=14, color=ft.Colors.PRIMARY, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)

    # --- LÓGICA DE EXTRACCIÓN AVANZADA ---
    def extraer_datos(ruta_archivo):
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        titulo_tag = soup.find("h1", class_="t1")
        titulo = titulo_tag.text.strip() if titulo_tag else "Sin título"

        artista_tag = soup.find("h2", class_="t3")
        artista = artista_tag.text.strip() if artista_tag else "Desconocido"

        tono_tag = soup.find("span", id="cifra_tom")
        tonalidad = ""
        if tono_tag and tono_tag.find("a"):
            tonalidad = tono_tag.find("a").text.strip()

        pre_tag = soup.find("pre")
        letra_y_acordes = ""
        
        if pre_tag:
            def get_marked_text(element):
                if isinstance(element, NavigableString):
                    return str(element)
                text = ""
                is_chord = getattr(element, 'name', '') == 'b'
                if is_chord:
                    text += '\x01'
                for child in element:
                    text += get_marked_text(child)
                if is_chord:
                    text += '\x02'
                return text

            raw_marked_text = get_marked_text(pre_tag)
            lines = raw_marked_text.split('\n')

            def parse_chord_line(line):
                chords = []
                visual_pos = 0
                i = 0
                while i < len(line):
                    if line[i] == '\x01':
                        i += 1
                        chord_name = ""
                        while i < len(line) and line[i] != '\x02':
                            chord_name += line[i]
                            i += 1
                        chords.append({"name": chord_name, "pos": visual_pos})
                    elif line[i] == '\x02':
                        i += 1
                    else:
                        visual_pos += 1
                        i += 1
                return chords

            merged_lines = []
            i = 0
            
            while i < len(lines):
                line = lines[i]
                
                if line.strip('\r\n\t ') == "":
                    i += 1
                    continue
                
                if '\x01' in line:
                    chords = parse_chord_line(line)
                    
                    next_i = i + 1
                    while next_i < len(lines) and lines[next_i].strip('\r\n\t ') == "":
                        next_i += 1
                        
                    if next_i < len(lines) and '\x01' not in lines[next_i]:
                        lyric_line = lines[next_i]
                        max_pos = max([c['pos'] for c in chords]) if chords else 0
                        
                        if len(lyric_line) < max_pos:
                            lyric_line = lyric_line.ljust(max_pos)

                        for c in reversed(chords):
                            pos = c['pos']
                            lyric_line = lyric_line[:pos] + f"[{c['name']}]" + lyric_line[pos:]

                        merged_lines.append(lyric_line)
                        i = next_i + 1 
                    else:
                        clean_line = line.replace('\x01', '[').replace('\x02', ']')
                        merged_lines.append(clean_line)
                        i = next_i
                else:
                    merged_lines.append(line)
                    i += 1

            final_lines = []
            for line in merged_lines:
                line_spaced = line
                while '  ' in line_spaced:
                    line_spaced = line_spaced.replace('  ', ' \xA0')
                final_lines.append(line_spaced.rstrip())

            letra_y_acordes = '\n'.join(final_lines)

        return {
            "titulo": titulo,
            "artista": artista,
            "bpm": 0,
            "genero": "",
            "tonalidad": tonalidad,
            "letra_y_acordes": letra_y_acordes,
            "id": str(uuid.uuid4())
        }

    # --- RUTINAS PARA EL ÉXITO ---
    def procesar_exito(ruta_html):
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

    def procesar_guardado(datos, ruta_guardado):
        try:
            if not ruta_guardado.endswith('.tnk'):
                ruta_guardado += '.tnk'
            with open(ruta_guardado, "w", encoding="utf-8") as f:
                json.dump(datos, f, indent=4, ensure_ascii=False)

            texto_estado.value = "¡Archivo .tnk exportado exitosamente!"
            texto_estado.color = ft.Colors.GREEN_400
            texto_detalles.value = "Listo para Tonika."
            btn_guardar.disabled = True 
        except Exception as ex:
            texto_estado.value = "Error al guardar el archivo."
            texto_estado.color = ft.Colors.ERROR
            texto_detalles.value = str(ex)
        page.update()

    # --- INSTANCIACIÓN DE SERVICIOS UNIVERSALES ---
    picker_abrir = ft.FilePicker()
    picker_guardar = ft.FilePicker()
    
    if hasattr(page, "services"):
        page.services.append(picker_abrir)
        page.services.append(picker_guardar)

    # --- ENRUTADORES PRINCIPALES ASÍNCRONOS ---
    async def btn_abrir_click(e):
        archivos = await picker_abrir.pick_files(allowed_extensions=["htm", "html"])
        if archivos and len(archivos) > 0:
            procesar_exito(archivos[0].path)

    async def btn_guardar_click(e):
        nombre = f"{page.data.get('extraidos', {}).get('titulo', 'cancion').replace(' ', '_')}.tnk" if page.data.get('extraidos') else "cancion.tnk"
        
        # Estrategia dinámica dependiendo de la plataforma
        es_movil = page.platform in [ft.PagePlatform.ANDROID, ft.PagePlatform.IOS]
        
        if es_movil:
            # En Android/iOS usamos el selector de carpetas
            ruta_carpeta = await picker_guardar.get_directory_path(dialog_title="Selecciona dónde guardar la canción")
            if ruta_carpeta:
                ruta_completa = os.path.join(ruta_carpeta, nombre)
                datos = page.data.get("extraidos")
                if datos:
                    procesar_guardado(datos, ruta_completa)
        else:
            # En PC usamos la ventana clásica de "Guardar como..."
            ruta = await picker_guardar.save_file(file_name=nombre, allowed_extensions=["tnk"])
            if ruta:
                datos = page.data.get("extraidos")
                if datos:
                    procesar_guardado(datos, ruta)

    # --- INTERFAZ GRÁFICA ---
    btn_abrir = ft.FilledButton(
        "1. Cargar archivo web (.htm)",
        icon=ft.Icons.UPLOAD_FILE,
        height=50,
        on_click=btn_abrir_click
    )

    btn_guardar = ft.FilledButton(
        "2. Exportar para Tonika (.tnk)",
        icon=ft.Icons.SAVE,
        height=50,
        disabled=True, 
        style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600),
        on_click=btn_guardar_click
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
    ft.run(main)