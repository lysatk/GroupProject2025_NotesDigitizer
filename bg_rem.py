import cv2
import numpy as np
from PIL import Image

def pil_to_cv(pil_image):
    """Converts a PIL image to an OpenCV image (BGR or Grayscale)."""
    if pil_image.mode == 'RGBA':
        # Convert RGBA to RGB then to BGR
        pil_image_rgb = pil_image.convert('RGB')
        open_cv_image = cv2.cvtColor(np.array(pil_image_rgb), cv2.COLOR_RGB2BGR)
    elif pil_image.mode == 'P': # Palette mode
        # Convert to RGB then to BGR
        pil_image_rgb = pil_image.convert('RGB')
        open_cv_image = cv2.cvtColor(np.array(pil_image_rgb), cv2.COLOR_RGB2BGR)
    elif pil_image.mode == 'L': # Grayscale PIL
        # OpenCV expects a 2D array for grayscale
        open_cv_image = np.array(pil_image)
    elif pil_image.mode == 'RGB':
        open_cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    else: # Default to converting to RGB then BGR
        pil_image_rgb = pil_image.convert('RGB')
        open_cv_image = cv2.cvtColor(np.array(pil_image_rgb), cv2.COLOR_RGB2BGR)
    return open_cv_image

def cv_to_pil(cv_image):
    """Converts an OpenCV image to a PIL image."""
    if len(cv_image.shape) == 2: # Grayscale
        return Image.fromarray(cv_image)
    elif len(cv_image.shape) == 3 and cv_image.shape[2] == 3: # Color (BGR)
        return Image.fromarray(cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB))
    else:
        raise ValueError(f"Unsupported OpenCV image format for PIL conversion: shape {cv_image.shape}")


def remove_background(cv_image_input, block_size=21, c_value=10):
    """
    Removes or simplifies the background of an image using adaptive thresholding.
    Args:
        cv_image_input: OpenCV image (NumPy array, BGR or Grayscale).
        block_size: Block size for adaptive thresholding (odd number).
        c_value: Constant C for adaptive thresholding.
    Returns:
        Processed OpenCV image (binary, grayscale).
    """
    if len(cv_image_input.shape) == 3 and cv_image_input.shape[2] == 3: # If it's a color image (BGR)
        gray_image = cv2.cvtColor(cv_image_input, cv2.COLOR_BGR2GRAY)
    elif len(cv_image_input.shape) == 2: # If it's already grayscale
        gray_image = cv_image_input
    else:
        raise ValueError("Input image must be BGR color or grayscale for background removal.")

    # Adaptive Thresholding
    processed_cv_image = cv2.adaptiveThreshold(
        gray_image,
        255,        # Max value to assign
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, # Text will be black, background white
        block_size,
        c_value
    )
    return processed_cv_image