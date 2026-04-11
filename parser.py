from fastapi import File, UploadFile, APIRouter
import pandas as pd
import io

router = APIRouter()

# 4. Create a POST endpoint, for example, /uploadfile/, that accepts an Excel file.
@router.post("/uploadfile/", tags=["Excel Processing"])
async def create_upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        df = df.fillna("")

        processed_data = df.to_dict(orient="records")

        # d. Return the processed data or a confirmation message.
        return {"filename": file.filename, "status": "success", "data": processed_data}
    except Exception as e:
        return {"filename": file.filename, "status": "error", "message:": str(e)}
