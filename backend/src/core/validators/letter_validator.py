import numpy as np
from typing import List
from ..interfaces.letter_validator import ILetterValidator
from ..models.letter_box import LetterBox
from ..utils.geometry_utils import GeometryUtils

class LetterValidator(ILetterValidator):
    """Validador de letras."""
    
    MIN_CONFIDENCE = 0.5
    OVERLAP_THRESHOLD = 0.5
    
    def validate(self, letter_boxes: List[LetterBox], image: np.ndarray) -> List[LetterBox]:
        """Valida e filtra caixas de letras."""
        # Remover duplicatas
        unique = self._remove_duplicates(letter_boxes)
        
        # Filtrar por confiança
        filtered = [box for box in unique if box.confidence >= self.MIN_CONFIDENCE]
        
        # Validar formato
        return [box for box in filtered if self.is_letter(box, image)]
    
    def calculate_confidence(self, letter_box: LetterBox, image: np.ndarray) -> float:
        """Calcula confiança de que um componente é uma letra."""
        confidence = 1.0
        
        # Aspect ratio
        if letter_box.aspect_ratio < 0.2 or letter_box.aspect_ratio > 2.0:
            confidence *= 0.7
        
        # Área relativa
        total_area = image.shape[0] * image.shape[1]
        area_ratio = letter_box.area / total_area
        if area_ratio < 0.001:
            confidence *= 0.8
        if area_ratio > 0.1:
            confidence *= 0.9
        
        return min(1.0, confidence)
    
    def is_letter(self, letter_box: LetterBox, image: np.ndarray) -> bool:
        """Verifica se um componente é uma letra."""
        confidence = self.calculate_confidence(letter_box, image)
        return confidence >= self.MIN_CONFIDENCE
    
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