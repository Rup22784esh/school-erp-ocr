from paddleocr import PaddleOCR
import cv2
import numpy as np
import logging
import gc

logger = logging.getLogger("SCHOOL_ERP_PRO_ENGINE")

# Initialize PaddleOCR globally for reuse (saves time on every call)
# lang='hi' supports Devanagari/Hindi/Nepali script
ocr = PaddleOCR(use_angle_cls=True, lang='hi', use_gpu=False, show_log=False)

def classify_document(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ["question", "marks", "allowed", "terminal", "exam"]):
        return "Question Paper"
    if any(k in text_lower for k in ["date of birth", "registration", "admission"]):
        return "Admission Form"
    if any(k in text_lower for k in ["terminal", "marksheet", "grade", "percentage"]):
        return "Marksheet"
    if any(k in text_lower for k in ["identity card", "id card", "student card"]):
        return "Student ID"
    return "General Document"

def warm_up_ocr():
    """Dummy call to load models into memory."""
    try:
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        ocr.ocr(dummy_img, cls=True)
        logger.info("⚡ PaddleOCR: Engine warmed up in RAM!")
    except Exception as e:
        logger.error(f"❌ Warm-up failed: {e}")

def get_pro_ocr(image_bytes, log_callback=None):
    def send_log(msg):
        if log_callback: log_callback(msg)
        logger.info(msg)

    send_log("⚙️ Step 1: Decoding Image...")
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None: raise ValueError("Invalid image")
    
    # PaddleOCR handles rotation and deskew internally (cls=True)
    send_log("🧠 Step 2: PaddleOCR Processing (16GB RAM mode)...")
    result = ocr.ocr(img, cls=True)
    
    # Extract text and confidence
    extracted_text = []
    conf_scores = []
    
    if result and result[0]:
        for line in result[0]:
            text = line[1][0]
            conf = line[1][1]
            extracted_text.append(text)
            conf_scores.append(conf)
            
    full_text = " ".join(extracted_text)
    avg_conf = (np.mean(conf_scores) * 100) if conf_scores else 0
    
    send_log("📊 Step 3: Document Classification...")
    doc_type = classify_document(full_text)

    send_log("✅ Scan Complete!")
    
    # Free up memory just in case
    gc.collect()
    
    return {
        "text": full_text,
        "document_type": doc_type,
        "confidence_avg": float(avg_conf)
    }
