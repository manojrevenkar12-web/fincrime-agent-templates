import type { Activation } from "../../shared/data/types";
import { CUSTOMERS } from "../../shared/customers";
import { pct } from "../../shared/format";
import { Scroll } from "../../shared/ui/Section";
import { color } from "../../shared/theme/tokens";

export function ActivationTable({ rows }: { rows: Activation[] }) {
  return (
    <Scroll>
      <table>
        <thead>
          <tr>
            <th scope="col">Customer</th>
            <th scope="col" className="num">Config lines</th>
            <th scope="col">Mapping check</th>
            <th scope="col" className="num">Threshold</th>
            <th scope="col" className="num">Shadow month: clears analysts agree with</th>
            <th scope="col">Switched on</th>
            <th scope="col">One-size config, same checks</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.tenant}>
              <th scope="row" style={{ fontWeight: 400 }}>
                {CUSTOMERS[r.tenant]?.name ?? r.tenant}
              </th>
              <td className="num">{r.config_lines}</td>
              <td style={{ color: r.mapping_ok ? color.ink : color.bad }}>{r.mapping_ok ? "passes" : "fails"}</td>
              <td className="num">{r.theta ?? "–"}</td>
              <td className="num">
                {pct(r.shadow.clears_analysts_agree_with ?? 0)} of {r.shadow.cleared ?? 0}
              </td>
              <td>{r.live ? `yes, in ${r.seconds} s` : "no"}</td>
              <td style={{ color: r.generic_live ? color.ink : color.bad }}>
                {r.generic_live === null ? "–" : r.generic_live ? "passes" : "fails the mapping check"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </Scroll>
  );
}
