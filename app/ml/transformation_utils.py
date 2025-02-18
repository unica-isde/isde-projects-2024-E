from PIL import ImageEnhance
from app.ml.classification_utils import fetch_image

def transform_image(image_id : str, color : float, brightness :float, contrast : float, sharpness :float):
    """Transforms the image with the specified parameters."""
    img = fetch_image(image_id)
    img = ImageEnhance.Color(img).enhance(color)
    img = ImageEnhance.Brightness(img).enhance(brightness)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)
    return img
