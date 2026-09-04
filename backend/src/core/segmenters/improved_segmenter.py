import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
import time
from difflib import SequenceMatcher
from ..interfaces.letter_segmenter import ILetterSegmenter
from ..interfaces.letter_validator import ILetterValidator
from ..models.processing_options import ProcessingOptions
from ..models.segment_result import SegmentResult
from ..models.letter_box import LetterBox
from ..processors.opencv_processor import OpenCVProcessor
from ..validators.letter_validator import LetterValidator
from ..utils.image_utils import ImageUtils
from ..utils.geometry_utils import GeometryUtils

class ImprovedSegmenter(ILetterSegmenter):
    """Segmentador de letras melhorado."""
    
    def __init__(self, options: Optional[ProcessingOptions] = None):
        self.options = options or ProcessingOptions()
        self.processor = OpenCVProcessor()
        self.validator = LetterValidator()
    
    def set_options(self, options: ProcessingOptions) -> None:
        """Define opções de processamento."""
        self.options = options
    
    def segment(self, image: np.ndarray, options: Optional[ProcessingOptions] = None) -> SegmentResult:
        """
        Executa os passos do trabalho em PDF e extrai as letras com alta precisão:
        1. Imagem Load (RGB)
        2. Conversão para Tons de Cinza (Y <- 0.299*R + 0.587*G + 0.114*B)
        3. Suavização (Filtro Bilateral preservando bordas)
        4. Binarização (Método de Otsu + bitwise_not)
        5. Detecção de Bordas (Algoritmo de Canny com limiares 70 e 150)
        6. Identificação dos Contornos (findContours RETR_EXTERNAL, CHAIN_APPROX_SIMPLE)
        7. Bounding Rectangles e Recorte das Letras
        """
        start_time = time.time()

        if options:
            self.set_options(options)

        # Passo 1: Imagem Load & Redimensionamento
        processed, scale = self.processor.resize_if_needed(image, self.options.max_image_size)

        # Passo 2: Conversão em Tons de Cinza
        gray = self.processor.to_grayscale(processed)

        # Passo 3: Suavização por Filtro Bilateral
        bilateral = self.processor.smooth_bilateral(
            gray,
            d=self.options.bilateral_d,
            sigma_color=self.options.bilateral_sigma_color,
            sigma_space=self.options.bilateral_sigma_space,
        )

        # Passo 4: Binarização (Método de Otsu com inversão)
        binary_otsu, otsu_thresh = self.processor.binarize_otsu(bilateral)

        # Seleciona máscara binária de acordo com o modo
        is_academic_mode = getattr(self.options, 'mode', 'enhanced') == 'academic'
        if is_academic_mode:
            binary = binary_otsu
            if self.options.remove_noise:
                binary = self.processor._remove_small_noise(binary, self.options.sensitivity)
        else:
            binary = self.processor.preprocess(processed, self.options)

        # Passo 5: Detecção de Bordas (Canny)
        edges = self.processor.detect_edges(
            binary,
            low_threshold=self.options.canny_low,
            high_threshold=self.options.canny_high,
        )

        # Passo 6: Contornos e Bounding Boxes
        contours, hierarchy = self.processor.find_contours(edges)
        contours_vis = processed.copy()
        cv2.drawContours(contours_vis, contours, -1, (0, 220, 110), 1)

        # Detecção de componentes e desmembramento de letras coladas
        components = self._detect_components(binary, edges)
        splits_count = sum(1 for c in components if c.get('was_split'))

        # Filtragem de elementos não-letras (linhas, molduras, ruídos sólidos e fundos)
        filtered = self._filter_components(components, binary, processed)
        filtered_count = len(components) - len(filtered)

        # Agrupamento por linhas
        lines = self._group_by_lines(filtered)

        # Segmentação e criação das LetterBox por linha
        all_letters: List[LetterBox] = []
        for line_idx, line in enumerate(lines):
            line_letters = self._segment_line(line, binary, line_idx + 1, processed)
            all_letters.extend(line_letters)

        # Ordenação por palavra preservando ordem natural de leitura
        ordered_letters = self._sort_letters_by_word(all_letters)

        # Validação morfológica final
        validated = self.validator.validate(ordered_letters, binary, processed)

        # Recorte matricial individual de cada letra: curt = target_img[y:y+h, x:x+w]
        self._attach_letter_images(processed, validated)

        # Overlay de depuração
        debug_image = self._create_debug_overlay(processed, validated)
        debug_data_url = ImageUtils.encode_to_data_url(debug_image)

        # Montagem dos 7 passos teóricos do PDF para visualização no frontend
        pipeline_steps = self._build_pipeline_steps(
            processed=processed,
            gray=gray,
            bilateral=bilateral,
            binary_otsu=binary_otsu,
            edges=edges,
            contours_vis=contours_vis,
            debug_image=debug_image,
            validated=validated,
            otsu_thresh=otsu_thresh,
        )

        processing_time = time.time() - start_time
        transcript = self._build_transcript(validated)
        conf_breakdown = self._calculate_confidence_breakdown(validated, processed)

        return SegmentResult(
            letters=validated,
            debug_image=debug_data_url,
            steps=pipeline_steps,
            metadata={
                'width': image.shape[1],
                'height': image.shape[0],
                'total_letters': len(validated),
                'processing_time': processing_time,
                'confidence_score': conf_breakdown['overall'],
                'confidence_breakdown': conf_breakdown,
                'scale': scale,
                'edge_pixels': int(cv2.countNonZero(edges)),
                'splits_count': splits_count,
                'filtered_count': filtered_count,
                'warnings': self._build_quality_warnings(
                    validated, components, splits_count, filtered_count, conf_breakdown
                ),
                'transcript': transcript,
                'mode': getattr(self.options, 'mode', 'enhanced'),
            },
            transcript=transcript,
        )

    def _build_pipeline_steps(
        self,
        processed: np.ndarray,
        gray: np.ndarray,
        bilateral: np.ndarray,
        binary_otsu: np.ndarray,
        edges: np.ndarray,
        contours_vis: np.ndarray,
        debug_image: np.ndarray,
        validated: List[LetterBox],
        otsu_thresh: float,
    ) -> List[Dict[str, Any]]:
        """Gera as imagens e metadados das 7 etapas descritas no documento em PDF."""
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        bilateral_bgr = cv2.cvtColor(bilateral, cv2.COLOR_GRAY2BGR)
        binary_bgr = cv2.cvtColor(binary_otsu, cv2.COLOR_GRAY2BGR)
        edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

        return [
            {
                'step': 1,
                'title': 'Passo 1: Carregamento da Imagem (Imagem Load)',
                'technique': 'OpenCV cv2.imread',
                'formula': 'Matriz NumPy com shape (H, W, 3) e profundidade 24 bits de cor',
                'description': (
                    'Carregamento da imagem em memória utilizando OpenCV. A função monta um array multidimensional '
                    'com a altura, largura e os 3 canais de cores (BGR/RGB).'
                ),
                'image': ImageUtils.encode_to_data_url(processed),
            },
            {
                'step': 2,
                'title': 'Passo 2: Conversão para Tons de Cinza (GrayScale Converter)',
                'technique': 'cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)',
                'formula': 'Y ← 0.299 * R + 0.587 * G + 0.114 * B',
                'description': (
                    'Representa a intensidade de cada pixel em um único valor numérico [0..255] em vez de três. '
                    'Permite medir com precisão quão claro ou escuro está cada ponto da imagem.'
                ),
                'image': ImageUtils.encode_to_data_url(gray_bgr),
            },
            {
                'step': 3,
                'title': 'Passo 3: Suavização da Imagem (Filtro Bilateral)',
                'technique': f'cv2.bilateralFilter(gray, d={self.options.bilateral_d}, sigmaColor={self.options.bilateral_sigma_color}, sigmaSpace={self.options.bilateral_sigma_space})',
                'formula': 'Filtro bilateral não-linear que combina proximidade espacial e similaridade radiométrica',
                'description': (
                    'Suavização aplicada para atenuar ruídos de alta frequência preservando com fidelidade as bordas '
                    'das letras, pois a detecção nítida de bordas é essencial para o recorte.'
                ),
                'image': ImageUtils.encode_to_data_url(bilateral_bgr),
            },
            {
                'step': 4,
                'title': 'Passo 4: Binarização (Método de Otsu + Inversão)',
                'technique': f'Limiar estatístico ótimo de Otsu (T ≈ {int(otsu_thresh)}) + cv2.bitwise_not',
                'formula': 'bin[bin > T] = 255; bin[bin < 255] = 0; return bitwise_not(bin)',
                'description': (
                    'Converte a imagem em escala de cinza para preto e branco absoluto. No ponto (x,y) onde a intensidade '
                    'supera o limiar ótimo de Otsu aplica-se 255. A inversão bitwise_not torna as arestas das letras '
                    'visíveis e prontas para contorno.'
                ),
                'image': ImageUtils.encode_to_data_url(binary_bgr),
            },
            {
                'step': 5,
                'title': 'Passo 5: Detecção de Bordas (Algoritmo de Canny)',
                'technique': f'cv2.Canny(bin, min={self.options.canny_low}, max={self.options.canny_high})',
                'formula': 'Derivadas de Sobel Gx e Gy + Supressão de Não-Máximos + Histerese',
                'description': (
                    'O algoritmo de Canny calcula a primeira derivada horizontal (Gy) e vertical (Gx) e aplica quatro filtros '
                    'direcionais para localizar com exatidão as arestas ao longo de todas as bordas dos caracteres.'
                ),
                'image': ImageUtils.encode_to_data_url(edges_bgr),
            },
            {
                'step': 6,
                'title': 'Passo 6: Identificação de Contornos e Bounding Rects',
                'technique': 'cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)',
                'formula': 'Agrupamento de pontos vizinhos de mesma intensidade com compressão de redundâncias',
                'description': (
                    'Rastreamento de todas as curvas de contorno externas. O parâmetro CHAIN_APPROX_SIMPLE comprime os '
                    'segmentos redundantes economizando memória e preparando os pontos para o cálculo dos Bounding Boxes.'
                ),
                'image': ImageUtils.encode_to_data_url(contours_vis),
            },
            {
                'step': 7,
                'title': 'Passo 7: Bounding Rects & Recorte Individual',
                'technique': 'x, y, w, h = cv2.boundingRect(c); curt = target_img[y:y+h, x:x+w]',
                'formula': 'Recorte matricial indexado por coordenadas [y : y + h, x : x + w]',
                'description': (
                    f'Cálculo do retângulo envolvente para cada letra individual detectada ({len(validated)} letras encontradas). '
                    'Cada letra é extraída como um array matricial independente e disposta na ordem natural de leitura.'
                ),
                'image': ImageUtils.encode_to_data_url(debug_image),
            },
        ]
    
    def _detect_components(self, binary: np.ndarray, edges: Optional[np.ndarray] = None) -> List[Dict]:
        """Detecta componentes conectados, associa diacríticos/pingos e separa letras agrupadas."""
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, 8)
        
        raw_components: List[Dict] = []

        for i in range(1, num_labels):
            comp = {
                'label': i,
                'area': stats[i, cv2.CC_STAT_AREA],
                'x': stats[i, cv2.CC_STAT_LEFT],
                'y': stats[i, cv2.CC_STAT_TOP],
                'width': stats[i, cv2.CC_STAT_WIDTH],
                'height': stats[i, cv2.CC_STAT_HEIGHT],
                'centroid': (centroids[i][0], centroids[i][1]),
            }

            if edges is not None:
                crop = edges[
                    comp['y']:comp['y'] + comp['height'],
                    comp['x']:comp['x'] + comp['width'],
                ]
                contours, _ = cv2.findContours(crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                comp['contour_count'] = len(contours)

            raw_components.append(comp)

        # Fusão inteligente de acentos e pingos (i, j, acentos, pontuações compostas)
        merged_components = self._merge_diacritics(raw_components)

        # Separa letras coladas/agrupadas se a opção estiver ativada
        components: List[Dict] = []
        for comp in merged_components:
            split_result = self._split_wide_component(comp, binary)
            components.extend(split_result)

        return components

    def _merge_diacritics(self, components: List[Dict]) -> List[Dict]:
        """
        Funde acentos, pingos (i, j) e marcas flutuantes com o caractere principal.
        Evita que pingos e acentos fiquem isolados ou sejam descartados como ruído.
        """
        if not components:
            return []

        min_size = max(3, int(self.options.min_letter_size))
        bases = [c for c in components if c['height'] >= max(7, min_size * 2) and c['area'] >= 20]
        smalls = [c for c in components if c not in bases]

        if not smalls or not bases:
            return components

        merged = []
        used_smalls = set()

        for b in bases:
            bx, by, bw, bh = b['x'], b['y'], b['width'], b['height']
            bx2, by2 = bx + bw, by + bh
            b_area = b['area']

            for s in smalls:
                if id(s) in used_smalls:
                    continue
                sx, sy, sw, sh = s['x'], s['y'], s['width'], s['height']
                sx2, sy2 = sx + sw, sy + sh

                overlap = min(bx2, sx2) - max(bx, sx)
                if overlap >= -2:
                    # Caso 1: Acento ou pingo acima (i, j, á, é, ã, !)
                    if sy < by and (by - sy2) <= max(bh * 0.85, 18):
                        bx = min(bx, sx)
                        by = min(by, sy)
                        bx2 = max(bx2, sx2)
                        by2 = max(by2, sy2)
                        b_area += s['area']
                        used_smalls.add(id(s))
                    # Caso 2: Pingo de pontuação ou cedilha abaixo (ç, ?, !)
                    elif sy >= by2 and (sy - by2) <= max(bh * 0.55, 12):
                        bx = min(bx, sx)
                        by = min(by, sy)
                        bx2 = max(bx2, sx2)
                        by2 = max(by2, sy2)
                        b_area += s['area']
                        used_smalls.add(id(s))

            merged_comp = dict(b)
            merged_comp.update({
                'x': bx,
                'y': by,
                'width': bx2 - bx,
                'height': by2 - by,
                'area': b_area,
                'centroid': (bx + (bx2 - bx) / 2.0, by + (by2 - by) / 2.0),
            })
            merged.append(merged_comp)

        for s in smalls:
            if id(s) not in used_smalls and s['area'] >= 8 and s['width'] >= min_size:
                merged.append(s)

        return merged

    def _is_single_wide_glyph(self, crop: np.ndarray) -> bool:
        """
        Verifica se um componente largo corresponde a uma única letra nativamente larga ('m', 'w', 'M', 'W'),
        evitando que seja indevidamente fatiada em múltiplos fragmentos.
        """
        h, w = crop.shape[:2]
        if h < 8 or w < 8:
            return False
        aspect = w / max(h, 1)
        if not (1.05 <= aspect <= 1.85):
            return False

        proj = np.count_nonzero(crop, axis=0).astype(float)
        k = max(3, int(w * 0.08))
        if k % 2 == 0:
            k += 1
        smooth = np.convolve(proj, np.ones(k) / k, mode='same')
        max_val = np.max(smooth)
        if max_val == 0:
            return False

        peaks = []
        for i in range(1, w - 1):
            if smooth[i] >= smooth[i - 1] and smooth[i] >= smooth[i + 1] and smooth[i] > max_val * 0.50:
                if not peaks or (i - peaks[-1]) >= max(3, int(w * 0.18)):
                    peaks.append(i)

        # Assinatura de 'm'/'M': 3 hastes verticais distribuídas
        if len(peaks) == 3:
            p1, p2, p3 = peaks
            if p1 <= 0.35 * w and 0.35 * w <= p2 <= 0.65 * w and p3 >= 0.65 * w:
                return True

        # Assinatura de 'w'/'W': 2 picos largos externos com vértice intermediário
        if len(peaks) == 2:
            p1, p2 = peaks
            if p1 <= 0.40 * w and p2 >= 0.60 * w and aspect <= 1.45:
                return True

        return False

    def _split_wide_component(self, component: Dict, binary: np.ndarray) -> List[Dict]:
        """
        Separa grupos de letras coladas/agrupadas usando análise de projeção vertical.
        Identifica vales de menor densidade de tinta entre caracteres vizinhos, preservando 'm' e 'w'.
        """
        if not getattr(self.options, 'split_grouped_letters', True):
            return [component]

        width = component['width']
        height = component['height']
        min_size = max(3, int(self.options.min_letter_size))

        if width < max(2 * min_size, int(height * 1.15)):
            return [component]

        crop = binary[component['y']:component['y'] + height, component['x']:component['x'] + width]
        if crop.size == 0:
            return [component]

        # Se for uma única letra nativamente larga ('m', 'w', 'M', 'W'), não dividir!
        if self._is_single_wide_glyph(crop):
            return [component]

        # Perfil de projeção vertical de pixels de tinta
        projection = np.count_nonzero(crop, axis=0).astype(float)
        min_char_w = max(min_size, int(height * 0.18))
        if len(projection) < 2 * min_char_w:
            return [component]

        # Suavização com média móvel para evitar ruídos de 1 pixel
        kernel_size = 3
        kernel = np.ones(kernel_size) / kernel_size
        smooth_proj = np.convolve(projection, kernel, mode='same')

        max_val = np.max(smooth_proj)
        if max_val == 0:
            return [component]

        # Busca vales locais significativos entre picos de caracteres
        valley_threshold = max(1.0, max_val * 0.42)
        cuts = []

        for i in range(min_char_w, width - min_char_w):
            if (smooth_proj[i] <= valley_threshold and
                smooth_proj[i] <= smooth_proj[i - 1] and
                smooth_proj[i] <= smooth_proj[i + 1]):
                
                if not cuts or (i - cuts[-1]) >= min_char_w:
                    cuts.append(i)

        # Fallback: Se for muito largo (largura >= 1.6 * altura) e não encontrou vales estritos,
        # procura o mínimo global na região intermediária
        if not cuts and width >= int(height * 1.6):
            mid_start = min_char_w
            mid_end = width - min_char_w
            if mid_end > mid_start:
                min_idx = mid_start + int(np.argmin(smooth_proj[mid_start:mid_end]))
                if smooth_proj[min_idx] < max_val * 0.70:
                    cuts.append(min_idx)

        if not cuts:
            return [component]

        # Monta os intervalos de divisão
        intervals = []
        curr_start = 0
        for cut in cuts:
            if cut - curr_start >= min_char_w:
                intervals.append((curr_start, cut))
                curr_start = cut
        if width - curr_start >= min_char_w:
            intervals.append((curr_start, width))

        if len(intervals) < 2:
            return [component]

        split_comps = []
        for start_x, end_x in intervals:
            part = crop[:, start_x:end_x]
            part_pts = np.argwhere(part > 0)
            if len(part_pts) < max(12, min_size * min_size):
                continue

            # Recalcula o bounding box justo em torno dos pixels reais da letra individual
            py_min, px_min = part_pts.min(axis=0)
            py_max, px_max = part_pts.max(axis=0)

            sub_x = component['x'] + start_x + int(px_min)
            sub_y = component['y'] + int(py_min)
            sub_w = int(px_max - px_min + 1)
            sub_h = int(py_max - py_min + 1)
            sub_area = int(len(part_pts))

            split_comps.append({
                'label': component.get('label', 1),
                'x': sub_x,
                'y': sub_y,
                'width': sub_w,
                'height': sub_h,
                'area': sub_area,
                'centroid': (sub_x + sub_w / 2.0, sub_y + sub_h / 2.0),
                'was_split': True,
            })

        return split_comps or [component]

    def _filter_components(self, components: List[Dict], binary: np.ndarray,
                           raw_image: Optional[np.ndarray] = None) -> List[Dict]:
        """
        Filtra componentes que não são letras:
        - Rejeita linhas horizontais (sublinhados, barras)
        - Rejeita linhas verticais (molduras laterais, divisórias)
        - Rejeita blocos sólidos geométricos (sem vazados ou traços típicos de letras)
        - Rejeita molduras de página e toques nos limites externos da imagem
        - Rejeita molduras vazadas e cantos decorativos geométricos (teste de preenchimento central)
        - Rejeita recortes lisos de fundo / papel sem contraste ou desvio padrão suficiente
        - Rejeita poeiras esparsas e ruídos de iluminação
        """
        total_area = binary.shape[0] * binary.shape[1]
        img_h, img_w = binary.shape[:2]
        sensitivity = max(0.1, min(0.8, float(self.options.sensitivity)))
        min_size = max(3, int(self.options.min_letter_size))
        if sensitivity >= 0.55:
            min_size = max(3, min_size - 1)
        max_size = max(self.options.max_letter_size, min_size)

        filter_non_letters = getattr(self.options, 'filter_non_letters', True)
        filter_bg_noise = getattr(self.options, 'filter_background_noise', True)

        gray_img = None
        if raw_image is not None and raw_image.size > 0:
            gray_img = cv2.cvtColor(raw_image, cv2.COLOR_BGR2GRAY) if raw_image.ndim == 3 else raw_image

        filtered: List[Dict] = []

        for comp in components:
            w = comp['width']
            h = comp['height']
            x = comp['x']
            y = comp['y']
            area = comp['area']
            bbox_area = max(w * h, 1)
            area_ratio = area / max(total_area, 1)
            aspect_ratio = w / max(h, 1)
            density = area / bbox_area

            # 1. Rejeição de molduras gigantes que englobam a página
            if area_ratio > 0.20:
                continue

            if filter_non_letters:
                # 2. Rejeição de toques nas bordas extremas da imagem (molduras, vinhetas, cantos de recorte)
                touches_border = (x <= 1 or y <= 1 or x + w >= img_w - 1 or y + h >= img_h - 1)
                if touches_border:
                    continue

                # 3. Rejeição de linhas horizontais (sublinhados, réguas)
                if aspect_ratio > 3.8 or (aspect_ratio > 2.5 and h <= 6):
                    continue

                # 4. Rejeição de linhas verticais (molduras laterais, divisórias longas de página)
                # Letras finas como 'l', 'I', '1' podem ter h/w até 10-12 em fontes grandes (h ~ 100px),
                # mas não ultrapassam uma fração substancial da altura total da imagem.
                is_vertical_line = (
                    (h / max(w, 1)) > 20.0 or
                    ((h / max(w, 1)) > 12.0 and h > max(120, int(img_h * 0.20))) or
                    ((h / max(w, 1)) > 6.0 and h > max(180, int(img_h * 0.30))) or
                    (w <= 2 and h > 40)
                )
                if is_vertical_line:
                    continue

                # 5. Rejeição de blocos sólidos geométricos (quadrados/retângulos compactos, preservando caracteres monolineares como 'l', 'I', '1')
                if density > 0.95 and area > 140 and min(w, h) > 10 and (0.25 <= aspect_ratio <= 3.5):
                    continue

                # 6. Rejeição de poeiras hiper-esparsas
                if density < 0.08:
                    continue

                # 7. Rejeição de molduras vazadas e cantos geométricos (L-shapes / caixas vazadas)
                if w >= 25 and h >= 25:
                    crop_bin = binary[y:y+h, x:x+w]
                    if crop_bin.size > 0:
                        cy, cx = crop_bin.shape
                        mid = crop_bin[int(cy * 0.25):int(cy * 0.75), int(cx * 0.25):int(cx * 0.75)]
                        c_fill = float(np.mean(mid > 0)) if mid.size > 0 else 0
                        if c_fill < 0.04 and (w > 35 or h > 35):
                            continue

            # 8. Filtro avançado contra ruídos de fundos coloridos, desenhos e artefatos de papel
            if filter_bg_noise and gray_img is not None:
                pad = 3
                x0 = max(0, x - pad)
                y0 = max(0, y - pad)
                x1 = min(img_w, x + w + pad)
                y1 = min(img_h, y + h + pad)
                crop_g = gray_img[y0:y1, x0:x1]
                if crop_g.size > 0:
                    std_val = float(np.std(crop_g))
                    dyn_range = float(np.max(crop_g) - np.min(crop_g))
                    # Descarta recortes quase lisos (fundo homogêneo recortado como letra)
                    if std_val < 16.0 or dyn_range < 35.0:
                        continue

            # Limite mínimo de área adaptativo:
            # Rejeita ruídos e poeiras irregulares (área < 16), preservando caracteres compactos (área >= 20).
            min_component_area = max(16, min_size * min_size)

            is_valid = (
                area >= min_component_area and
                area_ratio >= (2.0 / max(total_area, 1)) and
                w >= min_size and
                h >= min_size and
                w <= max_size and
                h <= max_size and
                aspect_ratio >= 0.04 and
                aspect_ratio <= 3.8 and
                density >= 0.06 and
                (density <= 0.98 or min(w, h) <= 12)
            )

            if is_valid:
                filtered.append(comp)

        return filtered
    
    def _group_by_lines(self, components: List[Dict]) -> List[List[Dict]]:
        """Agrupa componentes por linha usando centro vertical robusto e ordenação espacial."""
        if not components:
            return []

        sorted_comps = sorted(components, key=lambda c: (c['y'] + c['height'] / 2.0, c['x']))
        lines: List[List[Dict]] = []

        for comp in sorted_comps:
            cy = comp['y'] + comp['height'] / 2.0
            best_line = None
            best_dist = float('inf')

            for line in lines:
                line_med_cy = float(np.median([c['y'] + c['height'] / 2.0 for c in line]))
                line_med_h = float(np.median([c['height'] for c in line]))
                dist = abs(cy - line_med_cy)
                if dist <= line_med_h * 0.65:
                    if dist < best_dist:
                        best_dist = dist
                        best_line = line

            if best_line is not None:
                best_line.append(comp)
            else:
                lines.append([comp])

        lines.sort(key=lambda line: float(np.median([c['y'] for c in line])))
        return [sorted(line, key=lambda c: c['x']) for line in lines]
    
    def _segment_line(self, line: List[Dict], binary: np.ndarray, line_number: int,
                      raw_image: Optional[np.ndarray] = None) -> List[LetterBox]:
        """Segmenta letras em uma linha."""
        if not line:
            return []

        letter_boxes: List[LetterBox] = []
        padding = self.options.padding

        for comp in line:
            x, y, width, height = GeometryUtils.expand_rect(
                comp['x'], comp['y'], comp['width'], comp['height'],
                padding, binary.shape[1], binary.shape[0]
            )

            if width >= self.options.min_letter_size and height >= self.options.min_letter_size:
                confidence = self.validator.calculate_confidence(
                    LetterBox(
                        x=x, y=y, width=width, height=height,
                        area=comp['area'], confidence=0.9
                    ),
                    binary,
                    raw_image
                )

                letter_boxes.append(LetterBox(
                    x=x, y=y, width=width, height=height,
                    area=comp['area'],
                    confidence=confidence,
                    line=line_number
                ))

        return letter_boxes

    def _group_letters_by_words(self, letters: List[LetterBox]) -> List[List[LetterBox]]:
        """Agrupa componentes por palavra usando espaçamento horizontal e linha."""
        if not letters:
            return []

        sorted_letters = sorted(letters, key=lambda box: (box.line or 1, box.x, box.y))
        words: List[List[LetterBox]] = []
        current_word: List[LetterBox] = []

        for letter in sorted_letters:
            if not current_word:
                current_word = [letter]
                continue

            previous = current_word[-1]
            gap = letter.x - (previous.x + previous.width)
            same_line = (letter.line or previous.line or 1) == (previous.line or 1)
            word_gap_threshold = max(18, previous.width * 5)

            if same_line and gap <= word_gap_threshold:
                current_word.append(letter)
            else:
                words.append(current_word)
                current_word = [letter]

        if current_word:
            words.append(current_word)

        return words

    def _sort_letters_by_word(self, letters: List[LetterBox]) -> List[LetterBox]:
        """Ordena as letras por linha e por palavra, preservando a ordem real da leitura."""
        grouped_words = self._group_letters_by_words(letters)
        ordered: List[LetterBox] = []

        for word in grouped_words:
            ordered.extend(sorted(word, key=lambda box: box.x))

        if not ordered:
            return sorted(letters, key=lambda box: (box.line or 1, box.x, box.y))

        return ordered

    def _build_transcript(self, letters: List[LetterBox]) -> str:
        """Gera a sequência em ordem de leitura, respeitando a ordem do texto original sem placeholders artificiais."""
        if not letters:
            return ''

        ordered = self._sort_letters_by_word(letters)
        return ' '.join(
            str(letter.id if letter.id is not None else index + 1)
            for index, letter in enumerate(ordered)
        )

    def compare_images(self, source_image: np.ndarray, target_image: np.ndarray,
                       options: Optional[ProcessingOptions] = None) -> Dict[str, any]:
        """Compara duas imagens de texto para detectar similaridade e plágio."""
        source_result = self.segment(source_image, options)
        target_result = self.segment(target_image, options)

        source_transcript = self._build_transcript(source_result.letters)
        target_transcript = self._build_transcript(target_result.letters)

        similarity = SequenceMatcher(None, source_transcript, target_transcript).ratio()

        if source_result.letters and target_result.letters:
            letter_count_ratio = min(
                len(source_result.letters), len(target_result.letters)
            ) / max(len(source_result.letters), len(target_result.letters))
            similarity = max(similarity, letter_count_ratio)

        if similarity >= 0.90:
            status = 'plagio_detectado'
            verdict = 'A imagem de comparação tem conteúdo altamente semelhante ao original.'
        elif similarity < 0.70:
            status = 'imagem_aceita'
            verdict = 'As imagens possuem conteúdo muito diferente e podem ser aceitas.'
        else:
            status = 'semelhanca_parcial'
            verdict = 'As imagens possuem semelhança parcial e exigem revisão manual.'

        return {
            'source_letters': len(source_result.letters),
            'target_letters': len(target_result.letters),
            'similarity': round(float(similarity), 4),
            'status': status,
            'verdict': verdict,
            'threshold': {
                'plagio': 0.90,
                'aceita': 0.70
            },
            'source_transcript': source_transcript,
            'target_transcript': target_transcript,
        }
    
    def _attach_letter_images(self, image: np.ndarray, letters: List[LetterBox]) -> None:
        """Recorta a região de cada letra na imagem e anexa como data URL."""
        height, width = image.shape[:2]

        for letter in letters:
            x0 = max(0, letter.x)
            y0 = max(0, letter.y)
            x1 = min(width, letter.x + letter.width)
            y1 = min(height, letter.y + letter.height)

            if x1 <= x0 or y1 <= y0:
                continue

            crop = image[y0:y1, x0:x1]
            letter.image = ImageUtils.encode_to_data_url(crop)

    def _create_debug_overlay(self, image: np.ndarray, letters: List[LetterBox]) -> np.ndarray:
        """Cria overlay de debug com caixas delimitadoras."""
        overlay = image.copy()
        
        for letter in letters:
            cv2.rectangle(
                overlay,
                (letter.x, letter.y),
                (letter.x + letter.width, letter.y + letter.height),
                (46, 204, 113),
                2
            )
        
        return overlay
    
    def _calculate_overall_confidence(self, letters: List[LetterBox]) -> float:
        """Calcula confiança geral da segmentação."""
        if not letters:
            return 0.0
        return sum(l.confidence for l in letters) / len(letters)

    def _calculate_confidence_breakdown(
        self,
        letters: List[LetterBox],
        image: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Calcula a porcentagem de confiabilidade da segmentação e seu detalhamento de forma
        100% transparente em relação aos caracteres e métricas obtidas na imagem.
        Avalia 4 pilares:
        1. Morfologia Tipográfica (Aspect Ratio médio) - peso 35%
        2. Contraste e Nitidez de Tinta (Desvio padrão e amplitude dinâmica) - peso 30%
        3. Coerência e Alinhamento de Linha (Razão de altura com a mediana da linha) - peso 20%
        4. Solidez e Densidade de Preenchimento (Área de tinta / Bounding Box) - peso 15%
        """
        if not letters:
            return {
                'overall': 0.0,
                'letter_average': 0.0,
                'aspect_ratio_score': 0.0,
                'contrast_score': 0.0,
                'line_coherence_score': 0.0,
                'density_score': 0.0,
                'weights': {
                    'aspect_ratio': 0.35,
                    'contrast': 0.30,
                    'line_coherence': 0.20,
                    'density': 0.15,
                },
                'evaluated_letters': 0,
                'description': 'Nenhum caractere detectado para cálculo de confiabilidade.',
            }

        total_letters = len(letters)

        # Assegura que cada caractere possua seus detalhes de confiança
        for letter in letters:
            if getattr(letter, 'confidence_details', None) is None:
                if hasattr(self.validator, 'calculate_confidence_details') and image is not None:
                    letter.confidence_details = self.validator.calculate_confidence_details(letter, image)
                else:
                    letter.confidence_details = {
                        'aspect_ratio': letter.confidence,
                        'contrast': letter.confidence,
                        'line_coherence': letter.confidence,
                        'density': letter.confidence,
                        'overall': letter.confidence,
                    }

        avg_ar = sum(float(l.confidence_details.get('aspect_ratio', l.confidence)) for l in letters) / total_letters
        avg_contrast = sum(float(l.confidence_details.get('contrast', l.confidence)) for l in letters) / total_letters
        avg_line = sum(float(l.confidence_details.get('line_coherence', l.confidence)) for l in letters) / total_letters
        avg_density = sum(float(l.confidence_details.get('density', l.confidence)) for l in letters) / total_letters

        # A média ponderada dos 4 pilares globais
        overall = 0.35 * avg_ar + 0.30 * avg_contrast + 0.20 * avg_line + 0.15 * avg_density
        overall = round(float(min(1.0, max(0.0, overall))), 4)
        letter_avg = round(float(sum(l.confidence for l in letters) / total_letters), 4)

        description = (
            f"Confiabilidade geral de {overall * 100:.1f}% obtida pela média ponderada dos 4 pilares em "
            f"{total_letters} caractere(s): Morfologia Tipográfica ({avg_ar * 100:.1f}%), "
            f"Contraste de Tinta ({avg_contrast * 100:.1f}%), Coerência de Linha ({avg_line * 100:.1f}%) "
            f"e Solidez/Densidade ({avg_density * 100:.1f}%)."
        )

        return {
            'overall': overall,
            'letter_average': letter_avg,
            'aspect_ratio_score': round(avg_ar, 4),
            'contrast_score': round(avg_contrast, 4),
            'line_coherence_score': round(avg_line, 4),
            'density_score': round(avg_density, 4),
            'weights': {
                'aspect_ratio': 0.35,
                'contrast': 0.30,
                'line_coherence': 0.20,
                'density': 0.15,
            },
            'evaluated_letters': total_letters,
            'description': description,
        }

    def _build_quality_warnings(
        self,
        letters: List[LetterBox],
        components: List[Dict],
        splits_count: int = 0,
        filtered_count: int = 0,
        conf_breakdown: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Gera explicações transparentes sobre a detecção, imperfeições e limites do método."""
        warnings = []
        if not letters:
            warnings.append('Nenhum caractere com formato compatível foi detectado. Ajuste a sensibilidade ou verifique o contraste da imagem.')

        if splits_count > 0:
            warnings.append(
                f'Separação inteligente ativa: {splits_count} grupo(s) de caracteres colados foram identificados '
                'e desmembrados via análise de perfil de projeção vertical.'
            )

        if filtered_count > 0:
            warnings.append(
                f'Filtro morfológico ativo: {filtered_count} elemento(s) não-textuais (linhas, molduras ou ruídos) '
                'foram descartados para manter a precisão do recorte.'
            )

        if any(letter.aspect_ratio > 2.0 for letter in letters):
            warnings.append(
                'Alguns recortes possuem proporção larga. Letras com kerning muito apertado ou fontes decorativas '
                'podem se fundir na binarização clássica.'
            )

        overall_conf = conf_breakdown.get('overall', 0.0) if conf_breakdown else self._calculate_overall_confidence(letters)
        if letters and overall_conf < 0.75:
            warnings.append(
                f'A pontuação média de confiança é moderada ({overall_conf * 100:.1f}%). '
                'Recomendamos inspecionar os recortes na grade visual para checar eventuais fragmentações.'
            )
        elif letters and conf_breakdown:
            warnings.append(
                f"Transparência de confiabilidade ({overall_conf * 100:.1f}%): "
                f"{conf_breakdown.get('description', '')}"
            )

        warnings.append(
            'Transparência técnica: Conforme documentado no trabalho em PDF (UFRRJ TM438), o método clássico '
            '(Bilateral + Otsu + Canny + Contornos) é mais eficiente em palavras e imagens com letras maiores e contraste nítido.'
        )

        return warnings
