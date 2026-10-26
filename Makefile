.PHONY: test bench artifacts eval report api

test:
	python -m pytest -v -q

bench:
	python bench.py

artifacts:
	python -m ml.build_artifacts

eval:
	python -m ml.evaluation --seed 42

report:
	python -m ml.report

api:
	uvicorn apps.api.main:app --host 0.0.0.0 --port 8000 --reload
