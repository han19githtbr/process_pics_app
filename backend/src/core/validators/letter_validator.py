import cv2
import numpy as np
from typing import List, Optional
from ..interfaces.letter_validator import ILetterValidator
from ..models.letter_box import LetterBox
from ..utils.geometry_utils import GeometryUtils

class LetterValidator(ILetterValidator):
    """Validador de letras com inspeção de contraste, geometria e coerência tipográfica de linha."""
    
    MIN_CONFIDENCE = 0.50
    OVERLAP_THRESHOLD = 0.50
    
    def validate(self, letter_boxes: List[LetterBox], image: np.ndarray,
                 raw_image: Optional[np.ndarray] = None) -> List[LetterBox]:
        """Valida e filtra caixas de letras com remoção de duplicatas, ruídos e coerência tipográfica."""
        # 1. Remover duplicatas
        unique = self._remove_duplicates(letter_boxes)
        
        # Calcular alturas medianas por linha para contextualização do alinhamento
        by_line = {}
        for box in unique:
            by_line.setdefault(box.line or 1, []).append(box.height)
        line_medians = {lid: float(np.median(hs)) for lid, hs in by_line.items()}

        # 2. Recalcular confiança com dados de imagem bruta/contraste e contexto de linha
        for box in unique:
            details = self.calculate_confidence_details(
                box, image, raw_image, line_med_h=line_medians.get(box.line or 1)
            )
            box.confidence = details['overall']
            box.confidence_details = details

        # 3. Filtrar por confiança mínima
        filtered = [box for box in unique if box.confidence >= self.MIN_CONFIDENCE]
        
        # 4. Filtro de coerência tipográfica por linha (rejeitar alturas anômalas)
        coherent = self._filter_line_outliers(filtered)
        
        return coherent
    
    def calculate_confidence_details(self, letter_box: LetterBox, image: np.ndarray,
                                     raw_image: Optional[np.ndarray] = None,
                                     line_med_h: Optional[float] = None) -> dict:
        """
        Calcula a pontuação detalhada e 100% transparente dos 4 pilares de confiança:
        morfologia tipográfica, contraste de tinta, solidez e coerência de linha.
        """
        # 1. Avaliação morfológica de aspecto (largura / altura)
        ar = letter_box.aspect_ratio
        if 0.28 <= ar <= 0.95:
            ar_score = 1.0
        elif 0.18 <= ar < 0.28 or 0.95 < ar <= 1.45:
            ar_score = 0.93
        elif 0.10 <= ar < 0.18 or 1.45 < ar <= 1.85:
            ar_score = 0.85
        elif ar < 0.05 or ar > 3.5:
            return {
                'aspect_ratio': 0.10,
                'contrast': 0.10,
                'line_coherence': 0.10,
                'density': 0.10,
                'overall': 0.10,
            }
        else:
            ar_score = 0.72

        # 2. Avaliação de contraste e desvio padrão de tinta no suporte
        contrast_score = 0.95
        eval_img = raw_image if raw_image is not None else image
        if eval_img is not None and eval_img.size > 0:
            h_img, w_img = eval_img.shape[:2]
            gray = cv2.cvtColor(eval_img, cv2.COLOR_BGR2GRAY) if eval_img.ndim == 3 else eval_img
            
            pad = 2
            x0 = max(0, letter_box.x - pad)
            y0 = max(0, letter_box.y - pad)
            x1 = min(w_img, letter_box.x + letter_box.width + pad)
            y1 = min(h_img, letter_box.y + letter_box.height + pad)
            
            crop = gray[y0:y1, x0:x1]
            if crop.size > 0:
                std_val = float(np.std(crop))
                dyn_range = float(np.max(crop) - np.min(crop))
                if std_val < 14.0 or dyn_range < 30.0:
                    return {
                        'aspect_ratio': round(ar_score, 4),
                        'contrast': 0.10,
                        'line_coherence': 0.10,
                        'density': 0.10,
                        'overall': 0.10,
                    }
                elif std_val >= 45.0 and dyn_range >= 140.0:
                    contrast_score = 1.0
                elif std_val >= 30.0 and dyn_range >= 90.0:
                    contrast_score = 0.92
                elif std_val >= 20.0:
                    contrast_score = 0.82
                else:
                    contrast_score = 0.70

        # 3. Teste de moldura vazada (se for retângulo grande vazio no centro)
        if image is not None and image.ndim == 2 and letter_box.width >= 25 and letter_box.height >= 25:
            h_bin, w_bin = image.shape[:2]
            x0 = max(0, letter_box.x)
            y0 = max(0, letter_box.y)
            x1 = min(w_bin, letter_box.x + letter_box.width)
            y1 = min(h_bin, letter_box.y + letter_box.height)
            crop_bin = image[y0:y1, x0:x1]
            if crop_bin.size > 0:
                cy, cx = crop_bin.shape
                mid = crop_bin[int(cy * 0.25):int(cy * 0.75), int(cx * 0.25):int(cx * 0.75)]
                central_fill = float(np.mean(mid > 0)) if mid.size > 0 else 0
                bbox_area = max(letter_box.width * letter_box.height, 1)
                density = float(np.count_nonzero(crop_bin)) / bbox_area
                edge_width = max(2, int(min(cx, cy) * 0.16))
                side_fills = [
                    float(np.mean(crop_bin[:edge_width, :] > 0)),
                    float(np.mean(crop_bin[:, -edge_width:] > 0)),
                    float(np.mean(crop_bin[-edge_width:, :] > 0)),
                    float(np.mean(crop_bin[:, :edge_width] > 0)),
                ]
                strong_sides = sum(fill > 0.35 for fill in side_fills)
                weak_sides = sum(fill < 0.12 for fill in side_fills)
                has_adjacent_corner = any(
                    side_fills[i] > 0.35 and side_fills[(i + 1) % 4] > 0.35
                    for i in range(4)
                )
                if (
                    central_fill < 0.03
                    and density < 0.20
                    and strong_sides == 2
                    and weak_sides == 2
                    and has_adjacent_corner
                    and 0.8 <= letter_box.aspect_ratio <= 1.25
                    and (letter_box.width > 35 or letter_box.height > 35)
                ):
                    return {
                        'aspect_ratio': round(ar_score, 4),
                        'contrast': round(contrast_score, 4),
                        'line_coherence': 0.10,
                        'density': 0.10,
                        'overall': 0.10,
                    }

        # 4. Coerência tipográfica de linha
        line_score = 0.95
        if line_med_h and line_med_h > 0:
            ratio = letter_box.height / max(line_med_h, 1.0)
            if 0.75 <= ratio <= 1.35:
                line_score = 1.0
            elif 0.50 <= ratio < 0.75 or 1.35 < ratio <= 1.80:
                line_score = 0.92
            elif 0.28 <= ratio < 0.50:
                line_score = 0.82
            else:
                line_score = 0.65

        # 5. Densidade de preenchimento (solidez)
        bbox_area = max(letter_box.width * letter_box.height, 1)
        density = letter_box.area / bbox_area if letter_box.area else 0.4
        if 0.15 <= density <= 0.75:
            dens_score = 1.0
        elif 0.10 <= density < 0.15 or 0.75 < density <= 0.92:
            dens_score = 0.90
        else:
            dens_score = 0.72

        confidence = 0.35 * ar_score + 0.30 * contrast_score + 0.20 * line_score + 0.15 * dens_score
        overall = round(float(min(1.0, max(0.1, confidence))), 4)

        return {
            'aspect_ratio': round(ar_score, 4),
            'contrast': round(contrast_score, 4),
            'line_coherence': round(line_score, 4),
            'density': round(dens_score, 4),
            'overall': overall,
        }

    def calculate_confidence(self, letter_box: LetterBox, image: np.ndarray,
                             raw_image: Optional[np.ndarray] = None,
                             line_med_h: Optional[float] = None) -> float:
        """Calcula a pontuação de confiança de que o componente é uma letra."""
        return self.calculate_confidence_details(letter_box, image, raw_image, line_med_h)['overall']
    
    def is_letter(self, letter_box: LetterBox, image: np.ndarray) -> bool:
        """Verifica se um componente é uma letra."""
        confidence = self.calculate_confidence(letter_box, image)
        return confidence >= self.MIN_CONFIDENCE

    def _filter_line_outliers(self, boxes: List[LetterBox]) -> List[LetterBox]:
        """Remove componentes com alturas excessivamente destoantes da mediana da linha ou isolados."""
        if not boxes:
            return []
            
        by_line = {}
        for box in boxes:
            line_id = box.line or 1
            by_line.setdefault(line_id, []).append(box)
            
        all_heights = [b.height for b in boxes]
        global_med_h = float(np.median(all_heights)) if all_heights else 40.0

        validated = []
        for line_id, line_boxes in by_line.items():
            if len(line_boxes) >= 3:
                med_height = float(np.median([b.height for b in line_boxes]))
                for b in line_boxes:
                    if 0.28 * med_height <= b.height <= 2.2 * med_height:
                        validated.append(b)
            else:
                for b in line_boxes:
                    if b.height >= 0.35 * global_med_h and b.confidence >= 0.50:
                        validated.append(b)
                
        return validated
    
    def _remove_duplicates(self, letter_boxes: List[LetterBox]) -> List[LetterBox]:
        """Remove caixas duplicadas."""
        if not letter_boxes:
            return []
        
        # Ordenar por confiança (maior primeiro)
        sorted_boxes = sorted(letter_boxes, key=lambda b: b.confidence, reverse=True)
        unique: List[LetterBox] = []
        
        for box in sorted_boxes:
            is_duplicate = False
            for existing in unique:
                overlap = GeometryUtils.calculate_overlap(box, existing)
                if overlap > self.OVERLAP_THRESHOLD:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique.append(box)
        
        return unique
