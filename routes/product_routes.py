from flask import Blueprint, request, jsonify, session
from functools import wraps
# Importar funciones CRUD actualizadas de SQLAlchemy
from models.db_model import get_products, get_product_by_id, add_product, delete_product

# Crear un Blueprint para las rutas de la API
product_api = Blueprint('product_api', __name__, url_prefix='/api')


# --- Decorador de Autenticación Simple ---
def require_auth(f):
    """Decorador simple para verificar si el usuario está logeado."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica la sesión de Flask
        if 'user_id' not in session:
            # Devuelve una respuesta JSON si no está autenticado
            return jsonify({'message': 'Acceso no autorizado. Por favor, inicie sesión.'}), 401
        return f(*args, **kwargs)

    return decorated_function


# --- ENDPOINTS (Rutas de la A a la D) ---

# A. Método: GET -> Listado de todos los productos con paginación
@product_api.route('/products', methods=['GET'])
@require_auth
def list_products():
    """
    Endpoint GET para listar productos con paginación.
    Ejemplo: /api/products?page=1&per_page=5
    """
    try:
        # Obtener parámetros de paginación de la URL
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 5, type=int)

        # Llama a la función de DB (SQLAlchemy)
        products, total_products = get_products(page, per_page)

        if not products and page > 1:
            return jsonify({'message': 'No hay productos en esta página.'}), 404

        total_pages = (total_products + per_page - 1) // per_page

        response = {
            'products': products,
            'pagination': {
                'total_items': total_products,
                'total_pages': total_pages,
                'current_page': page,
                'per_page': per_page
            }
        }
        return jsonify(response)

    except Exception as e:
        print(f"Error al listar productos: {e}")
        return jsonify({'message': 'Error interno del servidor al listar productos.'}), 500


# B. Método: GET -> Listado de un producto específico
@product_api.route('/products/<int:product_id>', methods=['GET'])
@require_auth
def get_single_product(product_id):
    """Endpoint GET para obtener un producto por su ID."""
    # Llama a la función de DB (SQLAlchemy)
    product = get_product_by_id(product_id)

    if product:
        return jsonify(product)

    return jsonify({'message': f'Producto con ID {product_id} no encontrado.'}), 404


# C. Método: POST -> Ingreso de un producto
@product_api.route('/products', methods=['POST'])
@require_auth
def add_new_product():
    """Endpoint POST para agregar un nuevo producto."""
    data = request.get_json()

    # Validación simple de datos de entrada
    if not data or 'name' not in data or 'price' not in data:
        return jsonify({'message': 'Faltan campos obligatorios (name y price).'}), 400

    try:
        name = data['name']
        description = data.get('description', '')
        # Asegurarse de que el precio sea un número
        price = float(data['price'])

        # Llama a la función de DB (SQLAlchemy)
        new_id = add_product(name, description, price)

        return jsonify({
            'message': 'Producto creado exitosamente.',
            'id': new_id,
            'name': name
        }), 201

    except ValueError:
        return jsonify({'message': 'El precio debe ser un número válido.'}), 400
    except Exception as e:
        print(f"Error al agregar producto: {e}")
        return jsonify({'message': 'Error interno del servidor al crear producto.'}), 500


# D. Método: DELETE -> Eliminar un producto específico
@product_api.route('/products/<int:product_id>', methods=['DELETE'])
@require_auth
def delete_single_product(product_id):
    """Endpoint DELETE para eliminar un producto por su ID."""
    # Llama a la función de DB (SQLAlchemy)
    deleted_count = delete_product(product_id)

    if deleted_count > 0:
        return jsonify({'message': f'Producto con ID {product_id} eliminado exitosamente.'}), 200

    return jsonify({'message': f'Producto con ID {product_id} no encontrado para eliminar.'}), 404