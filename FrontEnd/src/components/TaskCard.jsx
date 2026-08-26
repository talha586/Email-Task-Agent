import { useState } from "react";
import PriorityStamp from "./PriorityStamp";
import ConfidenceMark from "./ConfidenceMark";

function PencilIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M11.3 2.3a1 1 0 0 1 1.4 0l1 1a1 1 0 0 1 0 1.4l-7 7-3 .6.6-3 7-7Z"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg
      width="15"
      height="15"
      viewBox="0 0 16 16"
      fill="none"
      aria-hidden="true"
    >
      <path
        d="M3 4.5h10M6.5 4.5V3a1 1 0 0 1 1-1h1a1 1 0 0 1 1 1v1.5M4.5 4.5 5 13a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1l.5-8.5"
        stroke="currentColor"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function TaskCard({ task, onSave, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(task);
  const [saving, setSaving] = useState(false);

  function startEdit() {
    setDraft(task);
    setEditing(true);
  }

  async function save() {
    setSaving(true);
    try {
      await onSave(task.id, {
        title: draft.title,
        description: draft.description,
        due_date: draft.due_date || null,
        priority: draft.priority || null,
      });
      setEditing(false);
    } finally {
      setSaving(false);
    }
  }

  if (editing) {
    return (
      <article className="card card--editing">
        <input
          className="field field--title"
          value={draft.title}
          onChange={(e) => setDraft({ ...draft, title: e.target.value })}
          placeholder="Task title"
          aria-label="Task title"
        />
        <textarea
          className="field field--desc"
          value={draft.description || ""}
          onChange={(e) => setDraft({ ...draft, description: e.target.value })}
          placeholder="Description"
          rows={3}
          aria-label="Task description"
        />
        <div className="field-row">
          <input
            type="date"
            className="field field--date"
            value={draft.due_date || ""}
            onChange={(e) => setDraft({ ...draft, due_date: e.target.value })}
            aria-label="Due date"
          />
          <select
            className="field field--priority"
            value={draft.priority || ""}
            onChange={(e) =>
              setDraft({ ...draft, priority: e.target.value || null })
            }
            aria-label="Priority"
          >
            <option value="">No priority</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
          </select>
        </div>
        <div className="card__actions">
          <button
            className="btn btn--ghost"
            onClick={() => setEditing(false)}
            disabled={saving}
          >
            Cancel
          </button>
          <button className="btn btn--primary" onClick={save} disabled={saving}>
            {saving ? "Saving…" : "Save changes"}
          </button>
        </div>
      </article>
    );
  }

  return (
    <article className="card">
      <header className="card__head">
        <PriorityStamp priority={task.priority} />
        {task.due_date && <span className="due">Due {task.due_date}</span>}
      </header>
      <h3 className="card__title">{task.title}</h3>
      {task.description && <p className="card__desc">{task.description}</p>}
      <footer className="card__foot">
        <ConfidenceMark value={task.confidence} />
        <div className="card__buttons">
          <button
            className="icon-btn"
            onClick={startEdit}
            aria-label="Edit task"
          >
            <PencilIcon />
          </button>
          <button
            className="icon-btn icon-btn--danger"
            onClick={() => onDelete(task.id)}
            aria-label="Delete task"
          >
            <TrashIcon />
          </button>
        </div>
      </footer>
    </article>
  );
}
