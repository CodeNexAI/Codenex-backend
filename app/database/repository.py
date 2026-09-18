"""Generic repository abstraction for database access."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.database.models import Project

T = TypeVar("T")


class Repository(Generic[T]):
    """Provide basic persistence operations for a mapped SQLAlchemy model."""

    def __init__(self, db: Session, model: type[T]) -> None:
        self.db = db
        self.model = model

    def get(self, item_id: str) -> T | None:
        """Return a record by primary key."""
        return self.db.get(self.model, item_id)

    def list(self) -> list[T]:
        """Return all records for this repository's model."""
        return list(self.db.query(self.model).all())

    def add(self, instance: T) -> T:
        """Persist and refresh an instance."""
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance

    def delete(self, instance: T) -> None:
        """Delete an instance."""
        self.db.delete(instance)
        self.db.commit()


class ProjectRepository:
    """Database operations for project records."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, project: Project) -> Project:
        """Persist and refresh a project."""
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def list(self) -> list[Project]:
        """Return projects with newest entries first."""
        return list(self.db.query(Project).order_by(Project.created_at.desc()).all())

    def get(self, project_id: str) -> Project | None:
        """Return a project by ID."""
        return self.db.get(Project, project_id)

    def delete(self, project: Project) -> None:
        """Remove a project record."""
        self.db.delete(project)
        self.db.commit()
