import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import ScanBar from "../components/ScanBar";
import TaskList from "../components/TaskList";
import {
  deleteTask,
  fetchTasks,
  logout,
  scanInbox,
  updateTask,
} from "../api/tasksApi";

export default function HomePage() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [lastResult, setLastResult] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchTasks();
      setTasks(data);
      setError(null);
    } catch (err) {
      setError(err.message);
      if (err.message.startsWith("401")) {
        logout();
        navigate("/login", { replace: true });
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleScan() {
    setScanning(true);
    setError(null);
    try {
      const result = await scanInbox();
      setLastResult(result);
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
    }
  }

  async function handleSave(id, data) {
    const updated = await updateTask(id, data);
    setTasks((prev) => prev.map((t) => (t.id === id ? updated : t)));
  }

  async function handleDelete(id) {
    await deleteTask(id);
    setTasks((prev) => prev.filter((t) => t.id !== id));
  }

  function handleLogout() {
    logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="page">
      <button className="signout-btn" onClick={handleLogout}>
        Sign out
      </button>
      <ScanBar
        onScan={handleScan}
        scanning={scanning}
        lastResult={lastResult}
        error={error}
      />
      <main className="main">
        {loading ? (
          <p className="loading">Checking the tray…</p>
        ) : (
          <TaskList tasks={tasks} onSave={handleSave} onDelete={handleDelete} />
        )}
      </main>
      {/* Bottom-right corner intentionally left free — the NL "find latest
          mail from a name" message bar goes here next. */}
    </div>
  );
}
