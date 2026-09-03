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


def test_delete_history_item_removes_item():
    service = MongoDBService()
    item_id = service.save_processing_result(
        image_data='data:image/png;base64,123',
        original_name='item_to_delete.png',
        transcript='DELETE ME',
        letters=[{'id': 1, 'image': 'data:image/png;base64,123'}],
    )

    assert service.get_history_item(item_id) is not None
    deleted = service.delete_history_item(item_id)
    assert deleted is True
    assert service.get_history_item(item_id) is None

    # Deletar novamente deve retornar False
    assert service.delete_history_item(item_id) is False


def test_clear_history_removes_all_items():
    service = MongoDBService()
    service.save_processing_result(
        image_data='data:image/png;base64,aaa',
        original_name='item1.png',
        transcript='AAA',
        letters=[],
    )
    service.save_processing_result(
        image_data='data:image/png;base64,bbb',
        original_name='item2.png',
        transcript='BBB',
        letters=[],
    )

    assert len(service.list_history(limit=10)) >= 2
    deleted_count = service.clear_history()
    assert deleted_count >= 2
    assert len(service.list_history(limit=10)) == 0


def test_handler_delete_and_clear():
    from src.api.handlers.letter_segmenter_handler import LetterSegmenterHandler
    handler = LetterSegmenterHandler()

    res, code = handler.save_history_item({
        'imageData': 'data:image/png;base64,xyz',
        'sourceName': 'handler_test.png',
        'letters': [{'id': 1, 'image': 'data:image/png;base64,xyz'}],
    })
    assert code == 200
    item_id = res['_id']

    # Deletar item existente
    del_res, del_code = handler.delete_history_item(item_id)
    assert del_code == 200
    assert del_res['success'] is True

    # Deletar inexistente
    del_res404, del_code404 = handler.delete_history_item('inexistente_id_999')
    assert del_code404 == 404

    # Salvar e limpar
    handler.save_history_item({
        'imageData': 'data:image/png;base64,xyz',
        'sourceName': 'to_clear.png',
        'letters': [],
    })
    clear_res, clear_code = handler.clear_history()
    assert clear_code == 200
    assert clear_res['success'] is True
    assert clear_res['deletedCount'] >= 1
