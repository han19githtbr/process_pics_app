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
        
        # 2. Recalcular confiança com dados de imagem bruta/contraste se disponível
        for box in unique:
            box.confidence = self.calculate_confidence(box, image, raw_image)

        # 3. Filtrar por confiança mínima
        filtered = [box for box in unique if box.confidence >= self.MIN_CONFIDENCE]
        
        # 4. Filtro de coerência tipográfica por linha (rejeitar alturas anômalas)
        coherent = self._filter_line_outliers(filtered)
        
        return coherent
    
    def calculate_confidence(self, letter_box: LetterBox, image: np.ndarray,
                             raw_image: Optional[np.ndarray] = None) -> float:
        """Calcula confiança de que um componente é uma letra, avaliando morfologia e contraste de tinta."""
        confidence = 1.0
        
        # Proporção largura / altura (aspect ratio)
        ar = letter_box.aspect_ratio
        if ar < 0.05 or ar > 3.5:
            return 0.1
        elif ar < 0.12 or ar > 2.0:
            confidence *= 0.8
        
        # Área relativa à imagem
        total_area = image.shape[0] * image.shape[1]
        area_ratio = letter_box.area / max(total_area, 1)
        if area_ratio < 0.0001:
            confidence *= 0.8
        if area_ratio > 0.15:
            return 0.1
            
        # Inspeção de contraste e desvio padrão no recorte (evita recortes de fundo liso)
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
                # Se for fundo homogêneo (sem tinta / sem letra)
                if std_val < 14.0 or dyn_range < 30.0:
                    return 0.1
                elif std_val < 22.0:
                    confidence *= 0.85
                    
        # Teste de moldura vazada (se a imagem binária estiver disponível)
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
                if central_fill < 0.03 and (letter_box.width > 35 or letter_box.height > 35):
                    return 0.1
        
        return min(1.0, max(0.0, confidence))
    
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
                    if 0.40 * med_height <= b.height <= 2.0 * med_height:
                        validated.append(b)
            else:
                for b in line_boxes:
                    if b.height >= 0.50 * global_med_h and b.confidence >= 0.60:
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