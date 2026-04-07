from typing import Any, Dict, Optional, Type
from sqlalchemy.orm import Session


class BaseRepository:
    def __init__(self, model: Type[Any]):
        self.model = model

    def create(self, db: Session, obj_in: Dict[str, Any]):
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def get_by_id(self, db: Session, id: int) -> Optional[Any]:
        return db.get(self.model, id)

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(self.model).offset(skip).limit(limit).all()

    def update(self, db: Session, db_obj: Any, obj_in: Dict[str, Any]):
        for field, value in obj_in.items():
            if hasattr(db_obj, field) and value is not None:
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.flush()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, id: int) -> Optional[Any]:
        obj = self.get_by_id(db, id)
        if obj:
            db.delete(obj)
            return obj
        return None