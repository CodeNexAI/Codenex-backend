from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

T = TypeVar("T")


class Repository(Generic[T]):
    def __init__(self, db: Session, model: type[T]) -> None:
        self.db = db
        self.model = model

    def get(self, item_id: str) -> T | None:
        return self.db.get(self.model, item_id)

    def list(self) -> list[T]:
        return list(self.db.query(self.model).all())

    def add(self, instance: T) -> T:
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: T) -> None:
        self.db.delete(instance)
        self.db.commit()
