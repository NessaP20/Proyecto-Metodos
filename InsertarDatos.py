import random
from faker import Faker
import psycopg2
from datetime import datetime
from psycopg2.extras import Json
from werkzeug.security import generate_password_hash

fake = Faker('en_US')

# Definir conexión a la base de datos
DATABASE = {
    'dbname': 'Supermercado',
    'user': 'postgres',
    'password': '1928',
    'host': 'localhost',
    'port': '5432'
}

def conectar_bd():
    try:
        conexion = psycopg2.connect(**DATABASE)
        return conexion
    except Exception as e:
        print(f"Error al conectar con la base de datos: {e}")
        return None

# Obtener todos los productos disponibles de la base de datos
def obtener_productos_disponibles():
    productos_disponibles = []
    try:
        conexion = conectar_bd()
        if conexion:
            cursor = conexion.cursor()
            cursor.execute("SELECT id_producto, nombre, precio FROM productos")
            productos_disponibles = cursor.fetchall()  # Recuperar todos los productos
            cursor.close()
            conexion.close()
    except Exception as e:
        print(f"Error al obtener productos: {e}")
    return productos_disponibles


# Generar fechas en formato 'YYYY-MM-DD'
def generar_fecha_expiracion():
    # Fecha aleatoria en el futuro (por ejemplo, entre 1 y 5 años a partir de hoy)
    años_adelante = random.randint(1, 5)
    fecha_expiracion = datetime.now().replace(year=datetime.now().year + años_adelante)
    return fecha_expiracion.strftime('%Y-%m-%d')

# Insertar datos en la base de datos
def insertar_datos(tabla, columnas, valores):
    conexion = conectar_bd()
    if conexion:
        try:
            cursor = conexion.cursor()
            query = f"INSERT INTO {tabla} ({', '.join(columnas)}) VALUES ({', '.join(['%s'] * len(valores))})"
            cursor.execute(query, valores)
            conexion.commit()
            conexion.close()
            print(f"Datos insertados en {tabla}.")
        except Exception as e:
            conexion.rollback()
            print(f"Error al insertar datos en {tabla}: {e}")
            conexion.close()

# Crear usuarios
usuarios_ids = []

# Abrir archivo antes del bucle
with open("usuarios.txt", "w", encoding="utf-8") as archivo:
    for i in range(1000):
        nombre = fake.first_name()
        apellido = fake.last_name()
        correo = fake.unique.email()
        telefono = fake.numerify(text='####-####')
        contraseña_plana = fake.password()
        contraseña = generate_password_hash(contraseña_plana)
        direccion = fake.address().replace("\n", ", ")
        rol = "Cliente"

        insertar_datos(
            'usuarios',
            ['nombre', 'apellido', 'correo', 'telefono', 'contraseña_hash', 'rol', 'direccion'],
            [nombre, apellido, correo, telefono, contraseña, rol, direccion]
        )

        # Guardar email y contraseña sin hash
        archivo.write(f"Email: {correo}\n")
        archivo.write(f"Contraseña: {contraseña_plana}\n")
        archivo.write("-" * 30 + "\n")

        # Obtener el id del usuario recién insertado
        with conectar_bd() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT MAX(id_usuario) FROM usuarios")
                user_id = cursor.fetchone()[0]
                usuarios_ids.append(user_id)

# Obtener los productos disponibles desde la base de datos
productos_disponibles = obtener_productos_disponibles()

# Crear métodos de pago por usuario
metodos_pago_ids = {}
for uid in usuarios_ids:
    tipo = random.choice(['Tarjeta de Crédito', 'Tarjeta de Débito', 'PayPal'])
    numero = fake.credit_card_number() if "Tarjeta" in tipo else None
    expiracion = generar_fecha_expiracion() if numero else None
    cvv = fake.credit_card_security_code() if numero else None

    insertar_datos(
        'metodos_pago',
        ['id_usuario', 'tipo', 'numero_tarjeta', 'fecha_expiracion', 'cvv'],
        [uid, tipo, numero, expiracion, cvv]
    )

    # Obtener el id del método de pago recién insertado
    with conectar_bd() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id_metodo_pago) FROM metodos_pago WHERE id_usuario = %s", (uid,))
            mp_id = cursor.fetchone()[0]
            metodos_pago_ids[uid] = mp_id

# Insertar 5000 pedidos
for _ in range(5000):
    usuario = random.choice(usuarios_ids)
    metodo_pago = metodos_pago_ids[usuario]

    # Verificar que productos_disponibles no esté vacío y que num_productos no exceda la cantidad de productos disponibles
    if productos_disponibles:
        num_productos = random.randint(1, min(len(productos_disponibles), 5))  # Limitar num_productos a la cantidad de productos disponibles
        productos_seleccionados = random.sample(productos_disponibles, num_productos)
    else:
        print("No hay productos disponibles.")
        productos_seleccionados = []

    # Si productos_seleccionados está vacío, manejar el caso apropiadamente
    if not productos_seleccionados:
        print("No se seleccionaron productos.")
    else:
        # Continuar con la creación del pedido si hay productos seleccionados
        total = 0.0
        productos_json = []
        for prod in productos_seleccionados:
            cantidad = random.randint(1, 3)
            productos_json.append({"id_producto": prod[0], "cantidad": cantidad})
            total += float(prod[2]) * cantidad  # Usar el precio del producto (prod[2])
        
        # Insertar el pedido (continúa con el resto del código)
    estado = random.choice(['Pendiente', 'En Proceso', 'Enviado', 'Entregado', 'Cancelado'])

    insertar_datos(
        'pedidos',
        ['id_usuario', 'id_metodo_pago', 'estado', 'productos', 'total'],
        [usuario, metodo_pago, estado, Json(productos_json), round(total, 2)]
    )
