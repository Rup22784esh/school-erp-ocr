from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
from ocr_engine import get_pro_ocr
import logging
import anyio

# Setup detailed logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SCHOOL_ERP_PRO")

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>School ERP - Smart OCR</title>
        <style>
            :root { --primary: #2563eb; --bg: #f8fafc; --card: #ffffff; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); color: #1e293b; margin: 0; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
            .container { background: var(--card); padding: 2rem; border-radius: 1rem; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1); width: 90%; max-width: 600px; text-align: center; }
            h1 { color: var(--primary); margin-bottom: 0.5rem; }
            p { color: #64748b; margin-bottom: 2rem; }
            .upload-area { border: 2px dashed #cbd5e1; padding: 2rem; border-radius: 0.75rem; cursor: pointer; transition: all 0.2s; margin-bottom: 1.5rem; position: relative; }
            .upload-area:hover { border-color: var(--primary); background: #f1f5f9; }
            input[type="file"] { position: absolute; width: 100%; height: 100%; top: 0; left: 0; opacity: 0; cursor: pointer; }
            button { background: var(--primary); color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; font-weight: 600; cursor: pointer; width: 100%; font-size: 1rem; }
            button:disabled { background: #94a3b8; cursor: not-allowed; }
            #result { margin-top: 2rem; text-align: left; display: none; }
            .result-card { background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid var(--primary); }
            pre { white-space: pre-wrap; word-wrap: break-word; font-size: 0.9rem; background: #fff; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #e2e8f0; }
            .loading { display: none; margin: 1rem 0; font-weight: bold; color: var(--primary); }
            .badge { display: inline-block; padding: 0.25rem 0.5rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.5rem; }
            .badge-info { background: #dbeafe; color: #1e40af; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎓 School ERP OCR</h1>
            <p>Upload a Marksheet, ID Card, or Admission Form</p>
            
            <div class="upload-area" id="drop-zone">
                <span id="file-name">Click or Drag & Drop Image Here</span>
                <input type="file" id="file-input" accept="image/*">
            </div>
            
            <button id="scan-btn">Start Intelligent Scan</button>
            <div class="loading" id="loader">Processing... Please wait (Tesseract is thinking)</div>

            <div id="result">
                <h3>Scan Results</h3>
                <div class="result-card">
                    <div><span class="badge badge-info" id="doc-type">Document</span></div>
                    <strong>Confidence:</strong> <span id="conf">0</span>%
                    <p><strong>Extracted Text:</strong></p>
                    <pre id="text-output"></pre>
                </div>
            </div>
        </div>

        <script>
            const fileInput = document.getElementById('file-input');
            const fileName = document.getElementById('file-name');
            const scanBtn = document.getElementById('scan-btn');
            const loader = document.getElementById('loader');
            const resultDiv = document.getElementById('result');

            fileInput.onchange = () => {
                if (fileInput.files[0]) fileName.innerText = fileInput.files[0].name;
            };

            scanBtn.onclick = async () => {
                if (!fileInput.files[0]) return alert("Please select a file first");
                
                scanBtn.disabled = true;
                loader.style.display = 'block';
                resultDiv.style.display = 'none';

                const formData = new FormData();
                formData.append("file", fileInput.files[0]);

                try {
                    const response = await fetch("/scan-pro", { method: "POST", body: formData });
                    const data = await response.json();

                    if (data.success) {
                        document.getElementById('doc-type').innerText = data.document_type;
                        document.getElementById('conf').innerText = Math.round(data.confidence_avg);
                        document.getElementById('text-output').innerText = data.text;
                        resultDiv.style.display = 'block';
                    } else {
                        alert("Error: " + data.error);
                    }
                } catch (e) {
                    alert("Connection Failed: Ensure the service is awake.");
                } finally {
                    scanBtn.disabled = false;
                    loader.style.display = 'none';
                }
            };
        </script>
    </body>
    </html>
    """

@app.post("/scan-pro")
async def scan_pro_document(file: UploadFile = File(...)):
    try:
        logger.info(f"PRO Scanning file: {file.filename}")
        content = await file.read()
        result = await anyio.to_thread.run_sync(get_pro_ocr, content)
        return {"success": True, "filename": file.filename, **result}
    except Exception as e:
        logger.error(f"PRO OCR Error for {file.filename}: {str(e)}")
        return {"success": False, "error": str(e)}

@app.get("/health")
def keep_alive():
    return {"status": "alive"}
