import type { ReactNode } from "react";
import { color, font, layout, leading, size, space } from "../theme/tokens";

export function Section({ title, lead, children }: { title: string; lead?: ReactNode; children: ReactNode }) {
  return (
    <section style={{ marginTop: space[8] }} aria-label={title}>
      <h2 style={{ font: `600 ${size.xl}px/${leading.tight} ${font.display}`, margin: 0 }}>{title}</h2>
      {lead && (
        <p style={{ maxWidth: `${layout.measure}ch`, color: color.muted, margin: `${space[3]}px 0 ${space[5]}px` }}>
          {lead}
        </p>
      )}
      {children}
    </section>
  );
}

export function Scroll({ children }: { children: ReactNode }) {
  return (
    <div style={{ overflowX: "auto" }} tabIndex={0} role="region" aria-label="Scrollable table">
      {children}
    </div>
  );
}
