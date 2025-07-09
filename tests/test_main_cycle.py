from pathlib import Path

from git import Repo
from main_cycle import git_clone_or_pull, plan_changes
from graph import workflow
from generated.contracts.v1 import contracts_pb2 as pb


def test_git_clone_or_pull(tmp_path):
    remote = Repo.init(tmp_path / "remote")
    (tmp_path / "remote" / "file.txt").write_text("first")
    remote.index.add(["file.txt"])
    remote.index.commit("init")

    clone_path = tmp_path / "clone"
    repo = git_clone_or_pull(remote.working_tree_dir, str(clone_path))
    assert (clone_path / "file.txt").exists()

    # add second commit to remote and ensure pull updates clone
    (Path(remote.working_tree_dir) / "file2.txt").write_text("second")
    remote.index.add(["file2.txt"])
    remote.index.commit("second")

    repo = git_clone_or_pull(remote.working_tree_dir, str(clone_path))
    assert (clone_path / "file2.txt").exists()
    assert repo.head.commit.hexsha == remote.head.commit.hexsha


def test_plan_changes_tags(tmp_path):
    plan = plan_changes(str(tmp_path))
    assert "refactor:" in plan
    assert "feature:" in plan


def test_optimise_simba_trigger(monkeypatch):
    called = False

    def critic_fail(state: workflow.WorkflowState):
        with workflow.tracer.start_as_current_span("critic_agent"):
            return {"critique": pb.Critique(score=0.5, feedback="bad")}

    def optimise_stub(state: workflow.WorkflowState):
        nonlocal called
        called = True
        with workflow.tracer.start_as_current_span("optimise_simba"):
            attempt = state.get("attempts", 0) + 1
            return {"repair_plan": pb.RepairPlan(steps=["fix"]), "attempts": attempt}

    monkeypatch.setattr(workflow, "critic_node", critic_fail)
    monkeypatch.setattr(workflow, "optimise_simba", optimise_stub)
    graph = workflow.create_graph()
    graph.invoke({"feature_request": pb.FeatureRequest(user_story="hi")})
    assert called
