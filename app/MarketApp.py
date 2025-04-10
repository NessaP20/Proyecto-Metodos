from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from werkzeug.utils import secure_filename
import os
marketApp = Flask(__name__)
marketApp.secret_key = os.urandom(24)  # Necesario para sesiones y mensajes flash

DATABASE = {
    
    'dbname': 'Supermercado-2',
    'user': 'postgres',
    'password': 'Lun@25',
    'host': 'localhost',  
    'port': '5432' , 
}

        
# Funcion para verificar usuario
def verificar_usuario(correo, contraseña):
    try:
        with psycopg2.connect(**DATABASE) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT id_usuario, nombre, contraseña_hash, rol FROM usuarios WHERE correo = %s",
                    (correo,)
                )
                usuario = cursor.fetchone()
                
                if usuario and check_password_hash(usuario[2], contraseña):
                    return {
                        'id_usuario': usuario[0],
                        'nombre': usuario[1],
                        'rol': usuario[3]
                    }
        return None
    except Exception as e:
        print(f"Error al verificar usuario: {e}")
        return None

# Funciona para crear un nuevo usuario
def registrar_usuario(nombre, apellido, correo, telefono, contraseña, direccion, rol='Cliente'):
    try:
        contraseña_hash = generate_password_hash(contraseña)

        with psycopg2.connect(**DATABASE) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id_usuario FROM usuarios WHERE correo = %s", (correo,))
                if cursor.fetchone():
                    return False, "El correo electrónico ya está registrado"

                cursor.execute(
                    """
                    INSERT INTO usuarios (nombre, apellido, correo, telefono, contraseña_hash, rol, direccion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id_usuario
                    """,
                    (nombre, apellido, correo, telefono, contraseña_hash, rol, direccion)
                )
                id_usuario = cursor.fetchone()[0]
                conn.commit()

                return True, id_usuario
    except Exception as e:
        print(f"Error al registrar usuario: {e}")
        return False, str(e)

# Login necesario para rutas protegidas por ejemplo mi_cuenta.html
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_required_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica que el usuario esté logueado
        if 'usuario_id' not in session:
            flash('Por favor inicie sesión para acceder a esta página', 'warning')
            return redirect(url_for('login'))
        
        # Verifica que el usuario tenga el rol de 'Administrador'
        if session.get('usuario_rol') != 'Administrador':
            flash('Acceso denegado. Solo los administradores pueden acceder a esta página.', 'danger')
            return redirect(url_for('index'))  # Redirige a la página de inicio o donde sea adecuado

        return f(*args, **kwargs)
    
    return decorated_function

# Prueba de conexion de base de datos
try:
    conn = psycopg2.connect(**DATABASE)
    print("Conexión exitosa a la base de datos")
    conn.close()
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")

# Obtener productos
def obtener_productos():
    try:
        with psycopg2.connect(**DATABASE) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id_producto, nombre, descripcion, precio, imagen_url FROM productos LIMIT 500")
                productos = cursor.fetchall()
        
        return [
            {
                'id_producto': p[0],
                'nombre': p[1],
                'descripcion': p[2],
                'precio': p[3],
                'imagen_url': p[4]
            }
            for p in productos
        ]
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return []
    
import json

