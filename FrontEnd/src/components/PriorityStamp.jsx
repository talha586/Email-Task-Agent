const LABELS = { high: "HIGH", medium: "MED", low: "LOW" };

export default function PriorityStamp({ priority }) {
  if (!priority) return null;
  return (
    <span className={`stamp stamp--${priority}`}>
      {LABELS[priority] || priority.toUpperCase()}
    </span>
  );
}
