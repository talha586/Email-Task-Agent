import { Navigate } from "react-router-dom";
import { getAuthToken } from "../api/tasksApi";

export default function ProtectedRoute({ children }) {
  if (!getAuthToken()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}
