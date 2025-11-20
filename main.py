from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.auth.routes import router as auth_router
from backend.users.routes import router as user_router

app = FastAPI()

# Serve frontend
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
def serve_login():
    return FileResponse("frontend/login.html")

# Routers
app.include_router(auth_router)
app.include_router(user_router)
