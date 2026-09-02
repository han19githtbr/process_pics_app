import cv2
import numpy as np
from typing import Optional, Tuple
from ..interfaces.image_processor import IImageProcessor
from ..models.processing_options import ProcessingOptions
from ..utils.image_utils import ImageUtils

class OpenCVProcessor(IImageProcessor):
    """Processador de imagens usando OpenCV."""
    
    def to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Passo 2 do trabalho: Conversão dos pixels RGB para escala de cinza.
        Método: Y <- 0.299 * R + 0.587 * G + 0.114 * B
        """
        if image.ndim == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image.copy()

    def smooth_bilateral(self, gray: np.ndarray, d: int = 10,
                         sigma_color: int = 75, sigma_space: int = 75) -> np.ndarray:
        """
        Passo 3 do trabalho: Suavização da Imagem por Filtro Bilateral.
        cv2.bilateralFilter(target_img_grayscale, 10, 75, 75)
        Filtro altamente eficaz na remoção de ruído preservando as bordas das letras.
        """
        return cv2.bilateralFilter(gray, d, sigma_color, sigma_space)

    def binarize_otsu(self, smooth: np.ndarray, invert: Optional[bool] = None) -> Tuple[np.ndarray, float]:
        """
        Passo 4 do trabalho: Binarização (Conversão Preto & Branco via Método de Otsu).
        def BinarizationImg(img):
            T = otsu(img)
            bin[bin > T] = 255
            bin[bin < 255] = 0
            return cv2.bitwise_not(bin)
        """
        # Detecção automática de polaridade do fundo se não for explicitada
        if invert is None:
            border = np.concatenate((
                smooth[0, :], smooth[-1, :],
                smooth[:, 0], smooth[:, -1]
            ))
            # Se a borda tiver mediana alta, o fundo é claro (papel branco) e texto escuro -> inverte (bitwise_not)
            # para letras ficarem brancas (foreground = 255)
            dark_background = float(np.median(border)) < 128
            invert = not dark_background

        t_val, binary = cv2.threshold(smooth, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if invert:
            binary = cv2.bitwise_not(binary)
        return binary, float(t_val)

    def detect_edges(self, binary: np.ndarray, low_threshold: int = 70,
                     high_threshold: int = 150) -> np.ndarray:
        """
        Passo 5 do trabalho: Detecção de Bordas com Algoritmo de Canny.
        cv2.Canny(target_bin, 70, 150)
        Utiliza derivadas direcionais horizontais e verticais para localizar arestas.
        """
        return cv2.Canny(binary, low_threshold, high_threshold)

    def find_contours(self, edges: np.ndarray) -> Tuple[Tuple[np.ndarray, ...], Optional[np.ndarray]]:
        """
        Passo 6 do trabalho: Procurar Contornos.
        cv2.findContours(target_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cv2.CHAIN_APPROX_SIMPLE remove pontos redundantes e comprime contornos.
        """
        return cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    def preprocess(self, image: np.ndarray, options: Optional[ProcessingOptions] = None) -> np.ndarray:
        """Pré-processa a imagem, suportando modo acadêmico (PDF puro) ou aprimorado."""
        options = options or ProcessingOptions()
        gray = self.to_grayscale(image)

        # Se modo acadêmico estrito do PDF
        if getattr(options, 'mode', 'enhanced') == 'academic':
            smooth = self.smooth_bilateral(
                gray,
                d=options.bilateral_d,
                sigma_color=options.bilateral_sigma_color,
                sigma_space=options.bilateral_sigma_space,
            )
            binary, _ = self.binarize_otsu(smooth)
            if options.remove_noise:
                binary = self._remove_small_noise(binary, options.sensitivity)
            return binary

        # Modo aprimorado (PDF + melhorias para robustez com baixo contraste e iluminação)
        smooth = self.smooth_bilateral(
            gray,
            d=options.bilateral_d,
            sigma_color=options.bilateral_sigma_color,
            sigma_space=options.bilateral_sigma_space,
        )

        equalized = smooth
        if options.enhance_contrast:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            equalized = clahe.apply(smooth)

        sensitivity = max(0.1, min(0.8, float(options.sensitivity)))
        block_size = 11
        if sensitivity > 0.6:
            block_size = 15
        elif sensitivity < 0.35:
            block_size = 9
        if block_size % 2 == 0:
            block_size += 1

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
    
    def _remove_small_noise(self, binary: np.ndarray, sensitivity: float = 0.44) -> np.ndarray:
        """Remove pequenos ruídos da imagem binária, preservando letras pequenas em textos densos."""
        height, width = binary.shape
        total_area = height * width
        area_threshold = max(3, int(total_area * (0.00025 if sensitivity <= 0.5 else 0.00012)))
        
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        clean = np.zeros_like(binary)
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= area_threshold:
                clean[labels == i] = 255
        
        return clean
