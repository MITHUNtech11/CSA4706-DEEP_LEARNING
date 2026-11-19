"""
Versioned System Prompt Renderer.
Injects verified server-side identity attributes and establishes untrusted context boundaries.
"""

from pathlib import Path
from typing import Dict, Any, List
import jinja2
from src.config import PROMPT_TEMPLATE_PATH


class PromptRenderer:
    def __init__(self, template_path: Path = PROMPT_TEMPLATE_PATH):
        self.template_path = template_path
        self.template_version = "v1"
        self._load_template()

    def _load_template(self):
        with open(self.template_path, "r", encoding="utf-8") as f:
            template_str = f.read()
        self.jinja_template = jinja2.Template(template_str)

    def render(
        self,
        role_name: str,
        role_level: int,
        allowed_categories: List[str],
        patient_scope: str,
        retrieved_context: str,
        user_query: str
    ) -> str:
        """
        Renders system prompt with server-side verified attributes.
        Retrieved context is explicitly wrapped as untrusted data.
        """
        categories_str = ", ".join(allowed_categories) if allowed_categories else "NONE (ACCESS RESTRICTED)"
        return self.jinja_template.render(
            ROLE_NAME=role_name,
            ROLE_LEVEL=role_level,
            ALLOWED_CATEGORIES=categories_str,
            PATIENT_SCOPE=patient_scope,
            RETRIEVED_CONTEXT=retrieved_context if retrieved_context.strip() else "[NO DOCUMENTS RETRIEVED - OUT OF SCOPE]",
            USER_QUERY=user_query
        )
