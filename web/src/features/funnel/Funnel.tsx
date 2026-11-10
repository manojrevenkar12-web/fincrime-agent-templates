import { motion, useReducedMotion } from "framer-motion";
import type { Run } from "../../shared/data/types";
import { CUSTOMERS } from "../../shared/customers";
import { pct } from "../../shared/format";
import { color, font, layout, motion as m, size, space } from "../../shared/theme/tokens";

/**
 * The page's one picture: for each customer, the share of screening alerts the activated template closes
 * without review, against the ceiling the customer's own policy allows (the dashed line). Below it, the
 * same agent with one configuration for everyone, and what that cost.
 */
function Bar({ share, ceiling, tone, index, label }: { share: number; ceiling: number; tone: string; index: number; label: string }) {
  const reduce = useReducedMotion();
  return (
    <div
      role="img"
      aria-label={label}
      style={{ position: "relative", height: layout.barHeight, background: color.queue, border: `1px solid ${color.rule}` }}
    >
      <motion.div
        initial={reduce ? false : { width: 0 }}
        animate={{ width: `${share * 100}%` }}
        transition={{ duration: m.fillSeconds, delay: index * m.stagger, ease: "easeOut" }}
        style={{ height: "100%", background: tone }}
      />
      <div
        aria-hidden
        style={{
          position: "absolute",
          top: -space[1],
          bottom: -space[1],
          left: `${ceiling * 100}%`,
          borderLeft: `2px dashed ${color.ceiling}`,
        }}
      />
    </div>
  );
}

export function Funnel({ run }: { run: Run }) {
  const act = run.variants["activated"];
  const gen = run.variants["generic"];
  return (
    <figure style={{ margin: 0 }}>
      <div style={{ display: "grid", gap: space[6] }}>
        {run.tenants.map((t, i) => {
          const a = act.tenants[t];
          const g = gen.tenants[t];
          const warn = [
            g.matches_cleared ? `${g.matches_cleared} true matches closed` : "",
            g.policy_breaches ? `${g.policy_breaches} closed against policy` : "",
          ].filter(Boolean);
          return (
            <div
              key={t}
              style={{ display: "flex", flexWrap: "wrap", gap: `${space[3]}px ${space[5]}px` }}
            >
              <div style={{ flex: `0 0 ${layout.labelColumn}px` }}>
                <div style={{ font: `600 ${size.md}px ${font.display}` }}>{CUSTOMERS[t]?.name ?? t}</div>
                <div style={{ color: color.muted, fontSize: size.sm }}>{CUSTOMERS[t]?.kind}</div>
                <div style={{ color: color.muted, fontSize: size.sm }}>{a.alerts} alerts</div>
              </div>
              <div style={{ display: "grid", gap: space[2], flex: `1 1 ${layout.barMinWidth}px`, minWidth: 0 }}>
                <Bar
                  index={i}
                  share={a.auto_clear}
                  ceiling={a.clearable_share}
                  tone={color.template}
                  label={`${CUSTOMERS[t]?.name}: template closes ${pct(a.auto_clear)} of alerts; policy allows ${pct(a.clearable_share)}`}
                />
                <div style={{ fontSize: size.sm }}>
                  <strong>{pct(a.auto_clear)}</strong> closed by the template; {a.matches_cleared === 0 ? "none" : a.matches_cleared} of
                  the {a.true_matches} true matches among them. Policy allows {pct(a.clearable_share)}.
                </div>
                <div style={{ fontSize: size.sm, color: warn.length ? color.bad : color.muted }}>
                  One config for all: {pct(g.auto_clear)} closed{warn.length ? `, ${warn.join(", ")}` : ", without harm"}.
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </figure>
  );
}
