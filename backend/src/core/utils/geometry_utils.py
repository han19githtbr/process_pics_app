from typing import Tuple
from ..models.letter_box import LetterBox

class GeometryUtils:
    """Utilitários para operações geométricas."""
    
    @staticmethod
    def calculate_overlap(box1: LetterBox, box2: LetterBox) -> float:
        """Calcula sobreposição entre duas caixas."""
        x_left = max(box1.x, box2.x)
        y_top = max(box1.y, box2.y)
        x_right = min(box1.x + box1.width, box2.x + box2.width)
        y_bottom = min(box1.y + box1.height, box2.y + box2.height)
        
        if x_right <= x_left or y_bottom <= y_top:
            return 0.0
        
        overlap_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = box1.width * box1.height
        area2 = box2.width * box2.height
        
        return overlap_area / max(area1, area2)
    
    @staticmethod
    def expand_rect(x: int, y: int, width: int, height: int, 
                   padding: int, max_width: int, max_height: int) -> Tuple[int, int, int, int]:
        """Expande um retângulo com padding."""
        new_x = max(0, x - padding)
        new_y = max(0, y - padding)
        new_width = min(max_width - new_x, width + 2 * padding)
        new_height = min(max_height - new_y, height + 2 * padding)
        return (new_x, new_y, new_width, new_height)
    
    @staticmethod
    def get_aspect_ratio(width: int, height: int) -> float:
        """Retorna a proporção largura/altura."""
        return width / max(height, 1)
    
    @staticmethod
    def get_area(width: int, height: int) -> int:
        """Retorna a área de um retângulo."""
        return width * height