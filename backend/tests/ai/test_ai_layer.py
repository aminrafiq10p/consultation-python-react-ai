from unittest.mock import ANY, Mock

import pytest

from app.ai.consultation_agent import ConsultationAgent
from app.ai.consultation_skill import ConsultationSkill
from app.ai.providers.base import (
    AIResult,
    ConsultationContext,
    ConversationMessage,
    ProviderError,
)
from app.ai.providers.mock import MockAIProvider
from app.ai.providers.openai import OpenAIProvider
from app.ai.service import (
    AIConfigurationError,
    AIService,
    AIServiceError,
    create_ai_service,
)


@pytest.fixture
def context() -> ConsultationContext:
    return ConsultationContext(
        consultation_id="consultation-1",
        primary_concern="Recurring headache",
        display_fields={"preferred_name": "Sam"},
    )


@pytest.fixture
def messages() -> tuple[ConversationMessage, ...]:
    return (
        ConversationMessage("USER", "The pain began yesterday."),
        ConversationMessage("ASSISTANT", "Can you describe its location?"),
        ConversationMessage("USER", "It is behind my eyes."),
    )


def test_mock_provider_is_deterministic_and_network_free(context, messages):
    provider = MockAIProvider()

    first = provider.generate(_request(context, messages))
    second = provider.generate(_request(context, messages))

    assert first == second
    assert first.content == "I understand your concern: It is behind my eyes."
    assert first.structured_payload == {"provider": "mock", "message_count": 3}


def test_service_coordinates_exactly_one_agent_call(context, messages):
    agent = Mock()
    agent.respond.return_value = AIResult("A useful response")

    result = AIService(agent).generate_response(context, messages)

    assert result == AIResult("A useful response")
    agent.respond.assert_called_once_with(context, messages)


def test_agent_forwards_ordered_context_and_skill_instructions(context, messages):
    provider = Mock()
    provider.generate.return_value = AIResult("Response", {"topics": ["pain", "timing"]})
    skill = Mock(spec=ConsultationSkill)
    skill.instructions_for.return_value = "focused instructions"

    result = ConsultationAgent(provider, skill).respond(context, messages)

    request = provider.generate.call_args.args[0]
    assert tuple(request.messages) == messages
    assert request.consultation_context is context
    assert request.system_instruction == "focused instructions"
    assert result.structured_payload == {"topics": ["pain", "timing"]}
    skill.instructions_for.assert_called_once_with(context)
    provider.generate.assert_called_once()


@pytest.mark.parametrize(
    "content,payload",
    [
        (" ", None),
        ("valid text", ["not", "an", "object"]),
        ("valid text", {"nested": {"not": "allowed"}}),
        ("valid text", {"nested": [["not allowed"]]}),
        ("valid text", {"number": float("nan")}),
    ],
)
def test_blank_or_malformed_results_are_rejected(content, payload):
    with pytest.raises(ValueError):
        AIResult(content, payload)


def test_service_translates_provider_failure_without_leaking_details(context, messages):
    agent = Mock()
    agent.respond.side_effect = ProviderError("secret provider detail")

    with pytest.raises(AIServiceError) as error:
        AIService(agent).generate_response(context, messages)

    assert str(error.value) == "Assistant response is temporarily unavailable"
    assert error.value.__cause__ is None


def test_skill_forbids_business_mutation_and_definitive_diagnosis(context):
    instructions = ConsultationSkill().instructions_for(context).lower()

    assert "do not claim" in instructions
    assert "booked" in instructions
    assert "consultation status" in instructions
    assert "definitive medical diagnosis" in instructions
    assert "structured" in instructions


def test_provider_values_have_no_flask_sqlalchemy_or_persistence_dependency():
    import app.ai.consultation_agent as agent_module
    import app.ai.consultation_skill as skill_module
    import app.ai.providers.base as base_module
    import app.ai.service as service_module

    source_names = " ".join(
        module.__dict__.get("__file__", "")
        for module in (agent_module, skill_module, base_module, service_module)
    )
    assert "flask" not in source_names.lower()
    assert "sqlalchemy" not in source_names.lower()
    assert not hasattr(AIService, "persist")


def test_configuration_selects_mock_and_rejects_invalid_configuration():
    assert isinstance(create_ai_service({"AI_PROVIDER": "mock"}), AIService)

    with pytest.raises(AIConfigurationError):
        create_ai_service({"AI_PROVIDER": "openai"})
    with pytest.raises(AIConfigurationError):
        create_ai_service({"AI_PROVIDER": "unknown"})


def test_openai_composition_centralizes_model_timeout_and_retry(monkeypatch):
    import app.ai.service as service_module

    provider = Mock()
    provider_type = Mock(return_value=provider)
    monkeypatch.setattr(service_module, "OpenAIProvider", provider_type)

    service = service_module.create_ai_service(
        {
            "AI_PROVIDER": "openai",
            "OPENAI_API_KEY": "server-only-key",
            "OPENAI_MODEL": "configured-model",
        }
    )

    assert isinstance(service, AIService)
    provider_type.assert_called_once_with(
        api_key="server-only-key",
        model="configured-model",
        timeout_seconds=30.0,
        max_retries=1,
    )


def test_openai_provider_uses_langchain_messages_without_network(context, messages):
    structured_chain = Mock()
    structured_chain.invoke.return_value = {
        "content": "Consider tracking when symptoms occur.",
        "structured_payload": {"topics": ["timing", "triggers"]},
    }
    chat_model = Mock()
    chat_model.with_structured_output.return_value = structured_chain
    provider = OpenAIProvider(
        api_key="test-key",
        model="test-model",
        chat_model=chat_model,
    )

    result = provider.generate(_request(context, messages))

    assert result.content == "Consider tracking when symptoms occur."
    assert result.structured_payload == {"topics": ["timing", "triggers"]}
    chat_model.with_structured_output.assert_called_once_with(
        ANY,
        method="function_calling",
    )
    sent_messages = structured_chain.invoke.call_args.args[0]
    assert [message.content for message in sent_messages[1:]] == [
        message.content for message in messages
    ]


def test_openai_provider_sanitizes_parser_or_boundary_failure(context, messages):
    structured_chain = Mock()
    structured_chain.invoke.side_effect = RuntimeError("raw SDK detail")
    chat_model = Mock()
    chat_model.with_structured_output.return_value = structured_chain
    provider = OpenAIProvider(api_key="test-key", model="test-model", chat_model=chat_model)

    with pytest.raises(ProviderError) as error:
        provider.generate(_request(context, messages))

    assert str(error.value) == "OpenAI generation failed"


def _request(context, messages):
    from app.ai.providers.base import ProviderRequest

    return ProviderRequest("instructions", context, messages)
