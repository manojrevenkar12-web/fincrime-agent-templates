# Working on fincrime-agent-templates

## Fast feedback

| What | Command | Time |
|---|---|---|
| Lint and format | `ruff check src tests scripts && ruff format --check src tests scripts` | ~1 s |
| Tests | `make test` | ~1 s |
| Activation of the development customers | `make activate` | ~2 s |
| Every design on the development months | `make eval` | ~4 s |
| Gate | `make gate` | ~4 s |
| Dashboard | `cd web && npm test && npm run dev` | ~3 s |

## Invariants

1. **Nothing that serves reads the truth.** `src/fat/agent`, `store.py` and `api.py` never import `fat.world`,
   `fat.sim` or `fat.evals` and never name `data/truth`; `tests/test_isolation.py` checks it. Only `demo_app`
   wires in the simulated provider.
2. **Code decides, the model reads.** Identifiers in structured fields are compared by code. A value a model
   reports counts only with a quote that is in the text and contains it. Attribution of an article and every
   closure are decided by code under the customer's policy.
3. **Retrieved text is data.** Remarks and articles reach a model only in untrusted blocks, with
   instruction-like sentences held back. Never put retrieved text in a system prompt.
4. **One template, configuration per customer.** Customer differences live in `config/customers/<id>.toml`,
   written from the customer's dictionary and policy. Template code never branches on a customer id.
5. **Activation before live.** A customer is served only with a live activation (mapping check, backtest,
   shadow month, gate) from its own history.
6. **The gate decides.** No true match closed, nothing closed against policy, no obeyed instruction, no missed
   finding. Limits live in `[gate]`; they are not loosened to make a design pass.
7. **Settings in config, generated reports.** Weights, tiers, guards, limits in `config/fat.toml`; dashboard
   constants in `web/src/shared/theme/tokens.ts`; `reports/` and `web/public/data` come from scripts.

## The held-out rule

The world (lists, media, four customers, truth) was generated and pinned in `config/heldout.lock` before any
agent code existed. Northbank and months 7-8 are held out. `scripts/heldout.py` refuses to run if the data
changed, if code or config are not committed, or if it has run before. Problems it shows are published and fixed
with tests on development data; it is not run again. Record what you see of held-out data in
`docs/heldout-exposure.md`.
