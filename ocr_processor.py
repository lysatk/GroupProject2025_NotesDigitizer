# ocr_processor.py
from PIL import Image
import easyocr
import numpy as np # EasyOCR works well with numpy arrays

# Global reader instance to load models only once per language set
# We'll initialize it lazily
EASYOCR_READER = None
CURRENT_EASYOCR_LANGS = []

def get_available_languages():
    """
    Returns a list of common EasyOCR supported language codes.
    Full list: https://www.jaided.ai/easyocr (see "Available Languages" section)
    For simplicity, we'll list a few common ones. Users can type others.
    """
    # Common language codes for EasyOCR
    return ['en', 'pl']
    # If you want users to be able to use any of EasyOCR's many languages,
    # you might let them type it in, or provide a more exhaustive list.


def _initialize_reader(lang_list):
    """Initializes or re-initializes the EasyOCR reader if necessary."""
    global EASYOCR_READER, CURRENT_EASYOCR_LANGS
    # Check if the reader needs to be (re)initialized
    # This happens if it's the first time, or if the requested languages changed
    if EASYOCR_READER is None or set(lang_list) != set(CURRENT_EASYOCR_LANGS):
        print(f"Initializing EasyOCR reader for languages: {lang_list}. This may take a moment...")
        try:
            # gpu=True if you have a compatible GPU and CUDA installed, otherwise False
            EASYOCR_READER = easyocr.Reader(lang_list, gpu=False)
            CURRENT_EASYOCR_LANGS = lang_list
            print("EasyOCR reader initialized.")
        except Exception as e:
            EASYOCR_READER = None # Ensure it's None on failure
            raise RuntimeError(f"Failed to initialize EasyOCR reader: {e}")
    return EASYOCR_READER


def extract_text_from_image(pil_image: Image.Image, lang: str = 'en'):
    """
    Extracts text from a PIL Image using EasyOCR.
    Args:
        pil_image: PIL.Image object.
        lang: Language code for OCR (e.g., 'en', 'fr').
              EasyOCR can accept a list of languages too, e.g., ['en', 'fr']
              For simplicity in the GUI, we'll pass a single lang, but wrap it in a list.
    Returns:
        Extracted text as a string, or an error message string.
    """
    if not isinstance(pil_image, Image.Image):
        return "OCR Error: Invalid image input."

    # Ensure the language is in a list format for EasyOCR
    lang_list = [lang] if not isinstance(lang, list) else lang
    
    try:
        reader = _initialize_reader(lang_list)
        if reader is None: # Should not happen if _initialize_reader raises error, but defensive
            return "OCR Error: EasyOCR reader could not be initialized."

        # EasyOCR prefers a NumPy array
        # Convert PIL image to NumPy array
        # If image is RGBA, convert to RGB first as EasyOCR might not handle alpha well directly
        if pil_image.mode == 'RGBA':
            image_for_ocr = np.array(pil_image.convert('RGB'))
        else:
            image_for_ocr = np.array(pil_image)

        # detail=0 means it returns only the text, not bounding boxes etc.
        # paragraph=True tries to join nearby text into paragraphs.
        result = reader.readtext(image_for_ocr, detail=0, paragraph=True)
        
        extracted_text = "\n".join(result)
        return extracted_text.strip()

    except RuntimeError as re: # Catch specific initialization errors
        return f"OCR Error: {re}"
    except Exception as e:
        # This will catch errors during readtext or other unexpected issues
        return f"OCR Error: An unexpected error occurred with EasyOCR: {e}"