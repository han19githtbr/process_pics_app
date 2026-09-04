import json
from typing import Dict, Any, List, Optional
from ...core.factory.segmenter_factory import SegmenterFactory
from ...core.models.processing_options import ProcessingOptions
from ...core.utils.image_utils import ImageUtils
from ...services.mongodb_service import MongoDBService


class LetterSegmenterHandler:
    """Handler para requisições de segmentação."""

    def __init__(self):
        self.segmenter = SegmenterFactory.create_default_segmenter()
        self.mongodb_service = MongoDBService()

    def _serialize_letters(self, result) -> List[Dict[str, Any]]:
        return [
            {
                'id': i + 1,
                'line': letter.line,
                'x': letter.x,
                'y': letter.y,
                'width': letter.width,
                'height': letter.height,
                'area': letter.area,
                'confidence': letter.confidence,
                'confidenceDetails': getattr(letter, 'confidence_details', None),
                'image': letter.image,
            }
            for i, letter in enumerate(result.letters)
        ]

    def list_history(self, limit: int = 20):
        return self.mongodb_service.list_history(limit=limit)

    def search_history(self, query: str, limit: int = 20):
        return self.mongodb_service.search_history(query=query, limit=limit)

    def save_history_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            image_data = data.get('imageData') or data.get('image')
            if not image_data:
                return {'error': 'Envie uma imagem para salvar no histórico.'}, 400

            original_name = str(data.get('sourceName') or data.get('fileName') or 'imagem-processada.png').strip() or 'imagem-processada.png'
            transcript = data.get('transcript') or ''
            letters = data.get('letters') or []
            metadata = data.get('metadata') or {}

            item_id = self.mongodb_service.save_processing_result(
                image_data=image_data,
                original_name=original_name,
                transcript=transcript,
                letters=letters,
                metadata=metadata,
            )

            if not item_id:
                if self.mongodb_service.uri and not self.mongodb_service.is_enabled:
                    return {
                        'error': 'MongoDB indisponível. Verifique MONGODB_URI, rede, IP allowlist e permissões do banco.',
                    }, 503
                return {'error': 'Não foi possível salvar o item no histórico.'}, 500

            return {
                '_id': item_id,
                'imageData': image_data,
                'sourceName': original_name,
                'transcript': transcript,
                'letters': letters,
                'metadata': metadata,
            }, 200
        except Exception as e:
            return {'error': 'Falha ao salvar a imagem no histórico.', 'detail': str(e)}, 500

    def get_history_item(self, item_id: str):
        return self.mongodb_service.get_history_item(item_id)

    def delete_history_item(self, item_id: str):
        """Remove um item individual do histórico."""
        try:
            success = self.mongodb_service.delete_history_item(item_id)
            if not success:
                return {'error': 'Item não encontrado no histórico.'}, 404
            return {'success': True, 'message': 'Item removido do histórico com sucesso.'}, 200
        except Exception as e:
            return {'error': 'Falha ao remover item do histórico.', 'detail': str(e)}, 500

    def clear_history(self):
        """Limpa todos os itens do histórico."""
        try:
            count = self.mongodb_service.clear_history()
            return {
                'success': True,
                'deletedCount': count,
                'message': f'Histórico limpo com sucesso ({count} itens apagados).',
            }, 200
        except Exception as e:
            return {'error': 'Falha ao limpar histórico.', 'detail': str(e)}, 500

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
            letters = self._serialize_letters(result)
            transcript = result.transcript or result.transcript_text

            conf_breakdown = result.metadata.get('confidence_breakdown', {})
            meta = {
                'width': result.metadata.get('width'),
                'height': result.metadata.get('height'),
                'totalLetters': result.metadata.get('total_letters'),
                'processingTime': result.metadata.get('processing_time'),
                'confidenceScore': result.metadata.get('confidence_score'),
                'confidenceBreakdown': conf_breakdown,
                'scale': result.metadata.get('scale'),
                'edgePixels': result.metadata.get('edge_pixels'),
                'splitsCount': result.metadata.get('splits_count', 0),
                'filteredCount': result.metadata.get('filtered_count', 0),
                'mode': result.metadata.get('mode', 'enhanced'),
                'warnings': result.metadata.get('warnings', []),
                'transcript': transcript,
            }

            payload = {
                'letters': letters,
                'debugImage': result.debug_image,
                'steps': getattr(result, 'steps', []),
                'meta': meta,
                'transcript': transcript,
                'confidence': result.confidence_score,
                'confidenceBreakdown': conf_breakdown,
            }

            if self.mongodb_service.is_enabled:
                file_name = (data.get('fileName') or data.get('name') or 'imagem-processada.png').strip() or 'imagem-processada.png'
                self.mongodb_service.save_processing_result(
                    image_data=image_data,
                    original_name=file_name,
                    transcript=transcript,
                    letters=letters,
                    metadata=meta,
                )

            return payload, 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'error': 'Falha ao segmentar a imagem.',
                'detail': str(e),
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
                'detail': str(e),
            }, 500
