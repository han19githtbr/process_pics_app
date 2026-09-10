from typing import Dict, Any
from ...core.factory.enhancer_factory import EnhancerFactory
from ...core.models.enhance_options import EnhanceOptions
from ...core.utils.image_utils import ImageUtils
from ...services.mongodb_service import MongoDBService
from ...config.settings import Settings


class ImageEnhancerHandler:
    """Handler para requisições de melhoria de qualidade de imagem e do
    Banco de Imagens de Alta Qualidade (persistido em uma coleção MongoDB
    dedicada, separada do histórico de segmentação de letras)."""

    def __init__(self):
        self.enhancer = EnhancerFactory.create_default_enhancer()
        settings = Settings()
        self.mongodb_service = MongoDBService(collection_name=settings.MONGODB_BANK_COLLECTION_NAME)

    def handle_enhance(self, data: Dict[str, Any]):
        """Processa requisição de melhoria de qualidade.

        Assim como em `/segment`, quando `preview=True` o resultado NUNCA é
        gravado no Banco de Imagens de Alta Qualidade — apenas requisições sem
        essa flag (o clique explícito em "Melhorar Qualidade") persistem no
        banco, evitando poluir a coleção com pré-visualizações ao vivo.
        """
        try:
            image_data = data.get('image')
            if not image_data:
                return {'error': 'Envie uma imagem para melhorar a qualidade.'}, 400

            is_preview = bool(data.get('preview'))
            image = ImageUtils.decode_data_url(image_data)
            options_data = data.get('options', {})
            options = EnhanceOptions.from_dict(options_data)
            result = self.enhancer.enhance(image, options)

            payload = {
                'enhancedImage': result.enhanced_image,
                'originalImage': result.original_image,
                'steps': result.steps,
                'metrics': result.metrics,
                'metadata': result.metadata,
            }

            if self.mongodb_service.is_enabled and not is_preview:
                file_name = (data.get('fileName') or data.get('name') or 'imagem-melhorada.png').strip() \
                    or 'imagem-melhorada.png'
                saved_id = self.mongodb_service.save_enhanced_image(
                    enhanced_image=result.enhanced_image,
                    original_image=result.original_image,
                    source_name=file_name,
                    techniques=result.metrics.get('techniquesApplied', []),
                    metrics=result.metrics,
                )
                payload['savedToBank'] = bool(saved_id)
                payload['bankItemId'] = saved_id

            return payload, 200

        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                'error': 'Falha ao melhorar a qualidade da imagem.',
                'detail': str(e),
            }, 500

    def list_bank(self, limit: int = 20):
        """Lista os itens mais recentes do Banco de Imagens de Alta Qualidade."""
        return self.mongodb_service.list_enhanced_images(limit=limit)

    def search_bank(self, query: str, limit: int = 20):
        """Busca itens do banco pelo nome do arquivo salvo."""
        return self.mongodb_service.search_enhanced_images(query=query, limit=limit)

    def save_bank_item(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Salva manualmente uma imagem já melhorada no banco (equivalente ao
        botão "Salvar" manual do histórico de segmentação)."""
        try:
            enhanced_image = data.get('enhancedImage') or data.get('image')
            if not enhanced_image:
                return {'error': 'Envie uma imagem melhorada para salvar no banco.'}, 400

            original_image = data.get('originalImage') or ''
            source_name = str(data.get('sourceName') or data.get('fileName') or 'imagem-melhorada.png').strip() \
                or 'imagem-melhorada.png'
            techniques = data.get('techniques') or []
            metrics = data.get('metrics') or {}

            item_id = self.mongodb_service.save_enhanced_image(
                enhanced_image=enhanced_image,
                original_image=original_image,
                source_name=source_name,
                techniques=techniques,
                metrics=metrics,
            )

            if not item_id:
                if self.mongodb_service.uri and not self.mongodb_service.is_enabled:
                    return {
                        'error': 'MongoDB indisponível. Verifique MONGODB_URI, rede, IP allowlist e permissões do banco.',
                    }, 503
                return {'error': 'Não foi possível salvar a imagem no Banco de Imagens de Alta Qualidade.'}, 500

            return {
                '_id': item_id,
                'enhancedImage': enhanced_image,
                'originalImage': original_image,
                'sourceName': source_name,
                'techniques': techniques,
                'metrics': metrics,
            }, 200
        except Exception as e:
            return {'error': 'Falha ao salvar no Banco de Imagens de Alta Qualidade.', 'detail': str(e)}, 500

    def get_bank_item(self, item_id: str):
        """Retorna um item específico do banco por ID."""
        return self.mongodb_service.get_enhanced_image(item_id)

    def delete_bank_item(self, item_id: str):
        """Remove um item individual do Banco de Imagens de Alta Qualidade."""
        try:
            success = self.mongodb_service.delete_enhanced_image(item_id)
            if not success:
                return {'error': 'Item não encontrado no Banco de Imagens de Alta Qualidade.'}, 404
            return {'success': True, 'message': 'Item removido do banco de imagens de alta qualidade com sucesso.'}, 200
        except Exception as e:
            return {'error': 'Falha ao remover item do banco de imagens de alta qualidade.', 'detail': str(e)}, 500

    def clear_bank(self):
        """Limpa todos os itens do Banco de Imagens de Alta Qualidade."""
        try:
            count = self.mongodb_service.clear_enhanced_images()
            return {
                'success': True,
                'deletedCount': count,
                'message': f'Banco de Imagens de Alta Qualidade limpo com sucesso ({count} itens apagados).',
            }, 200
        except Exception as e:
            return {'error': 'Falha ao limpar o Banco de Imagens de Alta Qualidade.', 'detail': str(e)}, 500
