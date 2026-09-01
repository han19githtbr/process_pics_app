import json
from typing import Dict, Any
from ...core.factory.segmenter_factory import SegmenterFactory
from ...core.models.processing_options import ProcessingOptions
from ...core.utils.image_utils import ImageUtils

class LetterSegmenterHandler:
    """Handler para requisições de segmentação."""
    
    def __init__(self):
        self.segmenter = SegmenterFactory.create_default_segmenter()
    
    def handle_segment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa requisição de segmentação."""
        try:
            image_data = data.get('image')
            if not image_data:
                return {'error': 'Envie uma imagem para processamento.'}, 400
            
            image = ImageUtils.decode_data_url(image_data)
            options_data = data.get('options', {})
            options = ProcessingOptions.from_dict(options_data)
            result = self.segmenter.segment(image, options)
            letters = [
                {
                    'id': i + 1,
                    'line': letter.line,
                    'x': letter.x,
                    'y': letter.y,
                    'width': letter.width,
                    'height': letter.height,
                    'area': letter.area,
                    'confidence': letter.confidence,
                    'image': letter.image
                }
                for i, letter in enumerate(result.letters)
            ]

            meta = {
                'width': result.metadata.get('width'),
                'height': result.metadata.get('height'),
                'totalLetters': result.metadata.get('total_letters'),
                'processingTime': result.metadata.get('processing_time'),
                'confidenceScore': result.metadata.get('confidence_score'),
                'scale': result.metadata.get('scale')
            }

            return {
                'letters': letters,
                'debugImage': result.debug_image,
                'meta': meta,
                'transcript': result.transcript_text,
                'confidence': result.confidence_score
            }, 200
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'error': 'Falha ao segmentar a imagem.',
                'detail': str(e)
            }, 500

    def handle_compare(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Compara duas imagens e retorna similaridade e classificação."""
        try:
            source_image = data.get('sourceImage')
            target_image = data.get('comparisonImage')
            if not source_image or not target_image:
                return {'error': 'Envie duas imagens para comparar.'}, 400

            source_decoded = ImageUtils.decode_data_url(source_image)
            target_decoded = ImageUtils.decode_data_url(target_image)
            options_data = data.get('options', {})
            options = ProcessingOptions.from_dict(options_data)

            comparison = self.segmenter.compare_images(source_decoded, target_decoded, options)
            return {
                'sourceLetters': comparison.get('source_letters'),
                'targetLetters': comparison.get('target_letters'),
                'similarity': comparison.get('similarity'),
                'status': comparison.get('status'),
                'verdict': comparison.get('verdict'),
                'threshold': comparison.get('threshold'),
                'sourceTranscript': comparison.get('source_transcript'),
                'targetTranscript': comparison.get('target_transcript'),
            }, 200
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'error': 'Falha ao comparar as imagens.',
                'detail': str(e)
            }, 500
