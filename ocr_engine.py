import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import logging
import re

logger = logging.getLogger("SCHOOL_ERP_PRO_ENGINE")

def auto_rotate_osd(img):
    """Detects and fixes 90/180/270 degree rotations efficiently."""
    try:
        # Optimization: OSD on a smaller, grayscale version is much faster
        small_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if small_gray.shape[1] > 800:
            scale = 800.0 / small_gray.shape[1]
            small_gray = cv2.resize(small_gray, (800, int(small_gray.shape[0] * scale)))
        
        osd = pytesseract.image_to_osd(small_gray, config='--psm 0 --oem 1')
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
    """Fixes minor tilts faster."""
    coords = np.column_stack(np.where(img > 0))
    if len(coords) < 10: return img
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45: angle = -(90 + angle)
    else: angle = -angle
    
    if abs(angle) < 0.5: return img # Skip if almost straight
    
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

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
        pytesseract.image_to_string(dummy_img, lang='eng', config='--oem 1 --psm 3')
        logger.info("⚡ OCR Engine: Warmed up and ready in RAM!")
    except Exception as e:
        logger.error(f"❌ Warm-up failed: {e}")

def get_pro_ocr(image_bytes, log_callback=None):
    def send_log(msg):
        if log_callback: log_callback(msg)
        logger.info(msg)

    send_log("⚙️ Step 1: Decoding & Resizing...")
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None: raise ValueError("Invalid image")
    
    # TURBO SPEED: Reduced to 800px. Lower resolution = much faster OCR.
    h, w = img.shape[:2]
    max_dim = 800 
    if w > max_dim or h > max_dim:
        scale = max_dim / float(max(w, h))
        img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)

    send_log("🔄 Step 2: Orientation...")
    img = auto_rotate_osd(img)

    send_log("🖼️ Step 3: Preprocessing...")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Deskewing needs binary, but OCR likes grayscale
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    send_log("📏 Step 4: Deskewing...")
    # Get rotation matrix from binary but apply to grayscale for OCR quality/speed
    coords = np.column_stack(np.where(binary > 0))
    if len(coords) > 10:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45: angle = -(90 + angle)
        else: angle = -angle
        if abs(angle) > 0.5:
            (h, w) = gray.shape[:2]
            M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            gray = cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

    # Add 10px white border (Tesseract works better with padding)
    gray = cv2.copyMakeBorder(gray, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255])

    send_log("🧠 Step 5: Tesseract OCR Engine (LSTM)...")
    # Using grayscale 'gray' instead of 'binary'. LSTM engine is optimized for this.
    custom_config = r'--oem 1 --psm 3'
    
    # image_to_data call
    data = pytesseract.image_to_data(gray, lang='eng+nep', config=custom_config, output_type=Output.DICT)
    
    # Extract text and confidence in one loop
    full_text = []
    conf_scores = []
    
    last_block_num = -1
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        if text:
            # Add newlines based on block/line changes to preserve structure
            if data['block_num'][i] != last_block_num and last_block_num != -1:
                full_text.append("\n")
            full_text.append(text + " ")
            conf_scores.append(int(data['conf'][i]))
            last_block_num = data['block_num'][i]

    raw_text = "".join(full_text).strip()
    avg_conf = np.mean(conf_scores) if conf_scores else 0
    
    send_log("📊 Step 6: Classification...")
    doc_type = classify_document(raw_text)

    send_log("✅ Scan Complete!")
    return {
        "text": raw_text,
        "document_type": doc_type,
        "confidence_avg": float(avg_conf)
    }
