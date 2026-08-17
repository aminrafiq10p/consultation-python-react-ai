from unittest.mock import ANY, Mock

import pytest

from app.ai.consultation_agent import ConsultationAgent
from app.ai.consultation_skill import ConsultationSkill
from app.ai.providers.base import (
    AIResult,
    ConsultationContext,
    ConversationMessage,
    ProviderError,
    SummaryProviderRequest,
    SummaryResult,
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


def test_service_coordinates_exactly_one_summary_agent_call(context, messages):
    agent = Mock()
    agent.summarize.return_value = SummaryResult(
        " Patient report ", [" First treatment ", "Second treatment"], " Why "
    )

    result = AIService(agent).generate_summary(context, messages)

    assert result == SummaryResult(
        "Patient report", ("First treatment", "Second treatment"), "Why"
    )
    agent.summarize.assert_called_once_with(context, messages)


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


def test_agent_forwards_full_ordered_messages_to_summary_skill_and_provider(
    context, messages
):
    full_history = messages + tuple(
        ConversationMessage("ASSISTANT" if index % 2 else "USER", f"message-{index}")
        for index in range(20)
    )
    provider = Mock()
    provider.generate_summary.return_value = SummaryResult("Summary", ["Treatment"])
    skill = Mock(spec=ConsultationSkill)
    skill.summary_instructions_for.return_value = "summary instructions"

    result = ConsultationAgent(provider, skill).summarize(context, full_history)

    request = provider.generate_summary.call_args.args[0]
    assert isinstance(request, SummaryProviderRequest)
    assert tuple(request.messages) == full_history
    assert request.consultation_context is context
    assert request.system_instruction == "summary instructions"
    assert result == SummaryResult("Summary", ["Treatment"])
    skill.summary_instructions_for.assert_called_once_with(context)
    provider.generate_summary.assert_called_once()


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


def test_summary_result_normalizes_values_and_preserves_treatment_order():
    result = SummaryResult(
        "  Patient-reported concern.  ",
        ["  Treatment B  ", "Treatment A"],
        "  Concise explanation.  ",
    )

    assert result.patient_summary == "Patient-reported concern."
    assert result.recommended_treatments == ("Treatment B", "Treatment A")
    assert result.recommendation_rationale == "Concise explanation."


@pytest.mark.parametrize("patient_summary", ["", "   ", None, 3])
def test_summary_result_rejects_malformed_or_blank_patient_summary(patient_summary):
    with pytest.raises(ValueError):
        SummaryResult(patient_summary, ["Treatment"])


@pytest.mark.parametrize("treatments", [[], (), "Treatment", None])
def test_summary_result_rejects_empty_or_invalid_treatment_collection(treatments):
    with pytest.raises(ValueError):
        SummaryResult("Summary", treatments)


@pytest.mark.parametrize(
    "treatments", [[""], ["  "], ["Valid", ""], ["Valid", None], [3]]
)
def test_summary_result_rejects_invalid_treatments(treatments):
    with pytest.raises(ValueError):
        SummaryResult("Summary", treatments)


@pytest.mark.parametrize("rationale", ["", "   ", 3])
def test_summary_result_rejects_blank_or_invalid_rationale(rationale):
    with pytest.raises(ValueError):
        SummaryResult("Summary", ["Treatment"], rationale)


def test_summary_result_keeps_absent_rationale_as_none():
    assert SummaryResult("Summary", ["Treatment"]).recommendation_rationale is None


def test_service_translates_provider_failure_without_leaking_details(context, messages):
    agent = Mock()
    agent.respond.side_effect = ProviderError("secret provider detail")

    with pytest.raises(AIServiceError) as error:
        AIService(agent).generate_response(context, messages)

    assert str(error.value) == "Assistant response is temporarily unavailable"
    assert error.value.__cause__ is None


@pytest.mark.parametrize(
    "failure",
    [ProviderError("secret provider detail"), ValueError("malformed secret output")],
)
def test_summary_service_sanitizes_provider_and_validation_failures(
    context, messages, failure
):
    agent = Mock()
    agent.summarize.side_effect = failure

    with pytest.raises(AIServiceError) as error:
        AIService(agent).generate_summary(context, messages)

    assert str(error.value) == "Consultation summary is temporarily unavailable"
    assert error.value.__cause__ is None


def test_skill_forbids_business_mutation_and_definitive_diagnosis(context):
    instructions = ConsultationSkill().instructions_for(context).lower()

    assert "do not claim" in instructions
    assert "booked" in instructions
    assert "consultation status" in instructions
    assert "definitive medical diagnosis" in instructions
    assert "structured" in instructions


def test_summary_skill_has_grounding_output_and_safety_instructions(context):
    instructions = ConsultationSkill().summary_instructions_for(context).lower()

    for phrase in (
        "complete ordered persisted conversation",
        "patient-reported",
        "non-diagnostic",
        "plain-text patient summary",
        "one or more",
        "concise, user-facing",
        "chain-of-thought",
        "never claim an appointment was booked",
        "never change consultation status",
        "perform persistence",
    ):
        assert phrase in instructions


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
    response_chain = Mock()
    response_chain.invoke.return_value = {
        "content": "Consider tracking when symptoms occur.",
        "structured_payload": {"topics": ["timing", "triggers"]},
    }
    summary_chain = Mock()
    chat_model = Mock()
    chat_model.with_structured_output.side_effect = [response_chain, summary_chain]
    provider = OpenAIProvider(
        api_key="test-key",
        model="test-model",
        chat_model=chat_model,
    )

    result = provider.generate(_request(context, messages))

    assert result.content == "Consider tracking when symptoms occur."
    assert result.structured_payload == {"topics": ["timing", "triggers"]}
    assert chat_model.with_structured_output.call_count == 2
    chat_model.with_structured_output.assert_any_call(ANY, method="function_calling")
    sent_messages = response_chain.invoke.call_args.args[0]
    assert [message.content for message in sent_messages[1:]] == [
        message.content for message in messages
    ]


def test_openai_provider_sanitizes_parser_or_boundary_failure(context, messages):
    response_chain = Mock()
    response_chain.invoke.side_effect = RuntimeError("raw SDK detail")
    summary_chain = Mock()
    chat_model = Mock()
    chat_model.with_structured_output.side_effect = [response_chain, summary_chain]
    provider = OpenAIProvider(api_key="test-key", model="test-model", chat_model=chat_model)

    with pytest.raises(ProviderError) as error:
        provider.generate(_request(context, messages))

    assert str(error.value) == "OpenAI generation failed"


def test_openai_summary_structured_output_mapping_without_network(context, messages):
    response_chain = Mock()
    summary_chain = Mock()
    summary_chain.invoke.return_value = {
        "patient_summary": "  The patient reported recurring headaches. ",
        "recommended_treatments": [" Track symptoms ", "Seek clinical review"],
        "recommendation_rationale": "  These steps support further assessment. ",
    }
    chat_model = Mock()
    chat_model.with_structured_output.side_effect = [response_chain, summary_chain]
    provider = OpenAIProvider(api_key="test-key", model="test-model", chat_model=chat_model)

    result = provider.generate_summary(_summary_request(context, messages))

    assert result == SummaryResult(
        "The patient reported recurring headaches.",
        ("Track symptoms", "Seek clinical review"),
        "These steps support further assessment.",
    )
    sent_messages = summary_chain.invoke.call_args.args[0]
    assert [message.content for message in sent_messages[1:]] == [
        message.content for message in messages
    ]


@pytest.mark.parametrize(
    "raw_response",
    [
        {"patient_summary": "", "recommended_treatments": ["Treatment"]},
        {"patient_summary": "Summary", "recommended_treatments": []},
        {"patient_summary": "Summary", "recommended_treatments": [" "]},
        {
            "patient_summary": "Summary",
            "recommended_treatments": ["Treatment"],
            "unexpected": "field",
        },
    ],
)
def test_openai_summary_sanitizes_malformed_structured_output(
    context, messages, raw_response
):
    response_chain = Mock()
    summary_chain = Mock()
    summary_chain.invoke.return_value = raw_response
    chat_model = Mock()
    chat_model.with_structured_output.side_effect = [response_chain, summary_chain]
    provider = OpenAIProvider(api_key="test-key", model="test-model", chat_model=chat_model)

    with pytest.raises(ProviderError) as error:
        provider.generate_summary(_summary_request(context, messages))

    assert str(error.value) == "OpenAI summary generation failed"


def test_mock_summary_is_deterministic_and_uses_all_user_messages(context, messages):
    provider = MockAIProvider()

    first = provider.generate_summary(_summary_request(context, messages))
    second = provider.generate_summary(_summary_request(context, messages))

    assert first == second
    assert first.patient_summary == (
        "The patient reported: The pain began yesterday.; It is behind my eyes."
    )
    assert len(first.recommended_treatments) == 1


def _request(context, messages):
    from app.ai.providers.base import ProviderRequest

    return ProviderRequest("instructions", context, messages)


def _summary_request(context, messages):
    return SummaryProviderRequest("summary instructions", context, messages)
