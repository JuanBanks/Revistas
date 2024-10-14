from flask import Flask, render_template
import subprocess
import os
import signal

app = Flask(__name__)

# Guardar los procesos en ejecución
procesos = []

# Ruta para la página principal
@app.route('/')
def home():
    return render_template('index.html')

# Ruta para ejecutar la secuencia de Publindex
@app.route('/run/publindex')
def run_publindex():
    try:
        # Ejecutar el primer script: prueba4.py
        proceso1 = subprocess.Popen(['python', 'prueba4.py'])
        procesos.append(proceso1)

        proceso2 = subprocess.Popen(['python', 'historicoAnos.py'])
        procesos.append(proceso2)

        proceso3 = subprocess.Popen(['python', 'Homologadas.py'])
        procesos.append(proceso3)

        proceso4 = subprocess.Popen(['python', 'RevistasP.py'])
        procesos.append(proceso4)

        return "Los scripts de Publindex se están ejecutando."
    except Exception as e:
        return f"Error al ejecutar la secuencia: {e}"

# Ruta para ejecutar la secuencia de SJR
@app.route('/run/sjr')
def run_sjr():
    try:
        proceso1 = subprocess.Popen(['python', 'Scimago.py'])
        procesos.append(proceso1)

        proceso2 = subprocess.Popen(['python', 'OrganizarScimagoOpen.py'])
        procesos.append(proceso2)

        return "Los scripts de SJR se están ejecutando."
    except Exception as e:
        return f"Error al ejecutar la secuencia: {e}"

# Ruta para ejecutar el script Revistas.py
@app.route('/run/revistas')
def run_revistas():
    try:
        proceso1 = subprocess.Popen(['python', 'Revistas.py'])
        procesos.append(proceso1)

        return "Revistas.py se está ejecutando."
    except Exception as e:
        return f"Error al ejecutar Revistas.py: {e}"

# Ruta para cancelar las descargas (terminar todos los procesos)
@app.route('/cancel')
def cancel_processes():
    try:
        for proceso in procesos:
            if proceso.poll() is None:  # Si el proceso está en ejecución
                os.kill(proceso.pid, signal.SIGTERM)  # Termina el proceso
                print(f"Proceso {proceso.pid} terminado.")
        
        # Limpiar la lista de procesos una vez que todos han sido detenidos
        procesos.clear()

        return "Todos los procesos han sido cancelados."
    except Exception as e:
        return f"Error al cancelar los procesos: {e}"

# Función para detener los procesos en ejecución si se cierra la aplicación
@app.route('/shutdown')
def shutdown():
    return cancel_processes()

# Iniciar la aplicación Flask
if __name__ == "__main__":
    app.run(debug=True, port=5000)
