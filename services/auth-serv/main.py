from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.auth.routes import router as auth_router
from backend.users.routes import router as user_router
#username: steward1
#password: Password123

#labeler
#youssef        password:123456
#annotator

#youness        123456789
app = FastAPI()

# Serve frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
def serve_login():
    return FileResponse("frontend/login.html")
from backend.database.mongodb import db

@app.get("/test-db")
async def test_db():
    try:
        collections = await db.list_collection_names()
        return {"status": "connected", "collections": collections}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# Routers
app.include_router(auth_router)
app.include_router(user_router)
