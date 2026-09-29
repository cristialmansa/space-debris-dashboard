from pathlib import Path 

import numpy as np 
import pandas as pd 

pd.set_option("display.max_columns", None)

RAIZ = Path(__file__).resolve().parent
ENTRADA = RAIZ / "data" / "satcat.csv"

df = pd.read_csv(ENTRADA, low_memory = False)

df["LAUNCH_DATE"] = pd.to_datetime(df["LAUNCH_DATE"], errors = "coerce")
df["DECAY_DATE"]  = pd.to_datetime(df["DECAY_DATE"], errors = "coerce")

print("Filas y columnas:", df.shape)
print("\nTipos de objeto:\n", df["OBJECT_TYPE"].value_counts())
print("\nNulos por columna:\n", df.isna().sum())

# CALIDAD DE LOS DATOS
# ¿Cada objeto aparece una sola vez?
print("NORAD_CAT_ID único:", df["NORAD_CAT_ID"].is_unique)

# ¿Hay objetos que reentran antes de haber sido lanzados? 
reentrada_imposible = (df["DECAY_DATE"] < df["LAUNCH_DATE"]).sum()
print("Reentrada antes del lanzamiento:", reentrada_imposible)

# ¿Hay órbitas imposibles? 
orbita_imposible = (df["APOGEE"] < df["PERIGEE"]).sum()
print("Apogeo menor que perigeo:", orbita_imposible)

# Rango temporal del catálogo 
print("Primer lanzamiento:", df["LAUNCH_DATE"].min().date())
print("Último lanzamiento:", df["LAUNCH_DATE"].max().date())

# ¿Alrededor de qué cuerpo orbita cada objeto? 
print("\nCentro de la órbita:\n", df["ORBIT_CENTER"].value_counts().head(6))

# El problema de las fechas del debris
df["LANZAMIENTO"] = df["OBJECT_ID"].str[:8]

fengyun = df[df["LANZAMIENTO"] == "1999-025"]
print("\nFengyun-1C: objetos por tipo\n", fengyun["OBJECT_TYPE"].value_counts())
print("\nAño de LAUNCH_DATE de su debris:\n", fengyun.loc[fengyun["OBJECT_TYPE"] == "DEB", "LAUNCH_DATE"].dt.year.value_counts())

# Solución: Fecha aproximada de catalogación
df["CAT_DATE"] = df.sort_values("NORAD_CAT_ID")["LAUNCH_DATE"].cummax()

for codigo, nombre, anio_real in [("1999-025", "Fengyun-1C (antisatélite)", 2007), ("1993-036", "Cosmos 2251 (colisión con Iridium 33)", 2009)]:
    deb = df[(df["LANZAMIENTO"] == codigo) & (df["OBJECT_TYPE"] == "DEB")] 
    print(f"\n{nombre} - evento real en {anio_real}")
    print(deb["CAT_DATE"].dt.year.value_counts().sort_index().head(6))

# Variables derivadas

# Tipo de objeto en español 
TIPOS = {
    "PAY": "Satélite", 
    "R/B": "Cuerpo de cohete",
    "DEB": "Debris", 
    "UNK": "Desconocido"
}

df["TIPO"] = df["OBJECT_TYPE"].map(TIPOS)

# ¿Orbita la Tierra? ¿Sigue en órbita hoy? 
df["ORBITA_TIERRA"] = df["ORBIT_CENTER"] == "EA"
df["EN_ORBITA"] = df["DECAY_DATE"].isna() & df["ORBITA_TIERRA"]

# Años, para agrupar y filtrar con el slider
df["ANIOS_LANZ"] = df["LAUNCH_DATE"].dt.year 
df["ANIO_CAT"] = df["CAT_DATE"].dt.year

# Altitud media de la órbita en km
df["ALT_MEDIA_KM"] = (df["APOGEE"] + df["PERIGEE"]) / 2 

print("\nObjetos en órbita terrestre hoy:", df["EN_ORBITA"].sum())
print(df.loc[df["EN_ORBITA"], "TIPO"].value_counts())

# Régimen orbital 
apo, peri = df["APOGEE"], df["PERIGEE"]

