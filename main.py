from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def ruta_principal():
    return {"mensaje": "¡Mi servidor para WhatsApp está vivo!"}