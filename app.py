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

import runpy 
from pathlib import Path 

import pandas as pd 

# DATOS 
RAIZ = Path(__file__).resolve().parent
