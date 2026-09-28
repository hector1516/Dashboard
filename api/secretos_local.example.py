# Plantilla. En el contenedor, el entrypoint genera `secretos_local.py` a partir
# de las variables de entorno (HUB_DB_*); este archivo es para desarrollo local.
import os

DB_SERVER = os.environ.get("HUB_DB_SERVER", "10.188.141.15")
DB_USER = os.environ.get("HUB_DB_USER", "sa")
DB_PASSWORD = ""   # <- la sacás de HUB_DB_PASSWORD o la ponés acá (NUNCA al repo)
DB_DATABASE = os.environ.get("HUB_DB_DATABASE", "ECCSA_Admon")
