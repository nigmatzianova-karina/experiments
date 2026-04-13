from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, File, Request
from server.parser import router as parser_router

app = FastAPI()

app.include_router(parser_router)

templates = Jinja2Templates(directory="client")

@app.get("/", tags=["Root"])
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )
