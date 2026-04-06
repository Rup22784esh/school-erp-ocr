from fastapi import FastAPI, UploadFile, File
import easyocr
import numpy as np
import cv2
import gc

app = FastAPI()

# EasyOCR Reader setup
# Note: gpu=False since Hugging Face basic spaces don't always have GPU
reader = easyocr.Reader(['en'], gpu=False)

@app.get("/")
def home():
    return {"status": "EasyOCR is running perfectly on Hugging Face!"}

@app.post("/ocr")
async def perform_ocr(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"success": False, "error": "Could not decode image"}
        
        # Perform OCR
        result = reader.readtext(img, detail=0)
        extracted_text = " ".join(result)
        
        # Cleanup
        del img, nparr, contents
        gc.collect()
            
        return {
            "success": True,
            "text": extracted_text.strip()
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
