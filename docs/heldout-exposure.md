# What I saw of the held-out data before the single run

- While generating the world I printed aggregate counts per customer over all eight months, Northbank included:
  screenings, provider alerts, true matches, and the split of ideal dispositions for alerts and media hits.
  No record, alert or article of Northbank, or of months 7-8, was looked at individually.
- Northbank's configuration (`config/customers/northbank.toml`) was written from its data dictionary and policy
  document only, as a forward-deployed engineer would receive them, before the template ran on any of its data.
- The template, its thresholds' grid, the guards and the model routing were built and measured on months 1-6 of
  Finvia, Ledgerly and Kreditwerk.
