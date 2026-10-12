import { type ReactNode } from "react";
import { useAuth } from "../auth/AuthContext";

export default function AdminGate({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== "admin") {
    return (
      <div className="card">
        <p className="error">Admin access required for this page.</p>
      </div>
    );
  }
  return <>{children}</>;
}