import dspy

class FeatureRequest(dspy.Signature):
    """User feature request."""
    user_story: str = dspy.OutputField(desc="End-user story")

class Spec(dspy.Signature):
    """API specification."""
    endpoint: str = dspy.OutputField(desc="HTTP endpoint")
    method: str = dspy.OutputField(desc="HTTP method")
    request_schema: str = dspy.OutputField(desc="Request JSON schema")
    response_schema: str = dspy.OutputField(desc="Response JSON schema")

class Tests(dspy.Signature):
    """Unit tests code."""
    code: str = dspy.OutputField(desc="Test source code")

class Patch(dspy.Signature):
    """Git patch."""
    diff: str = dspy.OutputField(desc="Unified diff")

class Critique(dspy.Signature):
    """Review feedback."""
    score: float = dspy.OutputField(desc="Rating from 0 to 1")
    feedback: str = dspy.OutputField(desc="Reviewer comments")

class RepairPlan(dspy.Signature):
    """Fix plan."""
    steps: list[str] = dspy.OutputField(desc="Ordered remediation steps")
