export const pct = (x: number | null | undefined, digits = 1): string =>
  x === null || x === undefined ? "–" : `${(100 * x).toFixed(digits)}%`;

export const ms = (x: number): string => (x < 1000 ? `${Math.round(x)} ms` : `${(x / 1000).toFixed(1)} s`);

export const eur = (x: number, digits = 2): string => `€${x.toFixed(digits)}`;
