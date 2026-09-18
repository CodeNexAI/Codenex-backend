from __future__ import annotations

from app.models.provider import ModelProvider, ModelProviderError
from app.models.schemas import CodeAction, DebugResult, ImplementationPlan
from app.tools.file_tools import (
    create_file,
    delete_file,
    update_file,
    validate_relative_path,
)


class CoderAgent:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    async def generate_actions(
        self,
        requirement: str,
        plan: ImplementationPlan,
        existing_files: list[str] | None = None,
    ) -> list[CodeAction]:
        fallback = {
            "actions": [
                CodeAction(action="CREATE_FILE", path=path, content="").model_dump()
                for planned_file in plan.files
                for path in [planned_file.path]
            ]
        }
        try:
            payload = await self.provider.generate_structured_response(
                prompt=(
                    f"Requirement: {requirement}\nPlan: {plan.model_dump_json()}\n"
                    f"Existing files: {existing_files or []}"
                ),
                schema_name="code_actions",
                fallback=fallback,
            )
            return [CodeAction.model_validate(item) for item in payload["actions"]]
        except (KeyError, ModelProviderError, ValueError):
            return [CodeAction.model_validate(item) for item in fallback["actions"]]

    async def generate_fix_actions(
        self, debug_result: DebugResult, plan: ImplementationPlan
    ) -> list[CodeAction]:
        return [
            CodeAction(
                action="UPDATE_FILE",
                path=plan.files[0].path if plan.files else "README.md",
                content=f"# Fix applied\n\n{debug_result.fix}\n",
            )
        ]

    def apply_actions(
        self, workspace_path: str, actions: list[CodeAction]
    ) -> list[str]:
        """Apply validated actions only within an assigned project workspace."""
        for action in actions:
            validate_relative_path(workspace_path, action.path)

        changed_files: list[str] = []
        for action in actions:
            if action.action == "CREATE_FILE":
                create_file(workspace_path, action.path, action.content or "")
            elif action.action == "UPDATE_FILE":
                update_file(workspace_path, action.path, action.content or "")
            elif action.action == "DELETE_FILE":
                delete_file(workspace_path, action.path)
            changed_files.append(action.path)
        return changed_files
