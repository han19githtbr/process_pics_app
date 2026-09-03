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

    def detect_dark_background(self, gray_or_smooth: np.ndarray) -> bool:
        """
        Determina se a imagem possui fundo escuro com texto claro (True) ou fundo claro com texto escuro (False).
        Avalia a região interna e a mediana geral, evitando distorção por molduras periféricas ou vinhetas.
        """
        h, w = gray_or_smooth.shape[:2]
        inner = gray_or_smooth[int(h * 0.15):int(h * 0.85), int(w * 0.15):int(w * 0.85)]
        inner_med = float(np.median(inner)) if inner.size > 0 else float(np.median(gray_or_smooth))
        global_med = float(np.median(gray_or_smooth))
        return (0.7 * inner_med + 0.3 * global_med) < 128

    def binarize_otsu(self, smooth: np.ndarray, invert: Optional[bool] = None) -> Tuple[np.ndarray, float]:
        """
        Passo 4 do trabalho: Binarização (Conversão Preto & Branco via Método de Otsu).
        def BinarizationImg(img):
            T = otsu(img)
            bin[bin > T] = 255
            bin[bin < 255] = 0
            return cv2.bitwise_not(bin)
        """
        dark_background = self.detect_dark_background(smooth)
        if invert is None:
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
        """Pré-processa a imagem, suportando modo acadêmico (PDF puro) ou aprimorado com supressão de ruídos de fundo."""
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

        # Modo aprimorado (PDF + normalização morfológica contra fundos coloridos, vinhetas e desenhos)
        smooth = self.smooth_bilateral(
            gray,
            d=options.bilateral_d,
            sigma_color=options.bilateral_sigma_color,
            sigma_space=options.bilateral_sigma_space,
        )

        h, w = smooth.shape[:2]
        dark_background = self.detect_dark_background(smooth)

        if options.enhance_contrast:
            # Normalização morfológica TopHat / BlackHat
            # Suprime fundos não-uniformes, molduras grandes e variações de iluminação
            kernel_size = min(35, max(15, int(min(h, w) * 0.08)))
            if kernel_size % 2 == 0:
                kernel_size += 1
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))

            if dark_background:
                norm = cv2.morphologyEx(smooth, cv2.MORPH_TOPHAT, kernel)
            else:
                norm = cv2.morphologyEx(smooth, cv2.MORPH_BLACKHAT, kernel)

            t_otsu, binary = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            if t_otsu < 15:
                thresh_type = cv2.THRESH_BINARY if dark_background else cv2.THRESH_BINARY_INV
                _, binary = cv2.threshold(smooth, 0, 255, thresh_type + cv2.THRESH_OTSU)
        else:
            thresh_type = cv2.THRESH_BINARY if dark_background else cv2.THRESH_BINARY_INV
            _, binary = cv2.threshold(smooth, 0, 255, thresh_type + cv2.THRESH_OTSU)

        # Refinamento morfológico suave para consolidação dos traços das letras
        kernel_m = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_m)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_m)

        if options.remove_noise:
            binary = self._remove_small_noise(binary, options.sensitivity)
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
