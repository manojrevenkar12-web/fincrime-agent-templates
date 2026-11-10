"""Nothing that serves reads the truth: the agent, the store and the API never import the world, the
simulated provider or the evaluation, and never name the truth."""

import ast
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src" / "fat"
SERVING = [*(SRC / "agent").glob("*.py"), SRC / "store.py", SRC / "api.py"]
FORBIDDEN = ("world", "sim", "evals")


def test_serving_code_imports_no_truth_side_module():
    for path in SERVING:
        tree = ast.parse(path.read_text())
        for fn in ast.walk(tree):
            if isinstance(fn, ast.FunctionDef) and fn.name == "demo_app":
                fn.body = []  # the demo wiring injects the simulated provider; nothing else may
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                parts = (node.module or "").split(".")
                assert not set(parts) & set(FORBIDDEN), f"{path.name} imports {node.module}"


def test_serving_code_never_names_the_truth():
    for path in SERVING:
        code = path.read_text()
        code = code.split("def demo_app")[0]
        for word in ("data/truth", '"truth"', "world.json", "list_facts", "is_match"):
            assert word not in code, f"{path.name} mentions {word}"
