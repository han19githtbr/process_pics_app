import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
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
        """Segmenta letras na imagem."""
        start_time = time.time()
        
        if options:
            self.set_options(options)
        
        # Pré-processamento
        processed, scale = self.processor.resize_if_needed(image, self.options.max_image_size)
        binary = self.processor.preprocess(processed, self.options)
        edges = self.processor.detect_edges(binary)
        
        # Detecção de componentes
        components = self._detect_components(binary, edges)
        
        # Filtragem
        filtered = self._filter_components(components, binary)

        # Agrupamento por linhas
        lines = self._group_by_lines(filtered)
        
        # Segmentação de letras
        all_letters: List[LetterBox] = []
        for line_idx, line in enumerate(lines):
            line_letters = self._segment_line(line, binary, line_idx + 1)
            all_letters.extend(line_letters)

        # Ordenação por palavra antes da validação final
        ordered_letters = self._sort_letters_by_word(all_letters)

        # Validação final
        validated = self.validator.validate(ordered_letters, binary)

        # Recortar a imagem de cada letra individualmente
        self._attach_letter_images(processed, validated)

        # Criar overlay de debug
        debug_image = self._create_debug_overlay(processed, validated)
        debug_data_url = ImageUtils.encode_to_data_url(debug_image)
        
        processing_time = time.time() - start_time
        transcript = self._build_transcript(validated)
        
        return SegmentResult(
            letters=validated,
            debug_image=debug_data_url,
            metadata={
                'width': image.shape[1],
                'height': image.shape[0],
                'total_letters': len(validated),
                'processing_time': processing_time,
                'confidence_score': self._calculate_overall_confidence(validated),
                'scale': scale,
                'edge_pixels': int(cv2.countNonZero(edges)),
                'warnings': self._build_quality_warnings(validated, components),
                'transcript': transcript
            },
            transcript=transcript
        )
    
    def _detect_components(self, binary: np.ndarray, edges: Optional[np.ndarray] = None) -> List[Dict]:
        """Detecta componentes e usa contornos Canny como evidência de borda."""
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, 8)
        
        components = []
        for i in range(1, num_labels):
            component = {
                'label': i,
                'area': stats[i, cv2.CC_STAT_AREA],
                'x': stats[i, cv2.CC_STAT_LEFT],
                'y': stats[i, cv2.CC_STAT_TOP],
                'width': stats[i, cv2.CC_STAT_WIDTH],
                'height': stats[i, cv2.CC_STAT_HEIGHT],
                'centroid': (centroids[i][0], centroids[i][1])
            }
            if edges is not None:
                crop = edges[
                    component['y']:component['y'] + component['height'],
                    component['x']:component['x'] + component['width']
                ]
                contours, _ = cv2.findContours(crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                component['contour_count'] = len(contours)
                component['contour_area'] = max((cv2.contourArea(contour) for contour in contours), default=0.0)
            components.extend(self._split_wide_component(component, binary))
        
        return components

    def _split_wide_component(self, component: Dict, binary: np.ndarray) -> List[Dict]:
        """Divide componentes largos em vales verticais claros, sem forçar cortes ambíguos."""
        width = component['width']
        height = component['height']
        min_size = max(3, int(self.options.min_letter_size))
        if width < max(2 * min_size, int(height * 1.8)):
            return [component]

        crop = binary[component['y']:component['y'] + height, component['x']:component['x'] + width]
        projection = np.count_nonzero(crop, axis=0)
        valleys = projection <= max(1, int(projection.max(initial=0) * 0.08))
        cuts = np.flatnonzero(valleys)
        if len(cuts) == 0:
            return [component]

        groups = []
        start = 0
        for cut in cuts:
            if cut - start >= min_size:
                groups.append((start, cut))
                start = cut + 1
        if width - start >= min_size:
            groups.append((start, width))
        if len(groups) < 2:
            return [component]

        split = []
        for start, end in groups:
            part = binary[component['y']:component['y'] + height, component['x'] + start:component['x'] + end]
            area = int(cv2.countNonZero(part))
            if area < max(24, min_size * min_size):
                continue
            split.append({
                **component,
                'x': component['x'] + start,
                'width': end - start,
                'area': area,
                'centroid': (component['x'] + start + (end - start) / 2, component['centroid'][1]),
            })
        return split or [component]
    
    def _filter_components(self, components: List[Dict], binary: np.ndarray) -> List[Dict]:
        """Filtra componentes que não são letras, rejeitando ruído esparso e fragmentos sem densidade real."""
        total_area = binary.shape[0] * binary.shape[1]
        sensitivity = max(0.1, min(0.8, float(self.options.sensitivity)))
        min_size = max(3, int(self.options.min_letter_size))
        if sensitivity >= 0.55:
            min_size = max(3, min_size - 1)
        max_size = max(self.options.max_letter_size, min_size)
        min_area_ratio = max(0.00018, 2.8 / max(total_area, 1))
        if sensitivity <= 0.35:
            min_area_ratio *= 1.2
        max_area_ratio = 0.30

        filtered = []
        for comp in components:
            area_ratio = comp['area'] / max(total_area, 1)
            aspect_ratio = comp['width'] / max(comp['height'], 1)
            density = comp['area'] / max(comp['width'] * comp['height'], 1)
            min_component_area = max(24, min_size * min_size)

            is_valid = (
                comp['area'] >= min_component_area and
                area_ratio >= min_area_ratio and
                area_ratio <= max_area_ratio and
                density >= 0.18 and
                aspect_ratio >= 0.12 and
                aspect_ratio <= 4.2 and
                comp['width'] >= min_size and
                comp['height'] >= min_size and
                comp['width'] <= max_size and
                comp['height'] <= max_size and
                density <= 0.92
            )

            if is_valid:
                filtered.append(comp)

        return filtered
    
    def _group_by_lines(self, components: List[Dict]) -> List[List[Dict]]:
        """Agrupa componentes por linha."""
        if not components:
            return []
        
        sorted_comps = sorted(components, key=lambda c: c['y'])
        avg_height = np.median([c['height'] for c in sorted_comps])
        line_threshold = avg_height * 0.5
        
        lines = []
        current_line = [sorted_comps[0]]
        
        for comp in sorted_comps[1:]:
            if abs(comp['y'] - current_line[-1]['y']) <= line_threshold:
                current_line.append(comp)
            else:
                lines.append(sorted(current_line, key=lambda c: c['x']))
                current_line = [comp]
        
        if current_line:
            lines.append(sorted(current_line, key=lambda c: c['x']))
        
        return lines
    
    def _segment_line(self, line: List[Dict], binary: np.ndarray, line_number: int) -> List[LetterBox]:
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
                    binary
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

    def _build_quality_warnings(self, letters: List[LetterBox], components: List[Dict]) -> List[str]:
        """Expõe limites conhecidos do método para manter o resultado auditável."""
        warnings = []
        if not letters:
            warnings.append('Nenhum componente com formato compatível foi encontrado.')
        if any(component['width'] >= component['height'] * 2.5 for component in components):
            warnings.append('Algumas regiões são muito largas e podem conter letras agrupadas ou elementos da imagem.')
        if letters and self._calculate_overall_confidence(letters) < 0.75:
            warnings.append('A confiança média é baixa; confirme visualmente os recortes antes de usar o resultado.')
        warnings.append('A detecção depende de contraste, foco e separação entre caracteres; ruídos podem gerar falsos positivos.')
        return warnings
