import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

try:
    from bson import ObjectId
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
except Exception:  # pragma: no cover
    ObjectId = None
    MongoClient = None
    PyMongoError = Exception


def _default_collection_name() -> str:
    """Define uma coleção separada para produção para evitar mistura com dados locais."""
    return 'processed_images_prod' if (os.getenv('ENVIRONMENT') or '').strip().lower() == 'production' else 'processed_images'


class MongoDBService:
    """Persistência opcional de processamento em MongoDB Atlas."""

    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None, collection_name: Optional[str] = None):
        self.uri = (uri or os.getenv('MONGODB_URI') or '').strip()
        self.db_name = (db_name or os.getenv('MONGODB_DB_NAME') or 'pattern_checker').strip()
        self.collection_name = (collection_name or os.getenv('MONGODB_COLLECTION_NAME') or _default_collection_name()).strip()
        self.client = None
        self.database = None
        self.collection = None
        self.is_enabled = False
        self._local_history: List[Dict[str, Any]] = []

        if not self.uri or MongoClient is None:
            return

        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.database = self.client[self.db_name]
            self.collection = self.database[self.collection_name]
            self.is_enabled = True
        except Exception:
            self.client = None
            self.database = None
            self.collection = None
            self.is_enabled = False

    def build_processing_document(
        self,
        image_data: str,
        original_name: str,
        transcript: str,
        letters: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            'imageData': image_data,
            'sourceName': original_name,
            'transcript': transcript,
            'letters': letters,
            'metadata': metadata or {},
            'createdAt': datetime.now(timezone.utc),
            'updatedAt': datetime.now(timezone.utc),
        }

    def save_processing_result(
        self,
        image_data: str,
        original_name: str,
        transcript: str,
        letters: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        document = self.build_processing_document(image_data, original_name, transcript, letters, metadata)

        if self.is_enabled and self.collection is not None:
            try:
                result = self.collection.insert_one(document)
                return str(result.inserted_id)
            except PyMongoError:
                pass

        item_id = f"local-{len(self._local_history) + 1}"
        document['_id'] = item_id
        self._local_history.insert(0, document)
        return item_id

    def list_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        if self.is_enabled and self.collection is not None:
            try:
                items = list(self.collection.find({}).sort('createdAt', -1).limit(limit))
                for item in items:
                    item['_id'] = str(item.get('_id'))
                return items
            except PyMongoError:
                pass

        items = list(self._local_history)[:limit]
        for item in items:
            item['_id'] = str(item.get('_id', ''))
        return items

    def get_history_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        if self.is_enabled and self.collection is not None:
            try:
                object_id = ObjectId(item_id) if ObjectId is not None else item_id
                item = self.collection.find_one({'_id': object_id})
                if item is None:
                    return None
                item['_id'] = str(item.get('_id'))
                return item
            except (TypeError, ValueError, PyMongoError):
                pass

        for item in self._local_history:
            if str(item.get('_id')) == str(item_id):
                item = dict(item)
                item['_id'] = str(item.get('_id'))
                return item
        return None

    def get_collection_name(self) -> str:
        return self.collection_name
