import { color, font, size, space } from "../theme/tokens";

export function ErrorNotice({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" style={{ borderLeft: `${space[1]}px solid ${color.bad}`, padding: `${space[3]}px ${space[4]}px` }}>
      <p style={{ margin: 0 }}>Results could not be loaded: {message}.</p>
      <p style={{ margin: `${space[2]}px 0`, color: color.muted }}>
        Check that <code>web/public/data</code> exists (it is written by <code>make report</code>), then try again.
      </p>
      <button type="button" onClick={onRetry} style={buttonStyle}>
        Try again
      </button>
    </div>
  );
}

export function EmptyNotice({ what, command }: { what: string; command: string }) {
  return (
    <p style={{ color: color.muted, margin: 0 }}>
      No {what} yet. Run <code>{command}</code> to produce them.
    </p>
  );
}

export const buttonStyle = {
  font: `600 ${size.sm}px ${font.display}`,
  color: color.paper,
  background: color.ink,
  border: "none",
  padding: `${space[2]}px ${space[4]}px`,
  cursor: "pointer",
} as const;
