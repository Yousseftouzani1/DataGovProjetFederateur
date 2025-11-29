from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
import gridfs
from bson import ObjectId
import pandas as pd
import json
import io
import os

# =================== CONFIG MONGODB ===================
client = MongoClient("mongodb://localhost:27017/")
db = client['mydatabase']
fs = gridfs.GridFS(db)

# =================== FASTAPI ===================
app = FastAPI()
templates = Jinja2Templates(directory="templates")  # Crée un dossier templates

# =================== FONCTIONS ===================
def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates()
    df = df.dropna(how='all')
    df = df.fillna('')
    for col in df.select_dtypes(include='object').columns:
        df[col] = df[col].str.lower()
    return df

def save_clean_file(df: pd.DataFrame, original_filename: str) -> str:
    desktop = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop')
    clean_path = os.path.join(desktop, f"cleaned_{original_filename}.csv")
    df.to_csv(clean_path, index=False)
    return clean_path

# =================== ROUTES ===================
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload/")
async def upload_file(request: Request, file: UploadFile = File(...)):
    contents = await file.read()
    preview = None
    
    # Lire le fichier selon son type
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
            preview = df.head().to_dict(orient="records")
        elif file.filename.endswith(".xlsx") or file.filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(contents))
            preview = df.head().to_dict(orient="records")
        elif file.filename.endswith(".json"):
            data = json.loads(contents)
            df = pd.json_normalize(data)
            preview = df.head().to_dict(orient="records")
        elif file.filename.endswith(".txt"):
            df = pd.read_csv(io.BytesIO(contents), delimiter="\t")
            preview = df.head().to_dict(orient="records")
        else:
            preview = ["Aperçu non disponible pour ce type de fichier."]
            df = None
    except Exception as e:
        preview = [f"Erreur lors de la lecture de l'aperçu: {str(e)}"]
        df = None
    
    if df is not None:
        # Nettoyer les données
        df_clean = clean_data(df)
        # Sauvegarder localement sur le bureau
        clean_file_path = save_clean_file(df_clean, os.path.splitext(file.filename)[0])
        # Uploader sur MongoDB
        with open(clean_file_path, "rb") as f:
            file_id = fs.put(f, filename=os.path.basename(clean_file_path))
    else:
        clean_file_path = None
        file_id = None

    return templates.TemplateResponse("result.html", 
                                      {"request": request,
                                       "preview": preview,
                                       "clean_file_path": clean_file_path,
                                       "file_id": str(file_id) if file_id else None})

@app.get("/files/")
def list_files():
    files = [{"filename": f.filename, "id": str(f._id)} for f in fs.find()]
    return {"files": files}

@app.get("/download/{file_id}")
def download_file(file_id: str):
    f = fs.get(ObjectId(file_id))
    return {"filename": f.filename, "content": f.read()}

# =================== LANCER LE SERVEUR ===================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
