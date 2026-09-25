"""The one place the model is called."""

from datetime import date

from openai import OpenAI

from app.ask.router import RouterDecision, build_system_prompt, build_user_message
from app.core.config import settings


class OpenAIRouter:
    def __init__(self, client: OpenAI | None = None, model: str | None = None):
        self._client = client or OpenAI(api_key=settings.OPENAI_API_KEY)
        self._model = model or settings.ASK_MODEL

    def decide(
        self,
        question: str,
        previous: RouterDecision | None,
        today: date,
        previous_question: str | None = None,
    ) -> RouterDecision:
        # The system prompt is identical for every question on a given day,
        # so it is served from the provider's prompt cache after the first.
        completion = self._client.chat.completions.parse(
            model=self._model,
            messages=[
                {"role": "system", "content": build_system_prompt(today)},
                {
                    "role": "user",
                    "content": build_user_message(question, previous, previous_question),
                },
            ],
            response_format=RouterDecision,
        )
        decision = completion.choices[0].message.parsed
        if decision is None:
            raise RuntimeError("The model returned no decision")
        return decision
