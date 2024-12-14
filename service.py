import pandas
from typing import Optional
import pandas as pd
import requests
from bs4 import BeautifulSoup
import warnings
import json
import yfinance as yf

# Desactivar warnings innecesarios

# Función para obtener datos de Finviz
def fetch_finviz_data(symbol: str) -> pd.DataFrame:
    url = f"https://finviz.com/quote.ashx?t={symbol}&ty=c&ta=1&p=d"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    warnings.filterwarnings("ignore", category=FutureWarning)
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


import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import yfinance as yf
import warnings
import time

# Desactivar warnings innecesarios
warnings.filterwarnings("ignore", category=FutureWarning)


def get_dataroma_data(n_pags=4, output_file="dataroma_data.json"):
    headersS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }
    all_data = []
    headers = None

    for i in range(1, n_pags + 1):
        url = f"https://www.dataroma.com/m/g/portfolio.php?L={i}"
        response = requests.get(url, headers=headersS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Buscar la tabla
        table = soup.find('table', id='grid')
        if not table:
            continue

        rows = table.find_all('tr')

        # Obtener los encabezados una sola vez
        if i == 1:
            headers = [header.text.strip() for header in rows[0].find_all('td')]

        # Obtener los datos de la tabla
        page_data = [
            [col.text.strip() for col in row.find_all('td')]
            for row in rows[1:-1]
        ]
        all_data.extend(page_data)

    # Crear el DataFrame
    df = pd.DataFrame(all_data, columns=headers)

    # Eliminar las columnas no deseadas
    columns_to_drop = ["Stock", "%\u25BC", "Hold Price*", "Max %", "52 WeekLow", "% Above52 WeekLow", "52 WeekHigh"]
    df.drop(columns=columns_to_drop, inplace=True, errors='ignore')

    # Transformar nombres de columnas restantes
    column_mapping = {
        "Symbol": "Symbol",
        "Ownershipcount": "Ownershipcount",
        "CurrentPrice": "CurrentPrice",
    }
    df.rename(columns=column_mapping, inplace=True)

    # Limpiar valores numéricos
    df["CurrentPrice"] = df["CurrentPrice"].replace('[\$,]', '', regex=True).astype(float, errors='ignore')

    # Agregar columnas adicionales para almacenar nuevos datos
    df['TargetPrice'] = None
    df['5 Year EPS Growth'] = None
    df['Earnings Yield'] = None

    # Definir la función para obtener información de las acciones
    def get_stock_info(symbol, retries=3):
        """Obtiene el precio objetivo, crecimiento EPS a 5 años, rendimiento de ganancias y el precio actual de una acción."""
        for attempt in range(retries):
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                target_mean_price = info.get('targetMeanPrice')
                five_year_eps_growth = info.get('earningsGrowth')
                trailing_eps = info.get('trailingEps')
                previous_close = info.get('previousClose')
                current_price = info.get('currentPrice')

                earnings_yield = None
                if isinstance(trailing_eps, (int, float)) and isinstance(previous_close, (int, float)):
                    earnings_yield = trailing_eps / previous_close

                return target_mean_price, five_year_eps_growth, earnings_yield, current_price
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Too Many Requests
                    print(f"Too many requests for {symbol}, waiting before retrying...")
                    time.sleep(10 * (attempt + 1))  # Esperar más tiempo en cada intento
                else:
                    print(f"HTTP error for {symbol}: {e}")
                    break
            except Exception as e:
                print(f"Error retrieving data for {symbol} (attempt {attempt + 1}): {e}")
                break
        return None, None, None, None

    # Obtener la información de cada acción
    for index, row in df.iterrows():
        symbol = row['Symbol']
        try:
            target_mean_price, five_year_eps_growth, earnings_yield, current_price = get_stock_info(symbol)
            if target_mean_price is not None:
                df.at[index, 'TargetPrice'] = target_mean_price
            if five_year_eps_growth is not None:
                df.at[index, '5 Year EPS Growth'] = five_year_eps_growth
            if earnings_yield is not None:
                df.at[index, 'Earnings Yield'] = earnings_yield
        except Exception as e:
            print(f"Final error retrieving data for {symbol}: {e}")

    # Rellenar NaN con valores predeterminados
    for col in df.select_dtypes(include=[float]).columns:
        df[col].fillna(0, inplace=True)  # Reemplazar NaN en valores numéricos con 0
    for col in df.select_dtypes(include=[object]).columns:
        df[col].fillna("", inplace=True)  # Reemplazar NaN en valores de texto con ""

    # Guardar JSON a un archivo
    json_data = df.to_dict(orient="records")
    with open(output_file, "w", encoding="utf-8") as json_file:
        json.dump(json_data, json_file, indent=4, ensure_ascii=False)

    return json_data


