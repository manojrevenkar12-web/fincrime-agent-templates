import type { Run } from "../../shared/data/types";
import { eur, pct } from "../../shared/format";
import { Scroll } from "../../shared/ui/Section";
import { color, font } from "../../shared/theme/tokens";

const ORDER = ["analysts-only", "rules-only", "generic", "activated", "activated-no-guards"];

export function DesignTable({ run }: { run: Run }) {
  return (
    <Scroll>
      <table>
        <thead>
          <tr>
            <th scope="col">Design</th>
            <th scope="col" className="num">Alerts closed</th>
            <th scope="col" className="num">True matches closed</th>
            <th scope="col" className="num">Against policy</th>
            <th scope="col" className="num">Media hits closed</th>
            <th scope="col" className="num">Instructions obeyed</th>
            <th scope="col" className="num">Analyst hours / 1,000</th>
            <th scope="col" className="num">Model cost / 1,000</th>
            <th scope="col">Gate</th>
          </tr>
        </thead>
        <tbody>
          {ORDER.filter((k) => run.variants[k]).map((k) => {
            const v = run.variants[k];
            const a = v.all;
            const lead = k === "activated";
            return (
              <tr key={k}>
                <th scope="row" style={{ fontFamily: font.body, fontWeight: lead ? 700 : 400, color: lead ? color.template : color.ink }}>
                  {v.label}
                </th>
                <td className="num">{pct(a.auto_clear)}</td>
                <td className="num" style={{ color: a.matches_cleared ? color.bad : color.ink }}>
                  {a.matches_cleared} of {a.true_matches}
                </td>
                <td className="num" style={{ color: a.policy_breaches ? color.bad : color.ink }}>{a.policy_breaches}</td>
                <td className="num">{pct(a.media_closed)}</td>
                <td className="num" style={{ color: a.obeyed ? color.bad : color.ink }}>
                  {a.obeyed} of {a.injected}
                </td>
                <td className="num">{Math.round(a.analyst_hours_per_1000)}</td>
                <td className="num">{eur(a.eur_per_1000)}</td>
                <td style={{ color: v.gate.ship ? color.good : color.bad }}>
                  {v.gate.ship ? "Ships" : `Held back: ${v.gate.failed.join("; ")}`}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </Scroll>
  );
}
