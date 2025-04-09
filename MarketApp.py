from flask import Flask, render_template
import psycopg2

marketApp = Flask(__name__)


DATABASE = {
    'dbname': 'Supermarket',
    'user': 'postgres',
    'password': '1928',
    'host': 'localhost',  
    'port': '5432'  
}

#ry:
   #conn = psycopg2.connect(**DATABASE)
   #print("Conexión exitosa a la base de datos")
   #conn.close()
#xcept Exception as e:
  # print(f"Error al conectar a la base de datos: {e}")


def obtener_productos():
    try:
        with psycopg2.connect(**DATABASE) as conn:
            with conn.cursor() as cursor:
               cursor.execute("SELECT id_producto, nombre, descripcion, precio, imagen_url FROM producto LIMIT 500")  
               productos = cursor.fetchall() 
            
        return [{'id_producto': p[0], 'nombre': p[1], 'descripcion': p[2], 'precio': p[3], 'imagen_url': p[4]} for p in productos]
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        return []
    
    


@marketApp.route('/')
def index():
    productos=obtener_productos()
    return render_template('index.html', productos=productos)




if __name__ == '__main__':
    marketApp.run(debug=True)