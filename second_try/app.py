from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, File, Request
from server.parser import router as parser_router

# 2. Initialize the FastAPI application.
app = FastAPI()

app.include_router(parser_router)

templates = Jinja2Templates(directory="client")

# 3. Create a root endpoint (/) that returns a simple welcome message.
@app.get("/", tags=["Root"])
async def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )
