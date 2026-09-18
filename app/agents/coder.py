from __future__ import annotations

from app.models.provider import ModelProvider
from app.models.schemas import CodeAction, DebugResult, ImplementationPlan
from app.tools.file_tools import create_file, delete_file, update_file


class CoderAgent:
    def __init__(self, provider: ModelProvider) -> None:
        self.provider = provider

    async def generate_actions(self, plan: ImplementationPlan) -> list[CodeAction]:
        fallback = {
            "actions": [
                CodeAction(action="create_file", path=path, content="").model_dump()
                for path in plan.files
            ]
        }
        payload = await self.provider.generate_structured_response(
            prompt=f"Generate code actions for files: {plan.files}",
            schema_name="code_actions",
            fallback=fallback,
        )
        return [CodeAction.model_validate(item) for item in payload.get("actions", [])]

    async def generate_fix_actions(
        self, debug_result: DebugResult, plan: ImplementationPlan
    ) -> list[CodeAction]:
        return [
            CodeAction(
                action="update_file",
                path=plan.files[0] if plan.files else "README.md",
                content=f"# Fix applied\n\n{debug_result.fix}\n",
            )
        ]

    def apply_actions(self, workspace_path: str, actions: list[CodeAction]) -> None:
        for action in actions:
            if action.action == "create_file":
                create_file(workspace_path, action.path, action.content or "")
            elif action.action == "update_file":
                target = action.content or ""
                try:
                    update_file(workspace_path, action.path, target)
                except FileNotFoundError:
                    create_file(workspace_path, action.path, target)
            elif action.action == "delete_file":
                delete_file(workspace_path, action.path)
