import { useState } from "react";
import { ActivationTable } from "../features/activation/ActivationTable";
import { DesignTable } from "../features/designs/DesignTable";
import { Funnel } from "../features/funnel/Funnel";
import { TierTable } from "../features/tiers/TierTable";
import type { Results } from "../shared/data/types";
import { type Fetcher, useJson } from "../shared/data/useJson";
import { eur, pct } from "../shared/format";
import { EmptyNotice, ErrorNotice } from "../shared/ui/Notice";
import { Section } from "../shared/ui/Section";
import { Segmented } from "../shared/ui/Segmented";
import { Skeleton } from "../shared/ui/Skeleton";
import { color, font, layout, leading, size, space } from "../shared/theme/tokens";

type Split = "heldout" | "dev";
const defaultFetch: Fetcher = (url) => fetch(url);

export function App({ fetcher = defaultFetch }: { fetcher?: Fetcher }) {
  const results = useJson<Results>("data/results.json", fetcher);
  return (
    <main style={{ maxWidth: layout.maxWidth, margin: "0 auto", padding: `${space[7]}px ${space[5]}px` }}>
      {results.state === "loading" && <Skeleton label="Loading results" rows={6} />}
      {results.state === "error" && <ErrorNotice message={results.message} onRetry={results.retry} />}
      {results.state === "ready" && <Dashboard results={results.data} />}
    </main>
  );
}

export function Dashboard({ results }: { results: Results }) {
  const [split, setSplit] = useState<Split>(results.heldout ? "heldout" : "dev");
  const run = (split === "heldout" ? results.heldout : results.dev) ?? results.dev;
  const act = run?.variants?.["activated"];
  const base = run?.variants?.["analysts-only"];
  if (!run || !act || !base || run.tenants.length === 0) {
    return <EmptyNotice what="results for the activated template" command="make eval && make report" />;
  }
  const saved = 1 - act.all.analyst_hours_per_1000 / base.all.analyst_hours_per_1000;
  return (
    <>
      <header style={{ maxWidth: `${layout.measure}ch` }}>
        <h1 style={{ font: `600 clamp(${size.xl}px, 5vw, ${size.xxl}px)/${leading.tight} ${font.display}`, margin: 0 }}>
          One screening agent, four customers
        </h1>
        <p style={{ fontSize: size.md, margin: `${space[4]}px 0` }}>
          Sanctions, PEP and adverse-media alerts reviewed by one agent template, configured and activated per customer
          from their own export, policy and past decisions. It closes what the evidence and the customer's policy allow,
          and sends everything else to an analyst with what it found.
        </p>
      </header>

      <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: space[4], margin: `${space[5]}px 0 ${space[6]}px` }}>
        <Segmented<Split>
          label="Months"
          value={split}
          onChange={setSplit}
          options={[
            ...(results.heldout ? [{ value: "heldout" as const, label: "Held-out months 7-8" }] : []),
            { value: "dev", label: "Development months 1-6" },
          ]}
        />
        <span style={{ color: color.muted, fontSize: size.sm }}>
          {split === "heldout"
            ? `Run once${run.commit ? ` at ${run.commit.slice(0, 7)}` : ""}; Northbank was activated inside that run.`
            : "The months the template was built and measured on."}
        </span>
      </div>

      <Funnel run={run} />

      <p style={{ maxWidth: `${layout.measure}ch`, margin: `${space[6]}px 0 0` }}>
        Across the customers the template closed {pct(act.all.auto_clear)} of alerts and {pct(act.all.media_closed)} of
        media hits, closed {act.all.matches_cleared} of {act.all.true_matches} true matches, and cut the analyst time per
        1,000 screenings by {pct(saved, 0)}, for {eur(act.all.eur_per_1000)} of model calls.
      </p>

      <Section
        title="Every design on these months"
        lead="The gate needs no true match closed, nothing closed against the customer's policy, no obeyed instruction, no missed finding, and a real share of work taken off analysts."
      >
        <DesignTable run={run} />
      </Section>

      <Section
        title="Activation"
        lead="From the customer's data dictionary and policy to a live template: a mapping check, a backtest that picks the threshold from analysts' past decisions, a shadow month, a gate."
      >
        {results.activation.length ? (
          <ActivationTable rows={results.activation} />
        ) : (
          <EmptyNotice what="activations" command="python scripts/activate.py finvia ledgerly kreditwerk" />
        )}
      </Section>

      <Section title="Which model reads what" lead="The cheapest tier whose measured pass rate, at its 95% lower bound on development history, meets the target.">
        <TierTable routing={results.routing} />
      </Section>

      <footer style={{ marginTop: space[8], color: color.muted, fontSize: size.sm, maxWidth: `${layout.measure}ch` }}>
        Lists, articles, customers and models are simulated; mistake rates are assumptions in config. Workload counts 6
        minutes per alert and 3 per media hit an analyst looks at. Generated by <code>make report</code>.
      </footer>
    </>
  );
}
