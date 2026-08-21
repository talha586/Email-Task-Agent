import { useCallback, useEffect, useState } from "react";
import ScanBar from "./components/ScanBar";
import TaskList from "./components/TaskList";
import LoginGate from "./components/LoginGate";
import {
  deleteTask,
  fetchTasks,
  getAuthToken,
  logout,
  scanInbox,
  updateTask,
} from "./api/tasksApi";
import "./App.css";

export default function App() {
  const [authed, setAuthed] = useState(!!getAuthToken());
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
      if (err.message.startsWith("401")) setAuthed(false);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (authed) load();
  }, [authed, load]);

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

  if (!authed) {
    return <LoginGate onSuccess={() => setAuthed(true)} />;
  }

  return (
    <div className="page">
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
      <button
        className="logout-link"
        onClick={() => {
          logout();
          setAuthed(false);
        }}
      >
        Sign out
      </button>
    </div>
  );
}
