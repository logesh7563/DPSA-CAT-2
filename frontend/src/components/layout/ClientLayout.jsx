import React from 'react';
import { useAuth } from '../../auth/AuthContext.jsx';
import {
  ShieldAlert,
  Home,
  Database,
  PlayCircle,
  Network,
  Crosshair,
  BookOpen,
  LogOut,
  ChevronRight,
  Lock,
} from 'lucide-react';

export function ClientLayout({ activeTab, onSelectTab, clientProfile, children }) {
  const { user, logout } = useAuth();

  const navItems = [
    { id: 'home', label: 'Gateway Overview', icon: Home },
    { id: 'data', label: 'Private Dataset', icon: Database },
    { id: 'training', label: 'Local Training', icon: PlayCircle },
    { id: 'model', label: 'Global Model & Matrix', icon: Network },
    { id: 'predict', label: 'Live Intrusion Detector', icon: Crosshair },
    { id: 'learn', label: 'How FL Works', icon: BookOpen },
  ];

  const gatewayNames = {
    0: 'Client 0: Web Application Gateway',
    1: 'Client 1: Edge Perimeter Router',
    2: 'Client 2: Internal Corporate LAN',
    3: 'Client 3: Regional Branch Office',
  };

  const displayName = gatewayNames[user?.client_id] || `Client ${user?.client_id}`;

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo" style={{ background: 'linear-gradient(135deg, #10b981, #059669)' }}>
            <ShieldAlert size={20} />
          </div>
          <div>
            <div className="sidebar-title">Client Gateway</div>
            <div className="sidebar-subtitle">Isolated Edge Worker</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section-title">Client Operations</div>
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
            <div className="user-avatar" style={{ color: 'var(--success)' }}>
              C{user?.client_id}
            </div>
            <div>
              <div style={{ fontSize: '13px', fontWeight: 600 }}>{user?.username}</div>
              <span className="badge badge-success" style={{ fontSize: '10px', padding: '1px 6px' }}>
                CLIENT GATEWAY
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
            <span style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>
              {displayName}
            </span>
            <span className="badge badge-info" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Lock size={12} />
              Isolated Storage Perimeter
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
              Privacy Budget Spent:{' '}
              <strong style={{ color: 'var(--primary)' }}>
                ε = {(clientProfile?.privacy_budget_spent || 0).toFixed(2)}
              </strong>
            </span>
          </div>
        </header>

        <main className="page-body">{children}</main>
      </div>
    </div>
  );
}
