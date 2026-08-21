import { useState } from "react";
import { login } from "../api/tasksApi";

export default function LoginGate({ onSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password);
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <form className="login-card" onSubmit={handleSubmit}>
        <p className="eyebrow">Mail Room</p>
        <h1 className="login-card__title">Sign In</h1>
        <input
          className="field"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoFocus
        />
        <input
          className="field"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {error && <p className="scan-bar__error">{error}</p>}
        <button className="btn btn--primary" type="submit" disabled={busy}>
          {busy ? "Checking…" : "Enter the Mail Room"}
        </button>
      </form>
    </div>
  );
}
