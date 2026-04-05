import cv2
import numpy as np
import pytesseract
from pytesseract import Output
import logging

logger = logging.getLogger("SCHOOL_ERP_PRO_ENGINE")

def deskew(img):
    """
    Automatically detects the angle of the text and rotates the image to be horizontal.
    """
    coords = np.column_stack(np.where(img > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    # Handle the angle range correctly
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
    """
    Intelligent document classification based on keywords.
    """
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

def get_pro_ocr(image_bytes):
    """
    Pro-grade OCR with deskewing, confidence filtering, and classification.
    """
    # 1. Decode & Resize (Free Tier Safety)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None: raise ValueError("Invalid image")
    
    h, w = img.shape[:2]
    if w > 1500:
        img = cv2.resize(img, (1500, int(h * (1500 / w))), interpolation=cv2.INTER_AREA)

    # 2. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    # 3. Deskewing (The 'Magic' step)
    deskewed_img = deskew(binary)

    # 4. OCR with Data (Coordinates & Confidence)
    custom_config = r'--oem 1 --psm 3'
    # Use bitwise_not because Tesseract prefers black text on white background
    final_for_ocr = cv2.bitwise_not(deskewed_img)
    
    data = pytesseract.image_to_data(final_for_ocr, lang='eng+nep+equ', config=custom_config, output_type=Output.DICT)

    # 5. Smart Filtering (Confidence > 60%)
    clean_words = []
    for i in range(len(data['text'])):
        if int(data['conf'][i]) > 60:
            word = data['text'][i].strip()
            if word:
                clean_words.append(word)

    extracted_text = " ".join(clean_words)
    
    # 6. Classification
    doc_type = classify_document(extracted_text)

    return {
        "text": extracted_text,
        "document_type": doc_type,
        "confidence_avg": np.mean([int(c) for c in data['conf'] if int(c) > 0])
    }
