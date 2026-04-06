# VIPERP OCR - Hugging Face Space

[![Hugging Face Spaces](https://img.shields.io/badge/Hugging%20Face%20Spaces-blue?style=flat-square&logo=huggingface)](https://huggingface.co/spaces/my-erp-ocr/viperp-ocr)

यह प्रोजेक्ट Hugging Face Spaces पर FastAPI और EasyOCR का उपयोग करके एक शक्तिशाली OCR (Optical Character Recognition) API प्रदान करता है।

## 🚀 मुख्य विशेषताएं

*   **सरल API:** `multipart/form-data` के माध्यम से इमेज अपलोड करके तुरंत टेक्स्ट प्राप्त करें।
*   **विश्वसनीय OCR:** EasyOCR इंजन का उपयोग करके सटीक टेक्स्ट निष्कर्षण।
*   **Hugging Face Integration:** कहीं भी डिप्लॉय करने के लिए तैयार, Hugging Face Spaces पर होस्ट किया गया।
*   **उपयोग में आसान:** Termux या किसी भी `curl` क्लाइंट से आसानी से इंटीग्रेट किया जा सकता है।

## 🔗 API एंडपॉइंट्स

### 1. होम (स्टेटस जांच)
सर्वर की लाइव स्थिति की जाँच करें।
- **URL:** `https://my-erp-ocr-viperp-ocr.hf.space/`
- **Method:** `GET`
- **Response:**
  ```json
  {
    "status": "EasyOCR is running perfectly on Hugging Face!"
  }
  ```

### 2. OCR निष्पादन
किसी इमेज से टेक्स्ट निकालने के लिए।
- **URL:** `https://my-erp-ocr-viperp-ocr.hf.space/ocr`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Parameters:**
    - `file`: (Binary) आपकी इमेज फाइल जिसे आप प्रोसेस करना चाहते हैं।
- **Response (Success):**
  ```json
  {
    "success": true,
    "text": "यहाँ इमेज से निकाला गया टेक्स्ट आएगा..."
  }
  ```
- **Response (Error):**
  ```json
  {
    "success": false,
    "message": "कोई फाइल अपलोड नहीं हुई या फाइल प्रोसेस करने में एरर।"
  }
  ```

## 🛠️ लोकल सेटअप (Docker का उपयोग करके)

यदि आप इस OCR इंजन को अपने लोकल डेवलपमेंट एनवायरनमेंट में चलाना चाहते हैं, तो आप Docker का उपयोग कर सकते हैं।

1.  **Dockerfile:** प्रोजेक्ट में प्रदान की गई `Dockerfile` का उपयोग करके एक इमेज बनाएं:
    ```bash
    docker build -t viperp-ocr .
    ```
2.  **कंटेनर चलाएं:**
    ```bash
    docker run -d -p 8000:80 viperp-ocr
    ```
    अब आप `http://localhost:8000` पर API को एक्सेस कर सकते हैं।

## 🧪 टेस्ट कैसे करें (Termux से)

आप नीचे दी गई `curl` कमांड का उपयोग करके आसानी से API का परीक्षण कर सकते हैं। `YOUR_IMAGE.jpg` को अपनी इमेज फ़ाइल के पाथ से बदलें।

```bash
curl -X POST "https://my-erp-ocr-viperp-ocr.hf.space/ocr" 
     -H "accept: application/json" 
     -H "Content-Type: multipart/form-data" 
     -F "file=@YOUR_IMAGE.jpg"
```

## 📁 प्रोजेक्ट स्ट्रक्चर

*   **app.py:** FastAPI सर्वर और EasyOCR का मुख्य लॉजिक।
*   **Dockerfile:** Hugging Face Spaces और लोकल Docker डिप्लॉयमेंट के लिए कंटेनर कॉन्फ़िगरेशन।
*   **requirements.txt:** आवश्यक Python लाइब्रेरी (fastapi, easyocr, opencv-python, uvicorn, आदि)।
*   **packages.txt:** आवश्यक सिस्टम पैकेज (जैसे libgl1, libglib2.0-0)।
*   **IMG_*.jpg:** टेस्ट इमेज (अब रूट डायरेक्टरी में)।

## 🧑‍💻 लेखक

*   **Mrrupess** ([my-erp-ocr](https://huggingface.co/my-erp-ocr))
*   **Hugging Face Space:** [viperp-ocr](https://huggingface.co/spaces/my-erp-ocr/viperp-ocr)

## 📄 लाइसेंस

यह प्रोजेक्ट [MIT License](LICENSE) के तहत लाइसेंस प्राप्त है - अधिक जानकारी के लिए `LICENSE` फ़ाइल देखें। (नोट: यदि `LICENSE` फ़ाइल मौजूद नहीं है, तो आपको इसे बनाना होगा या लाइसेंस निर्दिष्ट करना होगा।)