condiciones = [
    apo.isna(), 
    apo < 2000, 
    (peri < 2000) & (apo >= 2000),
    (peri >= 35286) & (apo <= 36286), 
    apo < 35286,
    peri > 36286,  
]

etiquetas = ["Sin datos", "LEO", "HEO / GTO", "GEO", "MEO", "Más allá de GEO"]

df["REGIMEN"] = np.select(condiciones, etiquetas, default="Elíptica alta")

print("\nObjetos en órbita hoy por régimen y tipo:\n", 
      pd.crosstab(df.loc[df["EN_ORBITA"], "REGIMEN"], df.loc[df["EN_ORBITA"], "TIPO"], margins = True))


# ESTADO OPERATIVO Y PROPIETARIO 

# Códigos de OPS_STATUS_CODE según CelesTrak
ESTADO_OP = {
    "+": "Operativo", 
    "P": "Parcialmente operativo", 
    "B": "Reserva", 
    "S": "Reserva",
    "X": "Operativo intermitente", 
    "-": "No operativo", 
    "D": "Reentrado",
}

df["ESTADO"] = df["OPS_STATUS_CODE"].map(ESTADO_OP).fillna("Sin dato")

# Propietarios más frecuentes. El resto conserva su código original
PROPIETARIOS = {
    "US": "Estados Unidos", 
    "CIS": "URSS / Rusia", 
    "PRC": "China", 
    "FR": "Francia",
    "JPN": "Japón", 
    "IND": "India", 
    "UK": "Reino Unido", 
    "ESA": "Agencia Espacial Europea",
    "GER": "Alemania", 
    "IT": "Italia", 
    "CA": "Canadá", 
    "SPN": "España",
    "SKOR": "Corea del Sur", 
    "AUS": "Australia", 
    "ISS": "Estación Espacial Internacional",
    "ITSO": "Intelsat", 
    "ORB": "ORBCOMM", 
    "GLOB": "Globalstar",
    "CHBZ": "China / Brasil", 
    "TBD": "Por determinar",
}

df["PROPIETARIO"] = df["OWNER"].map(PROPIETARIOS).fillna(df["OWNER"])

en_orbita = df[df["EN_ORBITA"]]
print("\nEstado de los satélites en órbita:\n",
      en_orbita.loc[en_orbita["OBJECT_TYPE"] == "PAY", "ESTADO"].value_counts())
print("\nPropietarios con más objetos en órbita:\n",
      en_orbita["PROPIETARIO"].value_counts().head(6))

# Stock anual: Objetos en órbita terrestre al cierre de cada año 
# Fecha de corte: el último dato disponible en el propio catálogo 
corte = max(df["LAUNCH_DATE"].max(), df["DECAY_DATE"].max())

tierra = df[df["ORBITA_TIERRA"]]
filas = []
for anio in range(1957, corte.year + 1):
    fecha = min(pd.Timestamp(f"{anio}-12-31"), corte)
    en_orbita_ese_anio = (tierra["CAT_DATE"] <= fecha) & (
        tierra["DECAY_DATE"].isna() | (tierra["DECAY_DATE"] > fecha)
    )
    filas.append(tierra.loc[en_orbita_ese_anio, "OBJECT_TYPE"].value_counts().rename(anio))

stock = (
    pd.DataFrame(filas)
    .reindex(columns = ["PAY", "R/B", "DEB", "UNK"])
    .fillna(0)
    .astype(int)
    .rename_axis("ANIO")
    .reset_index()
)

print(f"\nFecha de corte: {corte.date()}")
print("\nStock en años clave:\n", stock[stock["ANIO"].isin([1970, 1990, 2006, 2007, 2008, 2009, 2019, 2026])])

stock.to_csv(RAIZ / "data" / "stock_anual.csv", index = False)
print("\nGuardado: stock_anual.csv")

# Guardar el dataset limpio
SALIDA = RAIZ / "data" / "satcat_limpio.csv"
df.to_csv(SALIDA, index = False)
print(f"\nGuardado: {SALIDA.name} ({len(df):,} filas, {df.shape[1]} columnas)")