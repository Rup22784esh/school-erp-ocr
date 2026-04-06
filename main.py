from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse
from ocr_engine import get_pro_ocr
import logging
import asyncio

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
            
            /* Live Terminal Styles */
            #terminal { background: #0f172a; color: #10b981; text-align: left; padding: 1rem; border-radius: 0.5rem; font-family: monospace; font-size: 0.85rem; height: 180px; overflow-y: auto; margin-top: 1rem; display: none; box-shadow: inset 0 4px 6px rgba(0,0,0,0.3); }
            .term-line { margin-bottom: 4px; border-bottom: 1px solid #1e293b; padding-bottom: 2px; }
            
            #result { margin-top: 2rem; text-align: left; display: none; }
            .result-card { background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid var(--primary); }
            pre { white-space: pre-wrap; word-wrap: break-word; font-size: 0.9rem; background: #fff; padding: 0.5rem; border-radius: 0.25rem; border: 1px solid #e2e8f0; }
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
            
            <div id="terminal"></div>

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
            const terminal = document.getElementById('terminal');
            const resultDiv = document.getElementById('result');

            fileInput.onchange = () => {
                if (fileInput.files[0]) fileName.innerText = fileInput.files[0].name;
            };

            scanBtn.onclick = () => {
                if (!fileInput.files[0]) return alert("Please select a file first");
                
                scanBtn.disabled = true;
                resultDiv.style.display = 'none';
                terminal.style.display = 'block';
                terminal.innerHTML = '<div class="term-line">> Initializing Secure WebSocket Connection...</div>';

                // Connect to WebSocket
                const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
                const ws = new WebSocket(protocol + window.location.host + '/ws-scan');

                ws.onopen = () => {
                    terminal.innerHTML += '<div class="term-line">> Connection Established! Uploading image...</div>';
                    // Send raw image bytes to server
                    ws.send(fileInput.files[0]);
                };

                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    
                    if (data.type === 'log') {
                        terminal.innerHTML += `<div class="term-line">> ${data.message}</div>`;
                        terminal.scrollTop = terminal.scrollHeight; // Auto-scroll
                    } 
                    else if (data.type === 'result') {
                        const res = data.data;
                        document.getElementById('doc-type').innerText = res.document_type;
                        document.getElementById('conf').innerText = Math.round(res.confidence_avg);
                        document.getElementById('text-output').innerText = res.text;
                        resultDiv.style.display = 'block';
                        
                        terminal.innerHTML += '<div class="term-line" style="color: #34d399;">> Process Finished Successfully. Connection Closed.</div>';
                        terminal.scrollTop = terminal.scrollHeight;
                        scanBtn.disabled = false;
                        ws.close();
                    }
                    else if (data.type === 'error') {
                        terminal.innerHTML += `<div class="term-line" style="color: #ef4444;">> ERROR: ${data.message}</div>`;
                        scanBtn.disabled = false;
                        ws.close();
                    }
                };

                ws.onerror = () => {
                    terminal.innerHTML += '<div class="term-line" style="color: #ef4444;">> Network Error: Connection Lost.</div>';
                    scanBtn.disabled = false;
                };

                ws.onclose = () => {
                    console.log("WebSocket Closed");
                };
            };
        </script>
    </body>
    </html>
    """

@app.post("/scan-pro")
async def scan_pro_document(file: UploadFile = File(...)):
    """
    Standard POST endpoint for OCR (legacy/curl support).
    Note: May hit 100s timeout on Render if image is very large.
    """
    try:
        logger.info(f"Scanning via POST: {file.filename}")
        content = await file.read()
        # Using anyio to thread so it doesn't block the async loop
        import anyio
        result = await anyio.to_thread.run_sync(get_pro_ocr, content)
        return {"success": True, "filename": file.filename, **result}
    except Exception as e:
        logger.error(f"POST OCR Error: {str(e)}")
        return {"success": False, "error": str(e)}

@app.websocket("/ws-scan")
async def websocket_scan(websocket: WebSocket):
    await websocket.accept()
    try:
        # 1. Receive Image bytes over WebSocket
        image_bytes = await websocket.receive_bytes()

        # 2. Setup Async Queue for Thread-Safe Logging
        log_queue = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def sync_log_callback(msg):
            # This safely injects logs from the background sync thread into the async event loop
            asyncio.run_coroutine_threadsafe(log_queue.put({"type": "log", "message": msg}), loop)

        # 3. Run heavy OCR in a background thread so it doesn't block the WebSocket
        # executor=None uses the default ThreadPoolExecutor
        future = loop.run_in_executor(None, get_pro_ocr, image_bytes, sync_log_callback)

        # 4. Stream logs to frontend while OCR is processing
        while not future.done():
            try:
                # Wait 0.2s for a log message
                log_message = await asyncio.wait_for(log_queue.get(), timeout=0.2)
                await websocket.send_json(log_message)
            except asyncio.TimeoutError:
                # Keep the connection alive with a tiny empty message if needed, 
                # but sending logs usually does the job.
                continue 

        # 5. Get Final Result from the completed future
        result = await future

        # 6. Flush any remaining logs from the queue
        while not log_queue.empty():
            log_message = log_queue.get_nowait()
            await websocket.send_json(log_message)

        # 7. Send final JSON result
        await websocket.send_json({"type": "result", "data": {"success": True, **result}})

    except WebSocketDisconnect:
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket Error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass

@app.get("/health")
def keep_alive():
    return {"status": "alive"}
