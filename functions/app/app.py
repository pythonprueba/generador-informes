from flask import Flask, render_template, request, send_file
from generar_informe import generar_informe_docx
import datetime

app = Flask(__name__)

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