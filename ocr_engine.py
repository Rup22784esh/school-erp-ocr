import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import logging

logger = logging.getLogger("SCHOOL_ERP_PRO_ENGINE")

def deskew(img):
    """Automatically detects the angle of the text and rotates the image to be horizontal."""
    coords = np.column_stack(np.where(img > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    return rotated

def classify_document(text):
    """Intelligent document classification based on keywords."""
    text_lower = text.lower()
    if any(k in text_lower for k in ["date of birth", "registration", "admission"]):
        return "Admission Form"
    if any(k in text_lower for k in ["terminal", "marksheet", "grade", "percentage"]):
        return "Marksheet"
    if any(k in text_lower for k in ["identity card", "id card", "student card"]):
        return "Student ID"
    if any(k in text_lower for k in ["fee receipt", "payment", "invoice"]):
        return "Fee Receipt"
    return "General Document"

def get_pro_ocr(image_bytes, log_callback=None):
    """
    Pro-grade OCR optimized for Render Free Tier (512MB RAM).
    Removed 'equ' (Math) to ensure stability and speed.
    """
    def send_log(msg):
        if log_callback:
            log_callback(msg)
        logger.info(msg)

    send_log("⚙️ Step 1: Image Decode & Validation...")
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None: 
        raise ValueError("Invalid image")
    
    h, w = img.shape[:2]
    # Reduced to 1200px to save significant RAM
    if w > 1200:
        send_log(f"📐 Auto-resizing image from width {w}px to 1200px to save RAM...")
        img = cv2.resize(img, (1200, int(h * (1200 / w))), interpolation=cv2.INTER_AREA)

    send_log("🖼️ Step 2: Adaptive Thresholding (Fixing lights & shadows)...")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10)

    send_log("📏 Step 3: Deskewing (Fixing camera angles)...")
    deskewed_img = deskew(binary)

    # Manual Garbage Collection to free up RAM before heavy Tesseract work
    import gc
    gc.collect()

    send_log("🧠 Step 4: Tesseract OCR Engine Start (eng+nep)...")
    custom_config = r'--oem 1 --psm 3'
    final_for_ocr = cv2.bitwise_not(deskewed_img)
    
    # Removed '+equ' to prevent OOM (Out of Memory) crashes
    data = pytesseract.image_to_data(final_for_ocr, lang='eng+nep', config=custom_config, output_type=Output.DICT)

    send_log("🧹 Step 5: Filtering low-confidence text (>60% only)...")
    clean_words = []
    for i in range(len(data['text'])):
        if int(data['conf'][i]) > 60:
            word = data['text'][i].strip()
            if word:
                clean_words.append(word)

    extracted_text = " ".join(clean_words)
    
    send_log("📂 Step 6: Smart Document Classification...")
    doc_type = classify_document(extracted_text)

    send_log("✅ Scan Complete!")
    
    # Calculate average confidence for non-empty text blocks
    conf_scores = [int(c) for c in data['conf'] if int(c) > 0]
    avg_conf = np.mean(conf_scores) if conf_scores else 0

    return {
        "text": extracted_text,
        "document_type": doc_type,
        "confidence_avg": avg_conf
    }
