from sqlalchemy import create_engine
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de la base de datos
DB_HOST ="localhost"
DB_NAME ="Supermercado"
DB_USER ="postgres"
DB_PASS ="1928"
DB_PORT ="5432"

# Crear la conexión con SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
# Función para extraer datos de la tabla "Elija una Tabla de la DB "
def obtener_tabla_df():
    try:
        # Consulta SQL
        consulta = "SELECT id_usuario, estado, productos, total FROM pedidos"
        # Leer los datos en un DataFrame
        df = pd.read_sql(consulta, engine)
        return df
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None
# Función para graficar la duración de las películas
def graficar_algun_detalle_numerico_de_la_tabla(df):
    plt.figure(figsize=(10, 5))
    sns.histplot(df["estado"], bins=15, kde=True, color="skyblue")
    plt.xlabel("detalle_numerico")
    plt.ylabel("Frecuencia")
    plt.title("Distribución del dato a graficar")
    plt.grid(axis='y',linestyle='--',alpha=0.7)
    plt.show()

def graficar_cantidad_por_año(df):
    plt.figure(figsize=(10,5))
    sns.countplot(data=df, x="total", hue="total", palette="coolwarm", legend=False)
    plt.xticks(rotation=45)
    plt.show()


if __name__=="__main__":
    df_tabla=obtener_tabla_df()
    if df_tabla is not None:
        print(df_tabla.head())
        graficar_algun_detalle_numerico_de_la_tabla(df_tabla)
        graficar_cantidad_por_año(df_tabla)
