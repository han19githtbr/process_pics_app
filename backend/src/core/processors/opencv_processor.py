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

    def estimate_median_glyph_height(self, binary: np.ndarray) -> float:
        """
        Faz uma pré-análise rápida de componentes conectados na máscara binária para estimar
        a altura mediana dos possíveis caracteres presentes. Usada apenas como heurística de
        calibração adaptativa (não faz parte do pipeline de 7 passos do PDF) — orienta o
        dimensionamento do fechamento morfológico de reconexão de traços (ver
        `reconnect_broken_strokes`).
        """
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        heights = [
            int(stats[i, cv2.CC_STAT_HEIGHT])
            for i in range(1, num_labels)
            if stats[i, cv2.CC_STAT_AREA] >= 12
        ]
        if not heights:
            return 0.0
        return float(np.median(heights))

    def reconnect_broken_strokes(self, binary: np.ndarray) -> np.ndarray:
        """
        Passo adicional de calibração ("Reconexão de Traços Quebrados"): fecha pequenas
        quebras de 1 a poucos pixels no traço binarizado, causadas por anti-aliasing em
        fontes vazadas/contornadas (outline) ou em traços muito finos.

        Problema físico identificado: em glifos desenhados apenas com contorno (sem
        preenchimento interno), a curvatura acentuada de certos trechos (ex.: bojos de 'P',
        'R', 'S', 'B') faz com que alguns pixels da borda fiquem com intensidade
        intermediária após a suavização bilateral. Como o limiar de Otsu é único e global,
        esses pixels de transição ficam abaixo do limiar em pequenos trechos, quebrando o
        anel de contorno em 2 ou mais fragmentos desconectados — muitos deles pequenos
        demais para passar nos filtros de tamanho/proporção, fazendo a letra "sumir" do
        resultado final.

        Solução adotada — fechamento morfológico adaptativo E BASEADO EM EVIDÊNCIA (não um
        raio fixo aplicado às cegas): a função testa uma sequência crescente de raios de
        fechamento (`cv2.MORPH_CLOSE`, elemento elíptico) e mede, a cada tentativa, quantos
        componentes conectados continuam menores que ~55% da altura típica dos componentes
        maiores da imagem (uma "assinatura" de fragmento de letra quebrada). O menor raio que
        minimiza essa contagem de fragmentos é escolhido. Se a imagem de entrada já não
        apresenta fragmentos (texto já bem formado, mesmo com kerning apertado), nenhum
        fechamento é aplicado — isso evita fundir letras genuinamente vizinhas, que é o risco
        de um fechamento morfológico de raio fixo baseado apenas no tamanho da fonte.
        """
        num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        if num_labels <= 1:
            return binary

        areas = stats[1:, cv2.CC_STAT_AREA]
        heights = stats[1:, cv2.CC_STAT_HEIGHT]
        valid = areas >= 3
        if not np.any(valid):
            return binary

        ref_height = float(np.percentile(heights[valid], 75))
        if ref_height <= 0:
            return binary

        def _fragment_count(mask: np.ndarray) -> int:
            nl, _, st, _ = cv2.connectedComponentsWithStats(mask, 8)
            count = 0
            for i in range(1, nl):
                if st[i, cv2.CC_STAT_AREA] >= 3 and st[i, cv2.CC_STAT_HEIGHT] < 0.55 * ref_height:
                    count += 1
            return count

        baseline_fragments = _fragment_count(binary)
        best_mask = binary
        best_fragments = baseline_fragments

        # Testa raios crescentes; o dimensionamento máximo continua proporcional à altura
        # típica dos glifos, mas só é efetivamente usado se reduzir a contagem de fragmentos.
        max_kernel = max(3, min(15, int(round(ref_height * 0.18))))
        for kernel_size in range(3, max_kernel + 1, 2):
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
            candidate = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            fragments = _fragment_count(candidate)
            if fragments < best_fragments:
                best_fragments = fragments
                best_mask = candidate

        return best_mask

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
            binary = self.reconnect_broken_strokes(binary)
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

        # Refinamento morfológico suave para consolidação dos traços das letras (apenas fechamento para preservar hastes finas)
        kernel_m = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_m)

        # Reconexão adaptativa de traços quebrados (fontes vazadas/contornadas, ver docstring)
        binary = self.reconnect_broken_strokes(binary)

        if options.remove_noise:
            binary = self._remove_small_noise(binary, options.sensitivity)
        return binary
    
    def resize_if_needed(self, image: np.ndarray, max_size: int = 1800) -> Tuple[np.ndarray, float]:
        """Redimensiona imagem se necessário."""
        return ImageUtils.resize_if_needed(image, max_size)

    def auto_upscale_small_text(
        self,
        image: np.ndarray,
        target_height: float = 46.0,
        max_factor: float = 4.0,
        max_dimension: int = 3600,
    ) -> Tuple[np.ndarray, float]:
        """
        Amplia a imagem quando os caracteres detectados são pequenos demais para que a
        binarização binária mantenha um espaço de pelo menos 1-2px entre letras vizinhas.

        Problema físico identificado: em textos com corpo tipográfico pequeno (altura de
        caractere abaixo de ~25px), o anti-aliasing do próprio texto faz com que os traços de
        letras adjacentes se toquem após a binarização — o componente conectado resultante
        passa a ser a palavra inteira (ou vários caracteres colados), e não uma letra
        isolada. Ampliar a imagem antes da binarização (interpolação bicúbica) recria pixels
        de transição adicionais entre as letras, restaurando um "vale" de separação que o
        perfil de projeção vertical (`_split_wide_component`) consegue detectar.

        A estimativa de altura de caractere usa uma binarização auxiliar simples (Otsu, sem
        os demais passos do pipeline) apenas para a decisão de escala — não é a máscara
        binária final usada na segmentação.
        """
        gray = self.to_grayscale(image)
        _, quick_binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if self.detect_dark_background(gray):
            pass  # já é o polo correto: pixels claros (texto) tendem a virar 255
        else:
            quick_binary = cv2.bitwise_not(quick_binary)

        median_h = self.estimate_median_glyph_height(quick_binary)
        if median_h <= 0 or median_h >= target_height:
            return image, 1.0

        factor = min(max_factor, target_height / median_h)
        h, w = image.shape[:2]
        if factor <= 1.05:
            return image, 1.0

        # Respeita um teto de dimensão absoluta para não explodir o tempo de processamento
        largest_side = max(h, w)
        if largest_side * factor > max_dimension:
            factor = max(1.0, max_dimension / largest_side)
        if factor <= 1.05:
            return image, 1.0

        new_size = (int(round(w * factor)), int(round(h * factor)))
        upscaled = cv2.resize(image, new_size, interpolation=cv2.INTER_CUBIC)
        return upscaled, float(factor)
    
    def binarize(self, image: np.ndarray, method: str = 'auto') -> np.ndarray:
        """Binariza a imagem."""
        return self.preprocess(image)
    
    def _remove_small_noise(self, binary: np.ndarray, sensitivity: float = 0.44) -> np.ndarray:
        """Remove pequenos ruídos da imagem binária, preservando letras pequenas em textos densos."""
        height, width = binary.shape
        total_area = height * width
        
        # Limiar adaptativo seguro: não escala desproporcionalmente com a resolução da imagem,
        # evitando apagar letras pequenas, acentos e caracteres finos em textos densos.
        if sensitivity > 0.60:
            area_threshold = 3
        elif sensitivity >= 0.40:
            area_threshold = max(3, min(8, int(total_area * 0.000015)))
        else:
            area_threshold = max(4, min(14, int(total_area * 0.00003)))
        
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, 8)
        clean = np.zeros_like(binary)
        
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area >= area_threshold:
                clean[labels == i] = 255
        
        return clean
