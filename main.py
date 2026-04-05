from fastapi import FastAPI, UploadFile, File
from ocr_engine import get_pro_ocr
import logging
import anyio

# Setup detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SCHOOL_ERP_PRO")

app = FastAPI()

@app.get("/")
def home():
    return {"message": "PRO School ERP OCR API is Running"}

@app.post("/scan-pro")
async def scan_pro_document(file: UploadFile = File(...)):
    """
    Enterprise-grade OCR endpoint.
    Automatically: Deskews, Filters Noise, and Classifies Document type.
    """
    try:
        logger.info(f"PRO Scanning file: {file.filename}")
        content = await file.read()
        
        # PRO Tip: Run CPU-bound Tesseract in a threadpool to prevent blocking the main event loop
        result = await anyio.to_thread.run_sync(get_pro_ocr, content)
        
        return {
            "success": True,
            "filename": file.filename,
            **result
        }
    except Exception as e:
        logger.error(f"PRO OCR Error for {file.filename}: {str(e)}")
        return {
            "success": False, 
            "error": "Failed to process document. Ensure high-quality capture."
        }

@app.get("/health")
def keep_alive():
    """Keep-alive endpoint for cron-job.org."""
    return {"status": "alive"}
