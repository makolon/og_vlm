import json
import os
from typing import List, Optional, Tuple, Any

from pydantic import BaseModel, Field

from .prompt_templates import SYSTEM_TEMPLATE, USER_TEMPLATE


class PlanStep(BaseModel):
    op: str
    target: Optional[str] = None
    object: Optional[str] = None
    receptacle: Optional[str] = None


class Plan(BaseModel):
    plan: List[PlanStep] = Field(default_factory=list)


def _build_prompt(activity: str, catalog: List[str], notes: str) -> Tuple[str, str]:
    system = SYSTEM_TEMPLATE
    user = USER_TEMPLATE.format(activity=activity, catalog=", ".join(sorted(set(catalog))[:40]), notes=notes or "None")
    return system, user


def _attach_image_openai(content: List[dict], image_b64: Optional[str]):
    if image_b64:
        content.append(
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Latest RGB observation."},
                    {"type": "input_image", "image_url": f"data:image/png;base64,{image_b64}"},
                ],
            }
        )


class OpenAIPlanner:
    """
    OpenAI Responses API client for GPT-5 (multimodal).

    Requires:
        pip install openai>=1.40
        export OPENAI_API_KEY=...
    """
    def __init__(self, model: str = "gpt-5", temperature: float = 0.1):
        from openai import OpenAI
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature

    def plan(self, activity: str, catalog: List[str], notes: str = "", image_b64: Optional[str] = None) -> Plan:
        system, user = _build_prompt(activity, catalog, notes)

        content = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        _attach_image_openai(content, image_b64)

        resp = self.client.responses.create(
            model=self.model,
            input=content,
            temperature=self.temperature,
            text={"format": {"type": "json_object"}},
        )
        txt = resp.output_text
        data = json.loads(txt)
        return Plan(**data)


class GeminiPlanner:
    """
    Google GenAI SDK client for Gemini 2.5 Pro (multimodal).

    Requires:
        pip install google-genai
        export GEMINI_API_KEY=...
    """
    def __init__(self, model: str = "gemini-2.5-pro", temperature: float = 0.1):
        import genai
        from genai import Client, types

        # google-genai uses GEMINI_API_KEY (Developer API) by default
        self.client = Client(api_key=os.environ.get("GEMINI_API_KEY"))
        self.model = model
        self.temperature = temperature
        self._types = types

    def plan(self, activity: str, catalog: List[str], notes: str = "", image_b64: Optional[str] = None) -> Plan:
        system, user = _build_prompt(activity, catalog, notes)

        parts: List[Any] = [self._types.Part.from_text(system + "\n\n" + user)]
        if image_b64:
            parts.append(self._types.Part.from_bytes(b64_data=image_b64, mime_type="image/png"))

        resp = self.client.models.generate_content(
            model=self.model,
            contents=parts,
            config=self._types.GenerateContentConfig(temperature=self.temperature, response_mime_type="application/json"),
        )
        txt = resp.text
        data = json.loads(txt)
        return Plan(**data)


def get_planner(provider: str, model: str, temperature: float = 0.1):
    provider = provider.lower()
    if provider == "openai":
        return OpenAIPlanner(model=model, temperature=temperature)
    elif provider == "gemini":
        return GeminiPlanner(model=model, temperature=temperature)
    else:
        raise ValueError(f"Unknown provider: {provider}")
