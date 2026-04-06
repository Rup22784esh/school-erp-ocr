import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import logging
import re

logger = logging.getLogger("SCHOOL_ERP_PRO_ENGINE")

def auto_rotate_osd(img):
    """
    Detects if the image is rotated by 90, 180, or 270 degrees using Tesseract OSD
    and rotates it to be upright.
    """
    try:
        # Get Orientation info
        osd = pytesseract.image_to_osd(img)
        angle = re.search('(?<=Rotate: )\d+', osd).group(0)
        angle = int(angle)
        
        if angle != 0:
            logger.info(f"🔄 Auto-Rotating image by {angle} degrees...")
            if angle == 90:
                return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            elif angle == 180:
                return cv2.rotate(img, cv2.ROTATE_180)
            elif angle == 270:
                return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    except Exception as e:
        logger.warning(f"OSD rotation detection failed: {e}")
    return img

def deskew(img):
    """Fine-tunes small tilts (angles between -45 and 45)."""
    coords = np.column_stack(np.where(img > 0))
    if len(coords) == 0: return img
    
    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    (h, w) = img.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def classify_document(text):
    text_lower = text.lower()
    if any(k in text_lower for k in ["question paper", "terminal exam", "maximum marks", "time allowed"]):
        return "Question Paper"
    if any(k in text_lower for k in ["date of birth", "registration", "admission"]):
        return "Admission Form"
    if any(k in text_lower for k in ["terminal", "marksheet", "grade", "percentage"]):
        return "Marksheet"
    if any(k in text_lower for k in ["identity card", "id card", "student card"]):
        return "Student ID"
    return "General Document"

def warm_up_ocr():
    try:
        dummy_img = np.zeros((10, 10), dtype=np.uint8)
        pytesseract.image_to_string(dummy_img, lang='eng+nep', config='--oem 1 --psm 3')
        logger.info("⚡ OCR Engine: Warmed up and ready!")
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
    
    # 1. First Pass: Auto-Rotate Large Angles (90/180/270)
    send_log("🔄 Step 2: Checking Orientation (OSD)...")
    img = auto_rotate_osd(img)

    # 2. Resize for RAM safety
    h, w = img.shape[:2]
    if w > 1200:
        send_log("📐 Resizing for 512MB RAM optimization...")
        img = cv2.resize(img, (1200, int(h * (1200 / w))), interpolation=cv2.INTER_AREA)

    send_log("🖼️ Step 3: Preprocessing (Binarization)...")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10)

    send_log("📏 Step 4: Fine Deskewing (Fixing small tilts)...")
    deskewed_img = deskew(binary)

    import gc
    gc.collect()

    send_log("🧠 Step 5: Tesseract OCR Start (Full Page Mode)...")
    # PSM 3 is best for full question papers
    custom_config = r'--oem 1 --psm 3'
    final_for_ocr = cv2.bitwise_not(deskewed_img)
    
    data = pytesseract.image_to_data(final_for_ocr, lang='eng+nep', config=custom_config, output_type=Output.DICT)

    send_log("🧹 Step 6: Cleaning results...")
    clean_words = []
    for i in range(len(data['text'])):
        if int(data['conf'][i]) > 50: # Slightly lower threshold for dense question papers
            word = data['text'][i].strip()
            if word: clean_words.append(word)

    extracted_text = " ".join(clean_words)
    
    send_log("📂 Step 7: Intelligent Classification...")
    doc_type = classify_document(extracted_text)

    send_log("✅ Scan Complete!")
    
    conf_scores = [int(c) for c in data['conf'] if int(c) > 0]
    avg_conf = np.mean(conf_scores) if conf_scores else 0

    return {
        "text": extracted_text,
        "document_type": doc_type,
        "confidence_avg": avg_conf
    }
