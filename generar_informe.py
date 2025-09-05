from docxtpl import DocxTemplate
import datetime
from pathlib import Path
import io

# La función resource_path no es necesaria en el entorno web,
# los archivos se manejarán directamente con rutas relativas.

def generar_informe_docx(context):
    """
    Genera un informe médico en formato .docx a partir de una plantilla
    y un diccionario de contexto. Devuelve el documento en memoria.
    """
    try:
        # Construir rutas de archivo de forma robusta
        # Asumimos que la plantilla está en el mismo directorio que este script
        plantilla_path = Path(__file__).parent / "plantilla_informe.docx"
        doc = DocxTemplate(plantilla_path)

        # Añadir datos dinámicos que no están en el JSON
        hoy = datetime.date.today()
        context['fecha_actual'] = hoy.strftime("%d-%m-%Y")
        context['fecha_examen'] = hoy.strftime("%d-%m-%Y") # Asumiendo que el examen es hoy

        # --- INICIO: Calcular y añadir la edad del paciente ---
        try:
            fecnac_str = context.get('fecha_nacimiento', '')
            if fecnac_str:
                # Asumimos formato AAAA-MM-DD que es el estándar de input type="date" en HTML
                fecha_nacimiento = datetime.datetime.strptime(fecnac_str, "%Y-%m-%d").date()
                edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                context['edad'] = edad
                # También formateamos la fecha de nacimiento para el documento
                context['fecha_nacimiento'] = fecha_nacimiento.strftime("%d-%m-%Y")
            else:
                context['edad'] = "N/A"
        except (ValueError, AttributeError): # Ya no necesitamos capturar KeyError
            context['edad'] = "N/A" # Poner un valor por defecto si la fecha es inválida
        # --- FIN: Calcular y añadir la edad del paciente ---

        # Rellenar la plantilla con los datos
        doc.render(context)

        # Guardar el documento en un objeto en memoria en lugar de un archivo físico
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0) # Rebobinar el stream para que pueda ser leído
        return file_stream

    except Exception as e:
        print(f"Error al generar el documento: {e}")
        return None