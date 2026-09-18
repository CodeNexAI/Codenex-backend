from pathlib import Path


def test_project_create_retrieve_and_delete(client):
    create_response = client.post(
        "/api/projects",
        json={"name": "Student API", "description": "CRUD service", "project_type": "fastapi"},
    )
    assert create_response.status_code == 201
    project = create_response.json()
    workspace_path = Path(project["workspace_path"])
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
