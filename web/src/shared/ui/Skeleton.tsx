import { color, space } from "../theme/tokens";

/** Grey bars in the shape of the content that is on its way. */
export function Skeleton({ label, rows = 4 }: { label: string; rows?: number }) {
  return (
    <div role="status" aria-label={label} aria-busy="true" style={{ display: "grid", gap: space[3] }}>
      {Array.from({ length: rows }, (_, i) => (
        <div
          key={i}
          style={{ height: i === 0 ? space[7] : space[5], width: `${100 - i * 9}%`, background: color.panel }}
        />
      ))}
    </div>
  );
}
