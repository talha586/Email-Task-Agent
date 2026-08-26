import { useNavigate } from "react-router-dom";
import LoginGate from "../components/LoginGate";

export default function LoginPage() {
  const navigate = useNavigate();

  return <LoginGate onSuccess={() => navigate("/", { replace: true })} />;
}
