from __future__ import annotations

import shutil
from pathlib import Path
import re
import uuid

from sqlalchemy.orm import Session

from app.config.settings import Settings
from app.database.models import Project
from app.models.schemas import ProjectCreate


class ProjectService:
    def __init__(self, db: Session, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def create_project(self, payload: ProjectCreate) -> Project:
        workspace_root = Path(self.settings.workspace_root).resolve()
        workspace_root.mkdir(parents=True, exist_ok=True)
        slug = re.sub(r"[^a-z0-9-]+", "-", payload.name.lower().replace(" ", "-")).strip("-") or "project"
        project = Project(
            name=payload.name,
            description=payload.description,
            project_type=payload.project_type,
            workspace_path=str(workspace_root / f"{slug}-{uuid.uuid4().hex[:8]}"),
            status="created",
        )
        self.db.add(project)
        try:
            self.db.commit()
            self.db.refresh(project)
        except Exception:
            self.db.rollback()
            raise
        try:
            Path(project.workspace_path).mkdir(parents=True, exist_ok=True)
            return project
        except Exception:
            workspace_path = Path(project.workspace_path)
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
            persisted = self.db.get(Project, project.id)
            if persisted is not None:
                self.db.delete(persisted)
                self.db.commit()
            raise

    def list_projects(self) -> list[Project]:
        return list(self.db.query(Project).order_by(Project.created_at.desc()).all())

    def get_project(self, project_id: str) -> Project | None:
        return self.db.get(Project, project_id)

    def delete_project(self, project_id: str) -> bool:
        project = self.get_project(project_id)
        if project is None:
            return False
        workspace_root = Path(self.settings.workspace_root).resolve()
        workspace_path = Path(project.workspace_path).resolve()
        try:
            workspace_path.relative_to(workspace_root)
        except ValueError:
            pass
        else:
            if workspace_path.exists():
                shutil.rmtree(workspace_path)
        self.db.delete(project)
        self.db.commit()
        return True
