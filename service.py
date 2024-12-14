import pandas
from typing import Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup

# Función para obtener datos de Finviz
def fetch_finviz_data(symbol: str) -> pd.DataFrame:
    url = f"https://finviz.com/quote.ashx?t={symbol}&ty=c&ta=1&p=d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    # Realizar la solicitud HTTP
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Analizar el contenido de la página con BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Buscar la tabla específica
    table = soup.find('table', class_='js-table-ratings styled-table-new is-rounded is-small')
    if table is None:
        raise ValueError(f"No se encontró la tabla deseada para el símbolo {symbol}. Verifica la estructura HTML de la página.")

    # Extraer las filas de la tabla
    rows = table.find_all('tr')

    # Extraer encabezados de la tabla
    headers = [th.text.strip() for th in rows[0].find_all('th')]

    # Extraer datos de las filas
    data = []
    for row in rows[1:]:
        cols = row.find_all('td')
        data.append([col.text.strip() if col.text.strip() else None for col in cols])  # Manejar valores vacíos como None

    # Crear un DataFrame
    df = pd.DataFrame(data, columns=headers)

    return df