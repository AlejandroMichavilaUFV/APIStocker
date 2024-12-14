from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

# Inicializar la aplicación
app = FastAPI()

# Permitir solicitudes de cualquier origen (o especificar los orígenes permitidos)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Puedes especificar una lista de orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],  # Permite cualquier método (GET, POST, etc.)
    allow_headers=["*"],  # Permite cualquier encabezado
)

# Cargar el DataFrame inicial desde el JSON
dataframe = pd.read_json("dataroma_data.json")

# Modelo para la creación de filas
class RowData(BaseModel):
    Symbol: str  # Este es el identificador único
    Ownershipcount: Optional[int] = None
    CurrentPrice: Optional[float] = None
    TargetPrice: Optional[float] = None
    EPSGrowth5Year: Optional[float] = None
    EarningsYield: Optional[float] = None

# Endpoint para cargar un dataframe desde un JSON inicial
@app.post("/load_dataframe/")
def load_dataframe(data: List[RowData]):
    global dataframe
    dataframe = pd.DataFrame([row.dict() for row in data]).replace({None: np.nan})
    return {"message": "Dataframe cargado exitosamente", "rows": len(dataframe)}

# Operación CREATE: Agregar una nueva fila al dataframe
@app.post("/add_row/")
def add_row(row: RowData):
    global dataframe
    if row.Symbol in dataframe["Symbol"].values:
        raise HTTPException(status_code=400, detail="El Symbol ya existe en el dataframe")
    new_row = pd.DataFrame([row.dict()]).replace({None: np.nan})
    dataframe = pd.concat([dataframe, new_row], ignore_index=True)
    return {"message": "Fila añadida exitosamente", "Symbol": row.Symbol}

# Operación READ: Leer todas las filas o una específica
@app.get("/get_rows/")
def get_rows(Symbol: Optional[str] = None):
    global dataframe
    if Symbol is not None:
        row = dataframe[dataframe["Symbol"] == Symbol]
        if row.empty:
            raise HTTPException(status_code=404, detail="Fila no encontrada")
        return row.to_dict(orient="records")
    return dataframe.to_dict(orient="records")

# Operación UPDATE: Actualizar una fila existente
@app.put("/update_row/")
def update_row(row: RowData):
    global dataframe
    if row.Symbol not in dataframe["Symbol"].values:
        raise HTTPException(status_code=404, detail="El Symbol no existe en el dataframe")
    dataframe.loc[dataframe["Symbol"] == row.Symbol, :] = pd.DataFrame([row.dict()]).iloc[0].replace({None: np.nan})
    return {"message": "Fila actualizada exitosamente", "Symbol": row.Symbol}

# Operación DELETE: Eliminar una fila por Symbol
@app.delete("/delete_row/")
def delete_row(Symbol: str):
    global dataframe
    if Symbol not in dataframe["Symbol"].values:
        raise HTTPException(status_code=404, detail="El Symbol no existe en el dataframe")
    dataframe = dataframe[dataframe["Symbol"] != Symbol]
    return {"message": "Fila eliminada exitosamente", "Symbol": Symbol}

# Endpoint auxiliar para obtener el esquema del dataframe actual
@app.get("/get_dataframe_schema/")
def get_dataframe_schema():
    global dataframe
    return {"columns": dataframe.columns.tolist(), "rows": len(dataframe)}

# Endpoint adicional para mostrar todo el dataframe
@app.get("/get_full_dataframe/")
def get_full_dataframe():
    global dataframe
    return dataframe.to_dict(orient="records")

# Endpoint para servir un archivo HTML
@app.get("/home", response_class=HTMLResponse)
def home_page():
    with open("static/index.html", "r") as file:
        html_content = file.read()
    return html_content

# Endpoint para servir un archivo HTML
@app.get("/search", response_class=HTMLResponse)
def search_page():
    with open("static/search.html", "r") as file:
        html_content = file.read()
    return html_content