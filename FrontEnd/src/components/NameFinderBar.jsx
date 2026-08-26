import { useState } from "react";
import { findTaskByMessage } from "../api/tasksApi";

export default function NameFinderBar() {
  const [message, setMessage] = useState("");
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!message.trim()) return;

    setBusy(true);
    setError(null);
    setResult(null);
    try {
      const data = await findTaskByMessage(message.trim());
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="name-finder">
      {(result || error) && (
        <div className="name-finder__result">
          {error && <p className="name-finder__error">{error}</p>}
          {result && !result.task && (
            <p className="name-finder__empty">{result.message}</p>
          )}
          {result?.task && (
            <>
              <p className="name-finder__found-label">{result.message}</p>
              <p className="name-finder__task-title">{result.task.title}</p>
              {result.task.description && (
                <p className="name-finder__task-desc">
                  {result.task.description}
                </p>
              )}
              <p className="name-finder__task-meta">
                {result.task.priority && <span>{result.task.priority}</span>}
                {result.task.due_date && (
                  <span>Due {result.task.due_date}</span>
                )}
              </p>
            </>
          )}
        </div>
      )}
      <form className="name-finder__bar" onSubmit={handleSubmit}>
        <input
          className="name-finder__input"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="e.g. what did Sarah ask me to do?"
          aria-label="Find the latest task from a person"
        />
        <button className="name-finder__send" type="submit" disabled={busy}>
          {busy ? "…" : "Find"}
        </button>
      </form>
    </div>
  );
}
