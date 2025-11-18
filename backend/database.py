import os
from typing import Any, Dict, List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import BaseModel
from urllib.parse import quote_plus

DATABASE_URL = os.getenv("DATABASE_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ai_tools_db")

_client: AsyncIOMotorClient = AsyncIOMotorClient(DATABASE_URL)
db: AsyncIOMotorDatabase = _client[DATABASE_NAME]


def _collection_name(model_or_name: Any) -> str:
    if isinstance(model_or_name, str):
        return model_or_name
    # Derive from pydantic class name
    return model_or_name.__class__.__name__.lower()


async def create_document(collection_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    # Ensure timestamps
    now = datetime.utcnow()
    data.setdefault("created_at", now)
    data.setdefault("updated_at", now)
    col = db[collection_name]
    res = await col.insert_one(data)
    return {"_id": str(res.inserted_id), **data}


async def get_documents(collection_name: str, filter_dict: Optional[Dict[str, Any]] = None, limit: int = 50) -> List[Dict[str, Any]]:
    filter_dict = filter_dict or {}
    col = db[collection_name]
    cursor = col.find(filter_dict).sort("created_at", -1).limit(limit)
    items: List[Dict[str, Any]] = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])  # stringify ObjectId
        items.append(doc)
    return items
