import { useState } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Header from "./Header";

export default function AppLayout() {
  const [open, setOpen] = useState(false);
  return (
    <div className="app-shell">
      <div className={open ? "sidebar-mobile open" : "sidebar-mobile"}><Sidebar /></div>
      <div className="desktop-sidebar"><Sidebar /></div>
      <main className="main-area">
        <Header onMenu={() => setOpen((v) => !v)} />
        <div className="page-content"><Outlet /></div>
      </main>
    </div>
  );
}
