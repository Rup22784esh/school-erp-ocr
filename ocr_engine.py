import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import logging
import re

logger = logging.getLogger("SCHOOL_ERP_PRO_ENGINE")

def auto_rotate_osd(img):
    """Detects and fixes 90/180/270 degree rotations."""
    try:
        osd = pytesseract.image_to_osd(img)
        angle = re.search('(?<=Rotate: )\d+', osd).group(0)
        angle = int(angle)
        
        if angle != 0:
            logger.info(f"🔄 Auto-Rotating image by {angle} degrees...")
            if angle == 90: return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            elif angle == 180: return cv2.rotate(img, cv2.ROTATE_180)
            elif angle == 270: return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    except Exception as e:
        logger.warning(f"OSD rotation detection failed: {e}")
    return img

def deskew(img):
    """Fixes minor tilts (-45 to 45 degrees)."""
    coords = np.column_stack(np.where(img > 0))
    if len(coords) == 0: return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45: angle = -(90 + angle)
    else: angle = -angle
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

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
    """Tesseract ko RAM mein load karne ke liye dummy run."""
    try:
        dummy_img = np.zeros((10, 10), dtype=np.uint8)
        pytesseract.image_to_string(dummy_img, lang='eng+nep', config='--oem 1 --psm 3')
        logger.info("⚡ OCR Engine: Warmed up and ready in RAM!")
    except Exception as e:
        logger.error(f"❌ Warm-up failed: {e}")

def get_pro_ocr(image_bytes, log_callback=None):
    def send_log(msg):
        if log_callback: log_callback(msg)
        logger.info(msg)

    send_log("⚙️ Step 1: Image Decode...")
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None: raise ValueError("Invalid image")
    
    send_log("🔄 Step 2: Auto-Rotating (Checking if upside down)...")
    img = auto_rotate_osd(img)

    h, w = img.shape[:2]
    if w > 1200:
        send_log("📐 Optimization: Resizing for 512MB RAM safety...")
        img = cv2.resize(img, (1200, int(h * (1200 / w))), interpolation=cv2.INTER_AREA)

    send_log("🖼️ Step 3: Preprocessing (Adaptive Binarization)...")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10)

    send_log("📏 Step 4: Deskewing (Straightening tilts)...")
    deskewed_img = deskew(binary)

    import gc
    gc.collect()

    send_log("🧠 Step 5: Tesseract OCR Start (RAW Full Content Mode)...")
    custom_config = r'--oem 1 --psm 3'
    final_for_ocr = cv2.bitwise_not(deskewed_img)
    
    # NEW: Using image_to_string directly to get the FULL content with formatting (newlines/tabs)
    # No confidence filtering is applied to this raw output.
    raw_text = pytesseract.image_to_string(final_for_ocr, lang='eng+nep', config=custom_config)

    send_log("📊 Step 6: Calculating Confidence & Classification...")
    # We still use image_to_data just to get the average confidence score
    data = pytesseract.image_to_data(final_for_ocr, lang='eng+nep', config=custom_config, output_type=Output.DICT)
    
    doc_type = classify_document(raw_text)
    
    conf_scores = [int(c) for c in data['conf'] if int(c) > 0]
    avg_conf = np.mean(conf_scores) if conf_scores else 0

    send_log("✅ Scan Complete! Showing all detected characters.")
    return {
        "text": raw_text.strip(),
        "document_type": doc_type,
        "confidence_avg": avg_conf
    }
