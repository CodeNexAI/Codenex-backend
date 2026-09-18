from pathlib import Path

from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.database.database import get_session_factory
from app.database.models import Project


def test_project_create_retrieve_and_delete(client: TestClient) -> None:
    create_response = client.post(
        "/api/projects",
        json={
            "name": "Student API",
            "description": "CRUD service",
            "project_type": "fastapi",
        },
    )
    assert create_response.status_code == 201
    project = create_response.json()
    assert "workspace_path" not in project
    workspace_path = next(Path(get_settings().workspace_root).glob("student-api-*"))
    assert workspace_path.exists()

    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    get_response = client.get(f"/api/projects/{project['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Student API"

    delete_response = client.delete(f"/api/projects/{project['id']}")
    assert delete_response.status_code == 204
    assert not workspace_path.exists()

    missing_response = client.get(f"/api/projects/{project['id']}")
    assert missing_response.status_code == 404
    assert missing_response.json()["error"]["message"] == "Project not found"


def test_project_rejects_unsupported_type(client: TestClient) -> None:
    """Project creation only accepts the currently supported project types."""
    response = client.post(
        "/api/projects",
        json={"name": "Unsupported", "project_type": "rust"},
    )

    assert response.status_code == 422


def test_project_delete_skips_external_workspace(
    client: TestClient,
    tmp_path: Path,
) -> None:
    external_workspace = tmp_path / "external-workspace"
    external_workspace.mkdir()
    (external_workspace / "keep.txt").write_text("safe", encoding="utf-8")

    with get_session_factory()() as db:
        project = Project(
            name="External Project",
            description=None,
            project_type="generic",
            workspace_path=str(external_workspace),
            status="created",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

    response = client.delete(f"/api/projects/{project_id}")

    assert response.status_code == 204
    assert external_workspace.exists()
    assert (external_workspace / "keep.txt").exists()
