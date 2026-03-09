import { NavLink } from "react-router-dom";

const links = [
  { to: "/", label: "Dashboard" },
  { to: "/chat-monitor", label: "Chat Monitor" },
  { to: "/detection-debug", label: "Detection Debug" },
  { to: "/memory-center", label: "Memory Center" },
  { to: "/settings", label: "Settings" },
  { to: "/logs", label: "Logs" },
];

export function Sidebar() {
  return (
    <aside className="sidebar">
      <h1 className="sidebar-title">WeChat Console</h1>
      <nav>
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) => `sidebar-link${isActive ? " active" : ""}`}
            end={link.to === "/"}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
