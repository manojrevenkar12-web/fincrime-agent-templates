PY ?= python3
export PYTHONPATH := src

.PHONY: world tiers activate test eval gate heldout report web check

world:     ## regenerate the world (changes the held-out pin: only before it was taken)
	$(PY) scripts/build_world.py
tiers:     ## measure model tiers on development history -> config/routing.json
	$(PY) -m fat.evals.tiering
activate:  ## activation of the development customers -> config/activations, reports/activation*.json
	$(PY) scripts/activate.py finvia ledgerly kreditwerk
	$(PY) scripts/activate.py --generic finvia ledgerly kreditwerk
test:
	$(PY) -m pytest -q
eval:      ## every design on months 1-6 of the development customers -> reports/dev.json
	$(PY) scripts/evaluate.py
gate:      ## CI: exits 1 if the candidate fails the gate on development months
	$(PY) scripts/gate.py
heldout:   ## once: activate Northbank, then months 7-8 of all customers -> reports/heldout.json
	$(PY) scripts/heldout.py
report:
	$(PY) scripts/report.py
web:
	cd web && npm ci && npm test && npm run build
check: test gate
