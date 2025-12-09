import sqlite3
import os
import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, text
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

# --- Configuración de la Base de Datos ---
DB_FOLDER = 'data'
DB_FILE = os.path.join(DB_FOLDER, 'products.db')
DATABASE_URL = f"sqlite:///{DB_FILE}"

# Crear la carpeta 'data' si no existe
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER)

# Crear el motor de la base de datos
engine = create_engine(DATABASE_URL)

# Base para los modelos declarativos
Base = declarative_base()

# Crear una sesión gestionada
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# --- Definición de Modelos (Tablas) ---

class User(Base):
    """Modelo para la tabla de usuarios."""
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # En producción, debería ser hasheado


class Product(Base):
    """Modelo para la tabla de productos."""
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)


# --- Context Manager para la Sesión ---

@contextmanager
def get_db():
    """Proporciona y cierra una sesión de base de datos."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Funciones de Inicialización ---

def create_db_and_tables():
    """Crea la base de datos y todas las tablas definidas."""
    Base.metadata.create_all(bind=engine)

    # Insertar usuario de prueba y productos de ejemplo si no existen
    with get_db() as db:
        # 1. Insertar usuario de prueba
        if db.query(User).filter(User.username == 'admin').first() is None:
            # En un entorno real, la contraseña debe ser hasheada
            admin_user = User(username='admin', password='password123')
            db.add(admin_user)
            print("Usuario 'admin' insertado. Credenciales: admin/password123")

        # 2. Insertar productos de ejemplo
        if db.query(Product).count() == 0:
            products_data = [
                Product(name='Laptop Ultraligera', description='13 pulgadas, 16GB RAM, SSD 512GB', price=1200.00),
                Product(name='Monitor 4K', description='27 pulgadas, 60Hz, HDR', price=450.50),
                Product(name='Teclado Mecánico', description='Switches Blue, Retroiluminación RGB', price=85.99),
                Product(name='Mouse Gaming', description='Inalámbrico, 16000 DPI', price=55.00),
                Product(name='Webcam Full HD', description='1080p a 30fps', price=49.99),
                Product(name='Disco Duro Externo', description='2TB, USB 3.0', price=75.00),
                Product(name='Auriculares Inalámbricos', description='Cancelación de ruido', price=150.00),
            ]
            db.add_all(products_data)
            print("Productos de ejemplo insertados.")

        db.commit()


# --- Funciones de Validación de Usuario ---

def check_user(username, password):
    """Verifica si el usuario y la clave son correctos."""
    with get_db() as db:
        user = db.query(User).filter(User.username == username, User.password == password).first()
        if user:
            return user.id
        return None


# --- Funciones CRUD de Productos ---

def get_products(page: int = 1, per_page: int = 5):
    """Obtiene una lista de productos con paginación."""
    with get_db() as db:
        offset = (page - 1) * per_page

        # Consulta paginada de productos
        products = db.query(Product).offset(offset).limit(per_page).all()

        # Conteo total para la paginación
        total_products = db.query(Product).count()

        # Convertir objetos SQLAlchemy a diccionarios
        products_list = [{
            'id': p.id,
            'name': p.name,
            'description': p.description,
            'price': p.price
        } for p in products]

        return products_list, total_products


def get_product_by_id(product_id: int):
    """Obtiene un producto específico por su ID."""
    with get_db() as db:
        product = db.query(Product).filter(Product.id == product_id).first()

        if product:
            return {
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price
            }
        return None


def add_product(name: str, description: str, price: float):
    """Inserta un nuevo producto y devuelve su ID."""
    with get_db() as db:
        new_product = Product(name=name, description=description, price=price)
        db.add(new_product)
        db.commit()
        db.refresh(new_product)  # Refresca el objeto para obtener el ID generado
        return new_product.id


def delete_product(product_id: int):
    """Elimina un producto por su ID y devuelve el número de filas eliminadas."""
    with get_db() as db:
        product_to_delete = db.query(Product).filter(Product.id == product_id).first()

        if product_to_delete:
            db.delete(product_to_delete)
            db.commit()
            return 1  # Devuelve 1 si se eliminó
        return 0  # Devuelve 0 si no se encontró

def is_db_model_created(tables=[]):
    """Verifica si la base de datos es valida."""
    tb_exists = True
    inspector = sqlalchemy.inspect(engine)

    for tbl in tables:
        tb_exists &= inspector.has_table(tbl)

    return tb_exists