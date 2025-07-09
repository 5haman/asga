from dataclasses import dataclass, field
from typing import List

@dataclass
class FeatureRequest:
    user_story: str

@dataclass
class Spec:
    endpoint: str
    method: str
    request_schema: str
    response_schema: str

@dataclass
class Tests:
    code: str

@dataclass
class Patch:
    diff: str

@dataclass
class Critique:
    score: float
    feedback: str

@dataclass
class RepairPlan:
    steps: List[str] = field(default_factory=list)