def obtener_pedidos_usuario(id_usuario):
    try:
        with psycopg2.connect(**DATABASE) as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT id_pedido, fecha_pedido, estado, productos, total
                    FROM pedidos
                    WHERE id_usuario = %s
                    ORDER BY fecha_pedido DESC
                """, (id_usuario,))
                pedidos_raw = cursor.fetchall()

                pedidos = []
                for p in pedidos_raw:
                    productos_json = p[3]  # JSONB con id_producto y cantidad
                    productos_list = []

                    # Extrae lista de ids
                    ids = [item['id_producto'] for item in productos_json]
                    if ids:
                        format_strings = ','.join(['%s'] * len(ids))
                        cursor.execute(f"""
                            SELECT id_producto, nombre, precio
                            FROM productos
                            WHERE id_producto IN ({format_strings})
                        """, tuple(ids))
                        productos_info = {prod[0]: {'nombre': prod[1], 'precio': float(prod[2])} for prod in cursor.fetchall()}

                        for item in productos_json:
                            id_prod = item['id_producto']
                            cantidad = item['cantidad']
                            info = productos_info.get(id_prod, {'nombre': 'Producto desconocido', 'precio': 0.0})
                            productos_list.append({
                                'id_producto': id_prod,
                                'nombre': info['nombre'],
                                'precio': info['precio'],
                                'cantidad': cantidad
                            })

                    pedidos.append({
                        'id_pedido': p[0],
                        'fecha_pedido': p[1],
                        'estado': p[2],
                        'productos': productos_list,
                        'total': float(p[4])
                    })

                return pedidos
    except Exception as e:
        print(f"Error al obtener pedidos del usuario: {e}")
        return []


#Rutas
@marketApp.route('/')
def index():
    productos = obtener_productos()
    return render_template('index.html', productos=productos)

@marketApp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form.get('correo')
        contraseña = request.form.get('contraseña')
        
        usuario = verificar_usuario(correo, contraseña)
        
        if usuario:
            session['usuario_id'] = usuario['id_usuario']
            session['usuario_nombre'] = usuario['nombre']
            session['usuario_rol'] = usuario['rol']
            
            flash(f'Bienvenido, {usuario["nombre"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Correo o contraseña incorrectos', 'danger')
    
    return render_template('login.html')

@marketApp.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('login'))

@marketApp.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        apellido = request.form.get('apellido')
        correo = request.form.get('correo')
        telefono = request.form.get('telefono')
        contraseña = request.form.get('contraseña')
        confirmar_contraseña = request.form.get('confirmar_contraseña')
        direccion = request.form.get('direccion')
        crear_admin = request.form.get('crear_admin')  # <- NUEVO

        # validaciones
        if not all([nombre, apellido, correo, contraseña, confirmar_contraseña, direccion]):
            flash('Por favor complete todos los campos obligatorios', 'danger')
            return render_template('registro.html')

        if contraseña != confirmar_contraseña:
            flash('Las contraseñas no coinciden', 'danger')
            return render_template('registro.html')

        # Si se seleccionó "crear como admin", se cambia el rol
        rol = 'Administrador' if crear_admin else 'Cliente'

        success, result = registrar_usuario(
            nombre, apellido, correo, telefono, contraseña, direccion, rol
        )

        if success:
            flash('Registro exitoso. Ahora puede iniciar sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash(f'Error al registrar: {result}', 'danger')

    return render_template('registro.html')
#Cancelar Pedido
@marketApp.route('/cancelar_pedido/<int:id_pedido>', methods=['POST'])
@login_required
def cancelar_pedido(id_pedido):
    try:
        with psycopg2.connect(**DATABASE) as conn:
            with conn.cursor() as cursor:
                # Verificamos si el pedido pertenece al usuario y no ha sido entregado
                cursor.execute("""
                    SELECT estado, id_usuario FROM pedidos WHERE id_pedido = %s
                """, (id_pedido,))
                pedido = cursor.fetchone()

                if not pedido:
                    flash('Pedido no encontrado', 'danger')
                    return redirect(url_for('mi_cuenta'))
                
                estado, id_usuario = pedido
                # Solo puede cancelar el pedido si no está entregado
                if estado == 'Entregado':
                    flash('Este pedido ya ha sido entregado y no puede ser cancelado.', 'danger')
                    return redirect(url_for('mi_cuenta'))
                
                if id_usuario != session.get('usuario_id'):
                    flash('No tienes permiso para cancelar este pedido.', 'danger')
                    return redirect(url_for('mi_cuenta'))
                
                # Actualizamos el estado del pedido a 'Cancelado'
                cursor.execute("""
                    UPDATE pedidos
                    SET estado = 'Cancelado'
                    WHERE id_pedido = %s
                """, (id_pedido,))
                conn.commit()

                flash('Pedido cancelado exitosamente.', 'success')
                return redirect(url_for('mi_cuenta'))
    except Exception as e:
        print(f"Error al cancelar pedido: {e}")
        flash('Hubo un error al intentar cancelar el pedido.', 'danger')
        return redirect(url_for('mi_cuenta'))

@marketApp.route('/mi-cuenta')
@login_required
def mi_cuenta():
    pedidos = obtener_pedidos_usuario(session['usuario_id'])
    return render_template('mi_cuenta.html', pedidos=pedidos)

@marketApp.context_processor
def inject_user():
    return {
        'usuario_id': session.get('usuario_id'),
        'usuario_nombre': session.get('usuario_nombre'),
        'usuario_rol': session.get('usuario_rol')
    }

def obtener_categorias():
    """Obtiene todas las categorías de la base de datos"""
    try:
        with psycopg2.connect(**DATABASE) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id_categoria, nombre FROM categorias")
                return {nombre: id for id, nombre in cursor.fetchall()}
    except Exception as e:
        print(f"Error al obtener categorías: {e}")
        return {}

def agregar_producto_db(nombre, descripcion, precio, id_categoria, imagen_url=None):
    """Inserta un nuevo producto en la base de datos"""
    try:
        with psycopg2.connect(**DATABASE) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO productos (nombre, descripcion, precio, id_categoria, imagen_url)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id_producto
                    """,
                    (nombre, descripcion, precio, id_categoria, imagen_url)
                )
                id_producto = cursor.fetchone()[0]
                conn.commit()
                return True, id_producto
    except psycopg2.IntegrityError as ie:
        conn.rollback()
        return False, f"Error de integridad: {ie}"
    except Exception as e:
        conn.rollback()
        return False, f"Error al insertar producto: {e}"

