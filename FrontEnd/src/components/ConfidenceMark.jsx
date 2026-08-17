export default function ConfidenceMark({ value }) {
  if (value === null || value === undefined) return null;
  const pct = Math.round(value * 100);
  return (
    <span className="confidence" title={`${pct}% confidence`}>
      <span className="confidence__fill" style={{ width: `${pct}%` }} />
      <span className="confidence__label">{pct}%</span>
    </span>
  );
}
