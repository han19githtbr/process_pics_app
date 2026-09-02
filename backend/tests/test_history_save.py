from src.services.mongodb_service import MongoDBService


def test_save_history_item_supports_explicit_save():
    service = MongoDBService()
    item_id = service.save_processing_result(
        image_data='data:image/png;base64,abc',
        original_name='imagem-processada.png',
        transcript='HOW TO WRITE',
        letters=[{'id': 1, 'image': 'data:image/png;base64,abc'}],
        metadata={'totalLetters': 1, 'confidenceScore': 0.91},
    )

    assert item_id is not None
    assert service.get_history_item(item_id) is not None
    assert service.list_history(limit=5)[0]['sourceName'] == 'imagem-processada.png'
