from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
import gridfs
from bson import ObjectId
import pandas as pd
import json
import io

# =================== CONFIG MONGODB ===================
client = MongoClient("mongodb://localhost:27017/")
db = client['mydatabase']
fs = gridfs.GridFS(db)

# =================== FASTAPI ===================
app = FastAPI()
templates = Jinja2Templates(directory="templates")  # crée un dossier templates

# =================== ROUTES ===================
@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    return templates.TemplateResponse("uploadcsv.html", {"request": request})

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    preview = None
    
  
    try:
        if file.filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(contents))
            preview = df.head().to_dict(orient="records")
        elif file.filename.endswith(".xlsx") or file.filename.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(contents))
            preview = df.head().to_dict(orient="records")
        elif file.filename.endswith(".json"):
            data = json.loads(contents)
            preview = data if isinstance(data, list) else [data]
        elif file.filename.endswith(".txt"):
            preview = contents.decode('utf-8').splitlines()[:5]
        else:
            preview = ["Aperçu non disponible pour ce type de fichier."]
    except Exception as e:
        preview = [f"Erreur lors de la lecture de l'aperçu: {str(e)}"]
    

    file_id = fs.put(contents, filename=file.filename)
    
    return {
        "file_id": str(file_id),
        "filename": file.filename,
        "preview": preview
    }

@app.get("/files/")
def list_files():
    files = [{"filename": f.filename, "id": str(f._id)} for f in fs.find()]
    return {"files": files}

@app.get("/download/{file_id}")
def download_file(file_id: str):
    f = fs.get(ObjectId(file_id))
    return {"filename": f.filename, "content": f.read()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
