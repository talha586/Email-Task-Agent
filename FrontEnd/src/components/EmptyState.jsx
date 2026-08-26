export default function EmptyState() {
  return (
    <div className="empty">
      <svg
        width="64"
        height="48"
        viewBox="0 0 64 48"
        fill="none"
        className="empty__icon"
        aria-hidden="true"
      >
        <rect
          x="2"
          y="6"
          width="60"
          height="40"
          rx="3"
          stroke="currentColor"
          strokeWidth="1.5"
        />
        <path
          d="M4 8l28 22L60 8"
          stroke="currentColor"
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </svg>
      <p className="empty__title">Nothing sorted yet</p>
      <p className="empty__body">
        Scan your inbox to pull action items out of your latest mail.
      </p>
    </div>
  );
}
