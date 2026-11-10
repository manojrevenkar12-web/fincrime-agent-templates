import { color, font, size, space } from "../theme/tokens";

export function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: { value: T; label: string }[];
  value: T;
  onChange: (v: T) => void;
}) {
  return (
    <div role="radiogroup" aria-label={label} style={{ display: "inline-flex", border: `2px solid ${color.ink}` }}>
      {options.map((o) => {
        const on = o.value === value;
        return (
          <button
            key={o.value}
            type="button"
            role="radio"
            aria-checked={on}
            onClick={() => onChange(o.value)}
            style={{
              font: `600 ${size.sm}px ${font.display}`,
              padding: `${space[2]}px ${space[4]}px`,
              border: "none",
              cursor: "pointer",
              background: on ? color.ink : "transparent",
              color: on ? color.paper : color.ink,
            }}
          >
            {o.label}
          </button>
        );
      })}
    </div>
  );
}