@marketApp.route('/agregar_producto', methods=['GET', 'POST'])
@login_required_admin
def agregar_producto():
    categorias = obtener_categorias()
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario
            nombre = request.form.get('nombre')
            descripcion = request.form.get('descripcion')
            precio = float(request.form.get('precio', 0))
            categoria_nombre = request.form.get('categoria')
            
           
            if not nombre or len(nombre) > 255:
                flash('Nombre inválido (requerido, máx 255 caracteres)', 'danger')
                return render_template('agregar_producto.html', categorias=categorias)
            
            if precio <= 0:
                flash('El precio debe ser mayor a 0', 'danger')
                return render_template('agregar_producto.html', categorias=categorias)
            
            if not descripcion or len(descripcion) > 500:
                flash('descripcion es necesaria')
                return render_template('agregar_producto.html', categorias=categorias)
          
            id_categoria = categorias.get(categoria_nombre)
            if not id_categoria:
                flash('Categoría no válida', 'danger')
                return render_template('agregar_producto.html', categorias=categorias)
            
            # Manejar imagen
            imagen_url = None
            if 'imagen_file' in request.files:
                file = request.files['imagen_file']
                if file.filename != '':
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(marketApp.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    imagen_url = f"/static/uploads/{filename}"
            
            if not imagen_url:
                imagen_url = request.form.get('imagen_url') or None
            
            # Insertar en BD
            success, result = agregar_producto_db(
                nombre=nombre,
                descripcion=descripcion,
                precio=precio,
                id_categoria=id_categoria,
                imagen_url=imagen_url
            )
            
            if success:
                flash(f'Producto "{nombre}" agregado! ID: {result}', 'success')
                return redirect(url_for('agregar_producto'))
            else:
                flash(f'Error: {result}', 'danger')
        
        except ValueError:
            flash('Formato de precio inválido', 'danger')
        except Exception as e:
            flash(f'Error inesperado: {str(e)}', 'danger')
    
    return render_template('agregar_producto.html', categorias=categorias.keys())


@marketApp.route('/agregar_carrito/<int:producto_id>')
def agregar_carrito(producto_id):
    producto = obtener_producto_por_id(producto_id)  
    if 'carrito' not in session:
        session['carrito'] = []
    session['carrito'].append(producto) 
    session.modified = True 
    return redirect(url_for('index'))  

@marketApp.route('/carrito')
def carrito():
    productos_en_carrito = session.get('carrito', [])
    return render_template('carrito.html', productos=productos_en_carrito)
def obtener_producto_por_id(id_producto):
    productos=obtener_productos()
    return next((producto for producto in productos if producto['id']==id_producto), None)

@marketApp.route('/agregar_al_carrito/<int:producto_id>')
def agregar_al_carrito(producto_id):
    
    producto = obtener_producto_por_id(producto_id)  

    if producto:
        if 'carrito' not in session:
            session['carrito'] = []

        session['carrito'].append(producto)

    return redirect(url_for('carrito'))


if __name__ == '__main__':
    marketApp.run(debug=True)