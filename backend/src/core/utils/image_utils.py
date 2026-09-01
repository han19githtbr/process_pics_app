import base64
import re
from io import BytesIO
import numpy as np
from PIL import Image
import cv2

class ImageUtils:
    """Utilitários para manipulação de imagens."""
    
    @staticmethod
    def decode_data_url(data_url: str) -> np.ndarray:
        """Decodifica uma imagem de data URL para array numpy."""
        raw = re.sub(r"^data:image/[^;]+;base64,", "", data_url or "")
        image = Image.open(BytesIO(base64.b64decode(raw))).convert("RGB")
        return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    @staticmethod
    def encode_to_data_url(image: np.ndarray, format: str = 'png') -> str:
        """Codifica uma imagem numpy para data URL."""
        ext = '.png' if format == 'png' else '.jpg'
        _, buffer = cv2.imencode(ext, image)
        encoded = base64.b64encode(buffer).decode('ascii')
        return f"data:image/{format};base64,{encoded}"
    
    @staticmethod
    def resize_if_needed(image: np.ndarray, max_size: int = 1800) -> tuple:
        """Redimensiona imagem se necessário."""
        height, width = image.shape[:2]
        scale = min(1.0, max_size / max(height, width))
        
        if scale < 1.0:
            new_size = (int(width * scale), int(height * scale))
            resized = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
            return resized, scale
        
        return image, 1.0