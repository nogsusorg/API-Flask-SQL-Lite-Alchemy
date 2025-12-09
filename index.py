from flask import Flask, request, render_template, redirect, url_for, session
import secrets
# Importar la función de inicialización de la base de datos de SQLAlchemy
from models.db_model import create_db_and_tables, check_user, is_db_model_created
from routes.product_routes import product_api

# --- Configuración Inicial de la Aplicación ---
app = Flask(__name__, template_folder='templates')

# Generar una clave secreta fuerte para gestionar sesiones
app.secret_key = secrets.token_hex(24)

# Registrar el Blueprint de las rutas de la API
app.register_blueprint(product_api)


# --- Inicialización de la Base de Datos ---
# Antes de que se sirva la primera solicitud, asegurar que las tablas existen
@app.before_request
def initialize_database():
    """Llama a la función para crear las tablas de la DB usando SQLAlchemy."""
    try:
        if not is_db_model_created(["users", "products"]):
            create_db_and_tables()
            print("Base de datos y tablas inicializadas con éxito con SQLAlchemy.")
    except Exception as e:
        print(f"ERROR: Falló la inicialización de la base de datos: {e}")


# --- RUTAS PÚBLICAS (Login y Logout) ---

@app.route('/')
def index():
    """Ruta principal: dirige al login si no está logeado, o al dashboard si lo está."""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Maneja la solicitud de Login."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Validar las credenciales usando la función del modelo (SQLAlchemy)
        user_id = check_user(username, password)

        if user_id is not None:
            # Autenticación exitosa: establecer la sesión
            session['user_id'] = user_id
            print(f"Usuario {username} logeado con ID: {user_id}")
            return redirect(url_for('dashboard'))
        else:
            # Autenticación fallida
            return render_template('login.html', message='Credenciales incorrectas. Intente de nuevo.')

    # Si es GET, simplemente muestra el formulario de login
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Cierra la sesión del usuario."""
    session.pop('user_id', None)
    return redirect(url_for('index'))


# --- RUTA PROTEGIDA (Dashboard) ---

@app.route('/dashboard')
def dashboard():
    """Página de bienvenida y documentación de endpoints (Requiere sesión)."""
    if 'user_id' not in session:
        # Si no hay sesión, redirigir al login
        return redirect(url_for('login'))

    # Si hay sesión, mostrar el dashboard
    return render_template('dashboard.html', user_id=session['user_id'])


# --- Ejecución del Servidor ---
if __name__ == '__main__':
    # Usar un puerto y host estándar
    app.run(debug=True, host='127.0.0.1', port=5000)