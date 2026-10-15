from problem_discovery_agents.observability import summarize_usages
from problem_discovery_agents.flow import UsageCapturingAgent


def test_usage_totals_require_complete_metadata() -> None:
    summary = summarize_usages([
        {"input_tokens": 2, "output_tokens": 3, "cost_usd": 0.1},
        {"input_tokens": 5, "output_tokens": 7, "cost_usd": 0.2},
    ])
    assert summary["totals"]["input_tokens"] == 7
    assert summary["totals"]["estimated_model_cost_usd"] == 0.30000000000000004
    partial = summarize_usages([{"input_tokens": 2}, {}])
    assert partial["totals"]["input_tokens"] is None
    assert partial["complete"]["input_tokens"] is False


def test_usage_proxy_preserves_kickoff_result_and_metadata() -> None:
    class Result:
        usage_metrics = {"input_tokens": 2}
    class Agent:
        def kickoff(self, value, **kwargs):
            assert value == "request"
            assert kwargs == {"response_format": str}
            return Result()
    captured: list[object] = []
    result = UsageCapturingAgent(Agent(), captured).kickoff("request", response_format=str)
    assert isinstance(result, Result)
    assert captured == [{"input_tokens": 2}]
