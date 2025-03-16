from dotenv import load_dotenv
from pathlib import Path
import os
import requests

# Charger les variables d'environnement depuis un fichier .env
project_folder = os.path.expanduser('~/LogIAnalyzer')
load_dotenv(os.path.join(project_folder, '.env'))

API_KEY = os.getenv("API_KEY")

