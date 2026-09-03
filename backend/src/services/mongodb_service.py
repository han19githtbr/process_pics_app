import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / '.env')

logger = logging.getLogger('mongodb_service')

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
        except Exception as exc:
            logger.error(
                'Falha ao conectar no MongoDB (uri configurada, mas conexão/ping falhou): %s',
                exc,
            )
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
            except PyMongoError as exc:
                logger.error('Falha ao inserir item no histórico do MongoDB: %s', exc)

        # Fallback para histórico local em memória caso Mongo remoto esteja inacessível ou sem URI
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
            except PyMongoError as exc:
                logger.error('Falha ao listar histórico do MongoDB: %s', exc)

        items = list(self._local_history)[:limit]
        for item in items:
            item['_id'] = str(item.get('_id', ''))
        return items

    def get_history_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        if self.is_enabled and self.collection is not None:
            try:
                object_id = ObjectId(item_id) if ObjectId is not None else item_id
                item = self.collection.find_one({'_id': object_id})
                if item is not None:
                    item['_id'] = str(item.get('_id'))
                    return item
            except (TypeError, ValueError, PyMongoError) as exc:
                logger.error('Falha ao buscar item %s no histórico do MongoDB: %s', item_id, exc)

        for item in self._local_history:
            if str(item.get('_id')) == str(item_id):
                item = dict(item)
                item['_id'] = str(item.get('_id'))
                return item

        return None

    def get_collection_name(self) -> str:
        return self.collection_name

    def search_history(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Busca itens do histórico pelo nome do arquivo salvo."""
        term = (query or '').strip()

        if not term:
            return self.list_history(limit=limit)

        if self.is_enabled and self.collection is not None:
            try:
                pattern = re.escape(term)
                mongo_filter = {
                    '$or': [
                        {'sourceName': {'$regex': pattern, '$options': 'i'}},
                        {'transcript': {'$regex': pattern, '$options': 'i'}},
                    ]
                }
                items = list(
                    self.collection.find(mongo_filter).sort('createdAt', -1).limit(limit)
                )
                for item in items:
                    item['_id'] = str(item.get('_id'))
                return items
            except PyMongoError as exc:
                logger.error('Falha ao buscar histórico no MongoDB: %s', exc)

        term_lower = term.lower()
        items = [
            item for item in self._local_history
            if term_lower in str(item.get('sourceName', '')).lower()
            or term_lower in str(item.get('transcript', '')).lower()
        ][:limit]
        for item in items:
            item['_id'] = str(item.get('_id', ''))
        return items

    def delete_history_item(self, item_id: str) -> bool:
        """Remove um item do histórico pelo ID (no MongoDB e no fallback local)."""
        deleted = False
        clean_id = str(item_id).strip()

        if self.is_enabled and self.collection is not None:
            try:
                queries = [{'_id': clean_id}]
                if ObjectId is not None and ObjectId.is_valid(clean_id):
                    queries.append({'_id': ObjectId(clean_id)})

                query = {'$or': queries} if len(queries) > 1 else queries[0]
                res = self.collection.delete_one(query)
                if res.deleted_count > 0:
                    deleted = True
            except (TypeError, ValueError, PyMongoError) as exc:
                logger.error('Falha ao remover item %s do histórico no MongoDB: %s', clean_id, exc)

        initial_len = len(self._local_history)
        self._local_history = [
            item for item in self._local_history
            if str(item.get('_id')) != clean_id
        ]
        if len(self._local_history) < initial_len:
            deleted = True

        return deleted

    def clear_history(self) -> int:
        """Remove todos os itens do histórico (no MongoDB e no fallback local)."""
        deleted_count = 0

        if self.is_enabled and self.collection is not None:
            try:
                res = self.collection.delete_many({})
                deleted_count += res.deleted_count
            except PyMongoError as exc:
                logger.error('Falha ao limpar histórico no MongoDB: %s', exc)

        deleted_count += len(self._local_history)
        self._local_history.clear()
        return deleted_count
