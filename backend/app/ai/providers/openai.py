"""LangChain-backed OpenAI provider."""

from __future__ import annotations

from typing import Any, Protocol

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, ConfigDict

from app.ai.providers.base import (
    AIResult,
    ProviderError,
    ProviderRequest,
    SummaryProviderRequest,
    SummaryResult,
)


class _OpenAIResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str
    structured_payload: dict[str, Any] | None = None


class _OpenAISummaryResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_summary: str
    recommended_treatments: list[str]
    recommendation_rationale: str | None = None


class _Invokable(Protocol):
    def invoke(self, input: object) -> object: ...


class OpenAIProvider:
    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        timeout_seconds: float = 30.0,
        max_retries: int = 1,
        chat_model: Any | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("OpenAI API key is required")
        if not model.strip():
            raise ValueError("OpenAI model is required")
        base_model = chat_model or ChatOpenAI(
            api_key=api_key,
            model=model,
            timeout=timeout_seconds,
            max_retries=max_retries,
        )
        self._chain: _Invokable = base_model.with_structured_output(
            _OpenAIResponse,
            method="function_calling",
        )
        self._summary_chain: _Invokable = base_model.with_structured_output(
            _OpenAISummaryResponse,
            method="function_calling",
        )

    def generate(self, request: ProviderRequest) -> AIResult:
        messages: list[object] = [SystemMessage(content=request.system_instruction)]
        for message in request.messages:
            message_type = HumanMessage if message.role == "USER" else AIMessage
            messages.append(message_type(content=message.content))

        try:
            raw_response = self._chain.invoke(messages)
            response = (
                raw_response
                if isinstance(raw_response, _OpenAIResponse)
                else _OpenAIResponse.model_validate(raw_response)
            )
            return AIResult(response.content, response.structured_payload)
        except Exception as exc:
            raise ProviderError("OpenAI generation failed") from exc

    def generate_summary(self, request: SummaryProviderRequest) -> SummaryResult:
        messages: list[object] = [SystemMessage(content=request.system_instruction)]
        for message in request.messages:
            message_type = HumanMessage if message.role == "USER" else AIMessage
            messages.append(message_type(content=message.content))

        try:
            raw_response = self._summary_chain.invoke(messages)
            response = (
                raw_response
                if isinstance(raw_response, _OpenAISummaryResponse)
                else _OpenAISummaryResponse.model_validate(raw_response)
            )
            return SummaryResult(
                response.patient_summary,
                response.recommended_treatments,
                response.recommendation_rationale,
            )
        except Exception as exc:
            raise ProviderError("OpenAI summary generation failed") from exc
