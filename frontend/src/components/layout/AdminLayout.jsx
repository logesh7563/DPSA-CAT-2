import React from 'react';
import { useAuth } from '../../auth/AuthContext.jsx';
import {
  Shield,
  LayoutDashboard,
  Users,
  RefreshCw,
  Cpu,
  Lock,
  BarChart3,
  FileText,
  BookOpen,
  LogOut,
  ChevronRight,
} from 'lucide-react';

export function AdminLayout({ activeTab, onSelectTab, children }) {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'dashboard', label: 'Global Dashboard', icon: LayoutDashboard },
    { id: 'clients', label: 'Gateway Clients', icon: Users },
    { id: 'rounds', label: 'Round Orchestrator', icon: RefreshCw },
    { id: 'models', label: 'Model Registry', icon: Cpu },
    { id: 'privacy', label: 'Privacy & Security', icon: Lock },
    { id: 'communication', label: 'Benchmark & Comm', icon: BarChart3 },
    { id: 'audit', label: 'Security Audit Logs', icon: FileText },
    { id: 'learn', label: 'How FL Works', icon: BookOpen },
  ];

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <Shield size={20} />
          </div>
          <div>
            <div className="sidebar-title">FedIDS Platform</div>
            <div className="sidebar-subtitle">Central Admin Portal</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">Federated Management</div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectTab(item.id)}
                className={`nav-link ${isActive ? 'active' : ''}`}
                style={{ width: '100%', border: 'none', background: 'none', textAlign: 'left' }}
              >
                <Icon size={18} />
                <span>{item.label}</span>
                {isActive && <ChevronRight size={14} style={{ marginLeft: 'auto' }} />}
              </button>
            );
          })}
        </nav>

        <div className="sidebar-footer">
          <div className="user-profile">
            <div className="user-avatar">AD</div>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>{user?.username}</div>
              <span className="badge badge-info" style={{ fontSize: '10px', padding: '1px 6px' }}>
                ADMINISTRATOR
              </span>
            </div>
          </div>
          <button
            onClick={logout}
            className="btn btn-secondary btn-sm"
            title="Log Out"
            style={{ padding: '6px 8px' }}
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="main-content">
        <header className="topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Central Platform:</span>
            <span className="badge badge-success">Federation Online</span>
            <span className="badge badge-gray">KDDTest+ Benchmark Active</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Privacy-Preserving IDS Platform
            </span>
          </div>
        </header>

        <main className="page-body">{children}</main>
      </div>
    </div>
  );
}
