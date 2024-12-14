import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import yfinance as yf
import warnings
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
    def get_stock_info(symbol):
        """Obtiene el precio objetivo, crecimiento EPS a 5 años, rendimiento de ganancias y el precio actual de una acción."""
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

    # Obtener la información de cada acción
    for index, row in df.iterrows():
        symbol = row['Symbol']
        try:
            target_mean_price, five_year_eps_growth, earnings_yield, current_price = get_stock_info(symbol)
            df.at[index, 'TargetPrice'] = target_mean_price
            df.at[index, '5 Year EPS Growth'] = five_year_eps_growth
            df.at[index, 'Earnings Yield'] = earnings_yield
        except Exception as e:
            print(f"Error retrieving data for {symbol}: {e}")

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

# Ejemplo de uso
data = get_dataroma_data(n_pags=4)
print(f"Datos guardados en dataroma_data.json")
