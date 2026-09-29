"""
¿Cómo hemos transformado el espacio alrededor de la Tierra desde el Sputnik en 1957? 
Se necesita saber: 
- Cuántos objetos hay en órbita en cada momento de la historia
- De qué tipo son (satélites útiles o basura)
- Quién los ha puesto ahí 
- Dónde están concentrados

El SATCAT es el registro civil de los objetos espaciales. 
Cada vez que el ejército de EEUU detecta con radares y telescopios un objeto artificial en órbita, le asigna un número (NORAD_CAT_ID) y lo apunta en el catálogo. Cada fila del csv es un objeto: el Sputnik, un Starlink, un trozo de metal de una explosión. El catálogo solo incluye lo que se puede rastrear, que en órbita baja son objetos de unos 10 cm hacia arriba. 
Es un registro que nunca borra a nadie. Cuando un objeto cae y se desintegra en la atmósfera, no se elimina: se le apunta la fecha de reentrada en DECAY_DATE, como una fecha de defunción. Los que no tienen esa fecha es porque siguen arriba. 
Los tipos de objetos son cuatro: 
- PAY (payload): un satélite, lo que se lanzó con un propósito 
- R/B (rocket body): la etapa superior del cohete que lo llevó y que se quedó en órbita
- DEB (debris): fragmentos de explosiones, colisiones o piezas desprendidas 
- UNK: objetos sin identificar 

"""
from dash import Dash, html
import runpy 
from pathlib import Path 

import pandas as pd 

# DATOS 
RAIZ = Path(__file__).resolve().parent
DATA = RAIZ / "data"
LIMPIO = DATA / "satcat_limpio.csv"
STOCK = DATA / "stock_anual.csv"

if not (LIMPIO.exists() and STOCK.exists()):
    runpy.run_path(str(RAIZ / "limpieza_satcat.py"), run_name = "__main__")

df = pd.read_csv(LIMPIO, parse_dates = ["LAUNCH_DATE", "DECAY_DATE", "CAT_DATE"], low_memory = False)
stock = pd.read_csv(STOCK)

#print(df.shape)
#print(stock.tail(3))


ANIO_REF = 2019 # referencia: último año antes del despliegue masivo de megaconstelaciones

# Cálculo de KPIs 
en_orbita = df[df["EN_ORBITA"]]

total_hoy = len(en_orbita)
sat_operativos = int(((en_orbita["OBJECT_TYPE"] == "PAY") & (en_orbita["ESTADO"] == "Operativo")).sum())
debris_hoy = int((en_orbita["OBJECT_TYPE"] == "DEB").sum())

# Valores del año de referencia, sacados de la tabla de stock 
ref = stock.loc[stock["ANIO"] == ANIO_REF].iloc[0]
total_ref = int(ref[["PAY", "R/B", "DEB", "UNK"]].sum())
debris_ref = int(ref["DEB"])

def fmt(n: int) -> str: 
    """Número con punto como separador de miles (formato español)"""
    return f"{n:,}".replace(",", ".")

print("Objetos en órbita:", fmt(total_hoy), f"(×{total_hoy / total_ref:.1f} respecto a {ANIO_REF})")
print("Satélites operativos:", f"{sat_operativos / total_hoy:.0%}", f"({fmt(sat_operativos)})")
print("Debris:", fmt(debris_hoy), f"(en {ANIO_REF}: {fmt(debris_ref)})")

# Componentes de interfaz 
def tarjeta_kpi(titulo: str, valor: str, referencia: str) -> html.Div:
    """Tarjeta con un KPI grande y su referencia debajo."""
    return html.Div(
        className = "kpi", 
        children = [
            html.Div(titulo, className = "kpi-titulo"), 
            html.Div(valor, className = "kpi-valor"), 
            html.Div(referencia, className = "kpi-ref"),
        ],
    )

kpis = html.Div(
    className = "fila-kpi", 
    children=[
        tarjeta_kpi("Objetos en órbita hoy", fmt(total_hoy),
                    f"×{total_hoy / total_ref:.1f} respecto a {ANIO_REF} ({fmt(total_ref)})"),
        tarjeta_kpi("Satélites operativos", f"{sat_operativos / total_hoy:.0%}",
                    f"{fmt(sat_operativos)} de {fmt(total_hoy)} objetos"),
        tarjeta_kpi("Fragmentos de debris", fmt(debris_hoy),
                    f"{fmt(debris_ref)} en {ANIO_REF}"),
    ],
)

# Aplicación
app = Dash(__name__, title = "The Crowded Sky")
server = app.server # Servidor Flask subyacente (útil para desplegar)

app.layout = html.Div(
    className = "contenedor", 
    children = [
        html.H1("THE CROWDED SKY"), 
        html.P("¿Cómo hemos transformado el espacio alrededor de la Tierra desde el Sputnik (1957)?",
               className = "subtitulo"), 
        kpis, 
        html.P("Fuente: Satellite Catalog (SATCAT), CelesTrak", className = "fuente"),
    ],
)

if __name__ == "__main__":
    app.run(debug = True)