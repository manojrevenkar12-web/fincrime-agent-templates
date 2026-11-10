import type { Results } from "../../shared/data/types";
import { pct } from "../../shared/format";
import { Scroll } from "../../shared/ui/Section";
import { color } from "../../shared/theme/tokens";

const TASKS: Record<string, string> = {
  remarks: "Reading list remarks (date and place of birth)",
  media: "Reading articles (age, city, topic, outcome)",
};

export function TierTable({ routing }: { routing: Results["routing"] }) {
  const tiers = Object.values(routing)[0]?.tiers ?? [];
  return (
    <Scroll>
      <table>
        <thead>
          <tr>
            <th scope="col">Model task</th>
            <th scope="col" className="num">Target</th>
            {tiers.map((t) => (
              <th key={t.tier} scope="col" className="num">
                {t.tier}
              </th>
            ))}
            <th scope="col">Chosen</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(routing).map(([task, t]) => (
            <tr key={task}>
              <th scope="row" style={{ fontWeight: 400 }}>{TASKS[task] ?? task}</th>
              <td className="num">{pct(t.target, 0)}</td>
              {t.tiers.map((r) => (
                <td key={r.tier} className="num" style={{ color: r.tier === t.chosen ? color.template : color.ink }}>
                  {pct(r.rate)} <span style={{ color: color.muted }}>≥ {pct(r.lower)}</span>
                </td>
              ))}
              <td>
                {t.chosen}
                {t.meets_target ? "" : ", closest to the target"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Scroll>
  );
}
