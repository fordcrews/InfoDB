import { type ReactNode } from "react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/subnets", label: "Subnets" },
  { to: "/routers", label: "Routers" },
  { to: "/agencies", label: "Agencies" },
  { to: "/snmp-profiles", label: "SNMP" },
  { to: "/discovery", label: "Discovery" },
];

export default function Layout({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "admin";

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <h1>InfoDB</h1>
        <nav className="sidebar-nav">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          <span className="user-email">{user?.email}</span>
          {isAdmin && <span className="admin-badge">Admin</span>}
          <button className="btn-secondary" onClick={logout}>
            Logout
          </button>
        </div>
      </aside>
      <main className="main-content">{children}</main>
    </div>
  );
}