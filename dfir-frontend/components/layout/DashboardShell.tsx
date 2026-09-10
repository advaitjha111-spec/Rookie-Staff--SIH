"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { ChevronLeft, FileBadge, LayoutDashboard, Menu, Network, Search, Settings, Sun, Moon, LogOut } from "lucide-react";
import { useTheme } from "next-themes";

const links = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard }, { href: "/dashboard/certificate", label: "Certificate", icon: FileBadge },
  { href: "/dashboard/intelligence", label: "Threat intelligence", icon: Network },
];

export function DashboardShell({ children, title = "Active investigation", certificate = false }: { children: React.ReactNode; title?: string; certificate?: boolean }) {
  const [collapsed, setCollapsed] = useState(false); const [searching, setSearching] = useState(false); const { theme, setTheme } = useTheme(); const path = usePathname();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  
  return <div className="dashboard-shell">
    <motion.aside animate={{ width: collapsed ? 60 : 240 }} className="sidebar"><button className="sidebar-brand" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle navigation"><span className="brand-mark">✦</span>{!collapsed && <span>PRATIKRIYA</span>}<ChevronLeft className={collapsed ? "rotate" : ""} size={17} /></button><nav aria-label="Investigation navigation">{links.map(({ href, label, icon: Icon }) => <Link key={label} href={href} title={collapsed ? label : undefined} className={path === href ? "side-link active" : "side-link"}><Icon size={20} />{!collapsed && <span>{label}</span>}</Link>)}</nav><button className="side-link logout"><LogOut size={20} />{!collapsed && <span>Logout</span>}</button></motion.aside>
    <section className="workspace"><header className="workspace-header"><div><button className="mobile-menu" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle navigation"><Menu size={20} /></button><span className="eyebrow">Case workspace</span><h1>{title}</h1></div><div className="header-controls"><motion.div layout className={searching ? "search open" : "search"}><Search size={17} /><input aria-label="Search case data" onFocus={() => setSearching(true)} onBlur={() => setSearching(false)} placeholder={searching ? "Search logs, indicators, and artifacts..." : "Search"} /></motion.div><button aria-label="Toggle theme" className="icon-button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>{mounted && (theme === "dark" ? <Sun size={18} /> : <Moon size={18} />)}</button></div></header><AnimatePresence mode="wait"><motion.div key={path} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={{ duration: .2 }} className="workspace-content">{children}</motion.div></AnimatePresence></section>
  </div>;
}
