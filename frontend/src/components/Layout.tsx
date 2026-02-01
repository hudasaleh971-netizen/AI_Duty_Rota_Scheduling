import { NavLink, Outlet } from 'react-router-dom';

const Layout = () => {
    return (
        <div className="app-container">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="sidebar-logo">
                        <div className="sidebar-logo-icon">🏥</div>
                        <div>
                            <div className="sidebar-logo-text">DutyRota AI</div>
                            <div className="sidebar-logo-subtitle">Smart Scheduling</div>
                        </div>
                    </div>
                </div>

                <nav className="sidebar-nav">
                    <NavLink
                        to="/"
                        className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                        end
                    >
                        <span className="nav-link-icon">📊</span>
                        <span>Dashboard</span>
                    </NavLink>

                    <NavLink
                        to="/create-rota"
                        className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                    >
                        <span className="nav-link-icon">📅</span>
                        <span>Create Rota</span>
                    </NavLink>

                    <NavLink
                        to="/create-unit"
                        className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                    >
                        <span className="nav-link-icon">🏢</span>
                        <span>Create Unit</span>
                    </NavLink>
                </nav>

                <div style={{ padding: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-400)' }}>
                        Powered by CopilotKit
                    </div>
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                <Outlet />
            </main>
        </div>
    );
};

export default Layout;
