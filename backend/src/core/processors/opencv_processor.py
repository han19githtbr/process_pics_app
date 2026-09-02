import cv2
import numpy as np
from typing import Optional, Tuple
from ..interfaces.image_processor import IImageProcessor
from ..models.processing_options import ProcessingOptions
from ..utils.image_utils import ImageUtils

class OpenCVProcessor(IImageProcessor):
    """Processador de imagens usando OpenCV."""
    
    def preprocess(self, image: np.ndarray, options: Optional[ProcessingOptions] = None) -> np.ndarray:
        """Pré-processa a imagem, mantendo robustez para textos claros/escuros e baixo contraste."""
        options = options or ProcessingOptions()

        if image.ndim == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        # Redução de ruído preservando detalhes do texto
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)

        # Equalização local para melhorar contraste em textos fracos
        equalized = denoised
        if options.enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            equalized = clahe.apply(denoised)

        sensitivity = max(0.1, min(0.8, float(options.sensitivity)))
        block_size = 11
        if sensitivity > 0.6:
            block_size = 15
        elif sensitivity < 0.35:
            block_size = 9
        if block_size % 2 == 0:
            block_size += 1

        # Texto claro em fundo escuro precisa de uma máscara sem inversão.
        # As bordas normalmente representam o fundo e são mais confiáveis que a média global.
        border = np.concatenate((
            equalized[0, :], equalized[-1, :],
            equalized[:, 0], equalized[:, -1]
        ))
        dark_background = float(np.median(border)) < 128
        threshold_type = cv2.THRESH_BINARY if dark_background else cv2.THRESH_BINARY_INV

        adaptive = cv2.adaptiveThreshold(
            equalized,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            threshold_type,
            block_size,
            int(round(10 - sensitivity * 10)),
        )

        _, otsu = cv2.threshold(equalized, 0, 255, threshold_type + cv2.THRESH_OTSU)

        # Escolhe o limiar mais promissor para o tipo de texto detectado
        adaptive_white = cv2.countNonZero(adaptive)
        otsu_white = cv2.countNonZero(otsu)
        if sensitivity >= 0.55:
            binary = adaptive if adaptive_white > otsu_white * 0.8 else otsu
        else:
            binary = otsu if otsu_white > adaptive_white else adaptive

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        if options.remove_noise:
            binary = self._remove_small_noise(binary, sensitivity)
        return binary
    
    def resize_if_needed(self, image: np.ndarray, max_size: int = 1800) -> Tuple[np.ndarray, float]:
        """Redimensiona imagem se necessário."""
        return ImageUtils.resize_if_needed(image, max_size)
    
    def binarize(self, image: np.ndarray, method: str = 'auto') -> np.ndarray:
        """Binariza a imagem."""
        return self.preprocess(image)

    def detect_edges(self, binary: np.ndarray, low_threshold: int = 70,
                     high_threshold: int = 150) -> np.ndarray:
        """Detecta bordas com Canny, conforme o fluxo descrito no trabalho."""
        return cv2.Canny(binary, low_threshold, high_threshold)
    
    def _remove_small_noise(self, binary: np.ndarray, sensitivity: float = 0.44) -> np.ndarray:
        """Remove pequenos ruídos da imagem binária, preservando letras pequenas em textos densos."""
        height, width = binary.shape
        total_area = height * width
        area_threshold = max(3, int(total_area * (0.00025 if sensitivity <= 0.5 else 0.00012)))
        
        # Análise de componentes conectados
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        clean = np.zeros_like(binary)
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= area_threshold:
                clean[labels == i] = 255
        
        return clean
