default: test


install:
	pip install -r requirements.txt
	pip install ruff mypy black pytest
	pip install bandit semgrep evals

test:
	ruff check --fix .
	mypy src/
	black --check .
	bandit -r src -ll
	semgrep --config=auto
	pytest