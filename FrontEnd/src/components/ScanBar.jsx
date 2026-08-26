export default function ScanBar({ onScan, scanning, lastResult, error }) {
  return (
    <header className="scan-bar">
      <div className="scan-bar__title">
        <p className="eyebrow">Mail Room</p>
        <h1>Inbox Control</h1>
      </div>
      <div className="scan-bar__action">
        <button
          className={`stamp-btn ${scanning ? "stamp-btn--busy" : ""}`}
          onClick={onScan}
          disabled={scanning}
        >
          {scanning ? "Sorting…" : "Scan Inbox"}
        </button>
        {lastResult && !error && (
          <p className="scan-bar__note">
            {lastResult.messages_fetched} mail
            {lastResult.messages_fetched === 1 ? "" : "s"} checked ·{" "}
            {lastResult.total_tasks} task
            {lastResult.total_tasks === 1 ? "" : "s"} on file
          </p>
        )}
        {error && <p className="scan-bar__error">{error}</p>}
      </div>
    </header>
  );
}
