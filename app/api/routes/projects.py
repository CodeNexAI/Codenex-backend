from fastapi import APIRouter, HTTPException, status

from app.api.dependencies import (
    AuthenticatedDependency,
    DatabaseDependency,
    SettingsDependency,
)
from app.models.schemas import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    description="Creates a project workspace record without generating any code.",
    responses={401: {"description": "Missing or invalid bearer token."}},
)
async def create_project(
    payload: ProjectCreate,
    db: DatabaseDependency,
    settings: SettingsDependency,
    _auth: AuthenticatedDependency,
) -> ProjectResponse:
    service = ProjectService(db, settings)
    return ProjectResponse.model_validate(service.create_project(payload))


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List projects",
    responses={401: {"description": "Missing or invalid bearer token."}},
)
async def list_projects(
    db: DatabaseDependency, settings: SettingsDependency, _auth: AuthenticatedDependency
) -> list[ProjectResponse]:
    service = ProjectService(db, settings)
    return [
        ProjectResponse.model_validate(project) for project in service.list_projects()
    ]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a project",
    responses={
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Project not found."},
    },
)
async def get_project(
    project_id: str,
    db: DatabaseDependency,
    settings: SettingsDependency,
    _auth: AuthenticatedDependency,
) -> ProjectResponse:
    service = ProjectService(db, settings)
    project = service.get_project(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Removes the project record and its assigned workspace.",
    responses={
        401: {"description": "Missing or invalid bearer token."},
        404: {"description": "Project not found."},
    },
)
async def delete_project(
    project_id: str,
    db: DatabaseDependency,
    settings: SettingsDependency,
    _auth: AuthenticatedDependency,
) -> None:
    service = ProjectService(db, settings)
    if not service.delete_project(project_id):
        raise HTTPException(status_code=404, detail="Project not found")
