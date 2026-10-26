.PHONY: test bench artifacts eval report api web build-web

test:
	python -m pytest -q

bench:
	python bench.py

artifacts:
	python -m ml.build_artifacts

eval:
	python -m ml.evaluation --seed 42

report:
	python -m ml.report

api:
	python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000

web:
	cd apps/web && npm run dev

build-web:
	cd apps/web && npm run build
