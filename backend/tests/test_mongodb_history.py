import os

from src.services.mongodb_service import MongoDBService


def test_mongodb_service_is_disabled_without_uri():
    service = MongoDBService()

    assert service.is_enabled is False
    assert service.collection_name == 'processed_images'


def test_mongodb_service_uses_production_collection_name():
    original_env = os.environ.get('ENVIRONMENT')
    original_collection = os.environ.get('MONGODB_COLLECTION_NAME')
    os.environ['ENVIRONMENT'] = 'production'
    os.environ.pop('MONGODB_COLLECTION_NAME', None)

    try:
        service = MongoDBService()
        assert service.collection_name == 'processed_images_prod'
    finally:
        if original_env is None:
            os.environ.pop('ENVIRONMENT', None)
        else:
            os.environ['ENVIRONMENT'] = original_env

        if original_collection is None:
            os.environ.pop('MONGODB_COLLECTION_NAME', None)
        else:
            os.environ['MONGODB_COLLECTION_NAME'] = original_collection


def test_mongodb_service_builds_history_document():
    service = MongoDBService()
    document = service.build_processing_document(
        image_data='data:image/png;base64,abc',
        original_name='sample.png',
        transcript='S A M P L E',
        letters=[{'id': 1, 'width': 10, 'height': 10, 'image': 'data:image/png;base64,abc'}],
        metadata={'totalLetters': 1, 'confidenceScore': 0.9}
    )

    assert document['imageData'] == 'data:image/png;base64,abc'
    assert document['sourceName'] == 'sample.png'
    assert document['transcript'] == 'S A M P L E'
    assert document['letters'][0]['id'] == 1
