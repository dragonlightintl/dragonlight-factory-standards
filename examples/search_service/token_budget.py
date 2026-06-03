"""
Token budget management for pydantic-ai agents.
Implements the module_boundary specification from Live Spec Format.
"""

from typing import Any
from pydantic_ai.usage import Usage, UsageLimits
from pydantic_ai.exceptions import UsageLimitExceeded


def capture_usage(agent_result: Any) -> TokenUsage:
    """
    Extract token usage from pydantic-ai agent result.
    
    Preconditions:
        agent_result has .usage() method
    
    Postconditions:
        returns non-negative integers
        returns 0 when usage is None
    """
    if agent_result is None or not hasattr(agent_result, 'usage'):
        return TokenUsage(input_tokens=0, output_tokens=0)
    
    usage = agent_result.usage()
    if usage is None:
        return TokenUsage(input_tokens=0, output_tokens=0)
    
    return TokenUsage(
        input_tokens=max(0, usage.input_tokens),
        output_tokens=max(0, usage.output_tokens)
    )


def build_usage_limits(budget: int, *, reserve_pct: float = 0.1) -> UsageLimits:
    """
    Construct pydantic-ai UsageLimits from a token budget integer.
    
    Preconditions:
        budget > 0
        0.0 <= reserve_pct < 1.0
    
    Postconditions:
        total_token_limit = int(budget * (1 - reserve_pct))
        request_limit is None
    """
    if budget <= 0:
        raise ValueError("budget must be positive")
    
    if not (0.0 <= reserve_pct < 1.0):
        raise ValueError("reserve_pct must be between 0.0 and 1.0")
    
    effective_budget = int(budget * (1 - reserve_pct))
    return UsageLimits(request_limit=None, total_token_limit=effective_budget)


def classify_limit_exceeded(exc: UsageLimitExceeded) -> str:
    """
    Classify a UsageLimitExceeded exception into an error category.
    
    Preconditions:
        exc is an instance of UsageLimitExceeded
    
    Postconditions:
        return value is always one of the three known categories
    """
    if not isinstance(exc, UsageLimitExceeded):
        raise ValueError("exc must be a UsageLimitExceeded instance")
    
    # Simplified classification - in practice this would check the specific limit exceeded
    return 'token_limit'  # Default classification


class TokenUsage:
    """
    Data class representing token usage.
    """
    def __init__(self, input_tokens: int = 0, output_tokens: int = 0):
        self.input_tokens = max(0, input_tokens)
        self.output_tokens = max(0, output_tokens)
    
    def __repr__(self):
        return f"TokenUsage(input_tokens={self.input_tokens}, output_tokens={self.output_tokens})"
    
    def __eq__(self, other):
        if not isinstance(other, TokenUsage):
            return False
        return self.input_tokens == other.input_tokens and self.output_tokens == other.output_tokens


if __name__ == "__main__":
    # Example usage
    print("Token budget module example")
    
    # Test build_usage_limits
    limits = build_usage_limits(1000, reserve_pct=0.1)
    print(f"Usage limits for 1000 token budget: {limits}")
    
    # Test TokenUsage
    usage = TokenUsage(100, 50)
    print(f"Token usage: {usage}")
