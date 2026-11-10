// Every visual constant of the dashboard. Components read these; nothing else picks a colour or a size.
export const color = {
  paper: "#EEF1F4",
  panel: "#DDE3E9",
  ink: "#14212B",
  muted: "#52616D",
  rule: "#C3CCD4",
  rail: "#9AA9B4",
  template: "#1E5F74",
  queue: "#FFFFFF",
  ceiling: "#A8650E",
  signal: "#A8650E",
  good: "#1E6B4F",
  bad: "#B3261E",
  focus: "#2457C5",
} as const;

export const font = {
  display: "'Bitter', Georgia, serif",
  body: "'Work Sans', 'Helvetica Neue', Arial, sans-serif",
} as const;

// A modular scale of 1.25 from a 16 px base.
export const size = { xs: 12, sm: 14, base: 16, md: 20, lg: 25, xl: 31, xxl: 49 } as const;
export const leading = { tight: 1.12, body: 1.5 } as const;
export const space = { 1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48, 8: 72 } as const;
export const layout = { maxWidth: 1100, measure: 68, labelColumn: 240, barMinWidth: 300, barHeight: 34 } as const;
export const motion = { fillSeconds: 0.9, stagger: 0.12, expandSeconds: 0.22 } as const;
