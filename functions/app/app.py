from flask import Flask, render_template, request, send_file
import datetime
import os
import io
from pathlib import Path
from docxtpl import DocxTemplate
 
# Le decimos a Flask dónde encontrar la carpeta 'templates', que ahora está
# incluida dentro del paquete de la función gracias a 'included_files'.
template_dir = Path(__file__).parent / 'templates'
app = Flask(__name__, template_folder=template_dir)

def generar_informe_docx(context):
    """
    Genera un informe médico en formato .docx a partir de una plantilla
    y un diccionario de contexto. Devuelve el documento en memoria.
    """
    try:
        # La plantilla se incluye en el despliegue de la función,
        # por lo que podemos acceder a ella con una ruta relativa.
        plantilla_path = Path(__file__).parent / "plantilla_informe.docx"
        doc = DocxTemplate(plantilla_path)

        # Añadir datos dinámicos
        hoy = datetime.date.today()
        context['fecha_actual'] = hoy.strftime("%d-%m-%Y")
        context['fecha_examen'] = hoy.strftime("%d-%m-%Y")

        # Calcular y añadir la edad del paciente
        try:
            fecnac_str = context.get('fecha_nacimiento', '')
            if fecnac_str:
                fecha_nacimiento = datetime.datetime.strptime(fecnac_str, "%Y-%m-%d").date()
                edad = hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))
                context['edad'] = edad
                context['fecha_nacimiento'] = fecha_nacimiento.strftime("%d-%m-%Y")
            else:
                context['edad'] = "N/A"
        except (ValueError, AttributeError):
            context['edad'] = "N/A"

        doc.render(context)
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        return file_stream
    except Exception as e:
        print(f"Error al generar el documento: {e}")
        return None
 
@app.route('/')
def index():
    """Muestra el formulario web."""
    return render_template('index.html')

@app.route('/generar', methods=['POST'])
def generar():
    """
    Recibe los datos del formulario, genera el informe
    y lo devuelve como un archivo para descargar.
    """
    # Recolectar datos del formulario
    nombre = request.form.get('nombre', '')
    run = request.form.get('run', '')
    fecnac = request.form.get('fecnac', '') # HTML date input da formato YYYY-MM-DD
    tipo_examen = request.form.get('tipo_examen', 'TC')
    region_examen = request.form.get('region_examen', 'Cerebral')

    # Construir el diccionario de contexto
    context = {
        "centro_medico": "Hospital Clinico Viña del Mar",
        "nombre": nombre,
        "run": run,
        "fecha_nacimiento": fecnac,
        "TIPO_EXAMEN": f"{tipo_examen} {region_examen}",
        "antecedentes": request.form.get('antecedentes', ''),
        "hallazgos": request.form.get('hallazgos', ''),
        "conclusion": request.form.get('conclusion', ''),
        "medico_tratante": "Dr. Alejandro Venegas D."
    }

    # Generar el documento en memoria
    file_stream = generar_informe_docx(context)

    if file_stream:
        # Crear un nombre de archivo único
        fecha_hoy = datetime.date.today().strftime("%d-%m-%Y")
        nombre_archivo = f"Informe_{run or 'SIN_RUN'}_{fecha_hoy}.docx"

        # Enviar el archivo al usuario
        return send_file(
            file_stream,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
    
    return "Error al generar el documento.", 500

if __name__ == '__main__':
    app.run(debug=True)