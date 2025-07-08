import sys, os; sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..")))
from asga_contracts import FeatureRequest, Spec, Tests, Patch, Critique, RepairPlan
import dspy


def test_signature_types():
    for cls in [FeatureRequest, Spec, Tests, Patch, Critique, RepairPlan]:
        assert issubclass(cls, dspy.Signature)
        # ensure JSON schema generation works
        schema = cls.schema_json()
        assert "properties" in schema
