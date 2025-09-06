from flask import Flask, render_template, request, send_file
import datetime
import io
import os
from pathlib import Path
from docxtpl import DocxTemplate
import traceback

# --- CONFIGURACIÓN ROBUSTA PARA NETLIFY ---
# La carpeta 'templates' y la plantilla .docx se incluyen en el paquete de la función.
# Usamos pathlib para construir rutas relativas al script actual, lo que siempre funciona.
base_path = Path(__file__).parent
template_dir = base_path / 'templates'
app = Flask(__name__, template_folder=template_dir)

def generar_informe_docx(context):
    """Genera un informe .docx en memoria a partir de un contexto."""
    try:
        plantilla_path = base_path / "plantilla_informe.docx"
        doc = DocxTemplate(plantilla_path)

        hoy = datetime.date.today()
        context['fecha_actual'] = hoy.strftime("%d-%m-%Y")
        context['fecha_examen'] = hoy.strftime("%d-%m-%Y")

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
        # Imprime el error en los logs de la función de Netlify para depuración
        print(f"ERROR al generar DOCX: {traceback.format_exc()}")
        return None

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    """Maneja todas las peticiones GET para mostrar el formulario o depurar errores."""
    if path == "generar":
        return "Endpoint 'generar' solo acepta POST.", 405
    try:
        return render_template('index.html')
    except Exception:
        # Si render_template falla (ej. TemplateNotFound), devolvemos un error detallado.
        error_html = f"<h1>Error al Cargar la Página</h1><p>No se pudo encontrar o renderizar 'index.html'. Revisa los logs de la función de Netlify.</p><pre>{traceback.format_exc()}</pre>"
        return error_html, 500

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