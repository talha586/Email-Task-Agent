import TaskCard from "./TaskCard";
import EmptyState from "./EmptyState";

export default function TaskList({ tasks, onSave, onDelete }) {
  if (tasks.length === 0) return <EmptyState />;

  return (
    <div className="task-grid">
      {tasks.map((task) => (
        <TaskCard
          key={task.id}
          task={task}
          onSave={onSave}
          onDelete={onDelete}
        />
      ))}
    </div>
  );
}
