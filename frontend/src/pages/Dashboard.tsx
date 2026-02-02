import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { unitService } from '../services/unitService';
import { rotaService } from '../services/rotaService';
import type { RotaListItem, UnitState } from '../types';

const Dashboard = () => {
    const navigate = useNavigate();
    const [searchQuery, setSearchQuery] = useState('');
    const [sortBy, setSortBy] = useState<'recent' | 'unit' | 'date'>('recent');
    const [rotas, setRotas] = useState<RotaListItem[]>([]);
    const [units, setUnits] = useState<UnitState[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Load data from Supabase on mount
    useEffect(() => {
        const loadData = async () => {
            try {
                setLoading(true);
                const [rotaData, unitData] = await Promise.all([
                    rotaService.getRotaListItems(),
                    unitService.getUnits(),
                ]);
                setRotas(rotaData);
                setUnits(unitData);
                setError(null);
            } catch (err) {
                console.error('Failed to load data:', err);
                setError('Failed to load data from server');
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    // Filter and sort rotas
    const filteredRotas = useMemo(() => {
        let filtered = rotas.filter((rota) =>
            rota.unitName.toLowerCase().includes(searchQuery.toLowerCase())
        );

        switch (sortBy) {
            case 'recent':
                filtered.sort((a, b) => new Date(b.lastModified).getTime() - new Date(a.lastModified).getTime());
                break;
            case 'unit':
                filtered.sort((a, b) => a.unitName.localeCompare(b.unitName));
                break;
            case 'date':
                filtered.sort((a, b) => new Date(a.startDate).getTime() - new Date(b.startDate).getTime());
                break;
        }

        return filtered;
    }, [rotas, searchQuery, sortBy]);

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric',
        });
    };

    const getTimeAgo = (dateStr: string) => {
        const now = new Date();
        const date = new Date(dateStr);
        const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));

        if (diffInHours < 1) return 'Just now';
        if (diffInHours < 24) return `${diffInHours}h ago`;
        if (diffInHours < 48) return 'Yesterday';
        return `${Math.floor(diffInHours / 24)} days ago`;
    };

    if (loading) {
        return (
            <div className="page-body" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
                <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '2rem', marginBottom: '1rem' }}>⏳</div>
                    <p>Loading dashboard...</p>
                </div>
            </div>
        );
    }

    return (
        <>
            {/* Page Header */}
            <header className="page-header">
                <div className="page-header-content">
                    <div>
                        <h1 className="page-title">Dashboard</h1>
                        <p className="page-subtitle">Manage your duty rotas and scheduling</p>
                    </div>
                    <Button
                        variant="primary"
                        size="lg"
                        icon="➕"
                        onClick={() => navigate('/create-rota')}
                    >
                        Create New Duty Rota
                    </Button>
                </div>
            </header>

            {/* Page Body */}
            <div className="page-body">
                {error && (
                    <div className="card mb-4" style={{ background: '#fef2f2', borderColor: '#fecaca', padding: '1rem' }}>
                        <p style={{ color: '#dc2626' }}>⚠️ {error}</p>
                    </div>
                )}

                {/* Stats Cards */}
                <div className="dashboard-stats animate-fadeIn">
                    <div className="stat-card">
                        <div className="stat-icon teal">📋</div>
                        <div className="stat-content">
                            <h3>{rotas.length}</h3>
                            <p>Active Rotas</p>
                        </div>
                    </div>
                    <div className="stat-card stagger-1">
                        <div className="stat-icon blue">🏢</div>
                        <div className="stat-content">
                            <h3>{units.length}</h3>
                            <p>Units Configured</p>
                        </div>
                    </div>
                    <div className="stat-card stagger-2">
                        <div className="stat-icon orange">👥</div>
                        <div className="stat-content">
                            <h3>{units.reduce((acc, unit) => acc + unit.staff.length, 0)}</h3>
                            <p>Total Staff</p>
                        </div>
                    </div>
                </div>

                {/* Filter Bar */}
                <div className="filter-bar">
                    <div className="filter-search">
                        <span className="filter-search-icon">🔍</span>
                        <input
                            type="text"
                            placeholder="Search by unit name..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                    <div className="filter-select">
                        <select
                            className="form-select"
                            value={sortBy}
                            onChange={(e) => setSortBy(e.target.value as 'recent' | 'unit' | 'date')}
                        >
                            <option value="recent">Recent Modifications</option>
                            <option value="unit">Unit Name</option>
                            <option value="date">Start Date</option>
                        </select>
                    </div>
                </div>

                {/* Section Header */}
                <div className="section-header">
                    <h2 className="section-title">Existing Rotas</h2>
                    <span className="badge badge-teal">{filteredRotas.length} rotas</span>
                </div>

                {/* Rota List */}
                {filteredRotas.length > 0 ? (
                    <div className="rota-list">
                        {filteredRotas.map((rota, index) => (
                            <div
                                key={rota.id}
                                className="rota-list-item animate-fadeIn"
                                style={{ animationDelay: `${index * 0.1}s` }}
                            >
                                <div className="rota-list-info">
                                    <h4>{rota.unitName}</h4>
                                    <div className="rota-list-meta">
                                        <span>
                                            📅 {formatDate(rota.startDate)} – {formatDate(rota.endDate)}
                                        </span>
                                        <span>🕐 Modified {getTimeAgo(rota.lastModified)}</span>
                                    </div>
                                </div>
                                <div className="flex gap-2">
                                    <Button
                                        variant="primary"
                                        size="sm"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/schedule/${rota.id}`);
                                        }}
                                    >
                                        📊 View Schedule
                                    </Button>
                                    <Button
                                        variant="secondary"
                                        size="sm"
                                        onClick={() => navigate(`/edit-rota/${rota.id}`)}
                                    >
                                        ✏️ Edit
                                    </Button>
                                </div>
                            </div>
                        ))}
                    </div>

                ) : (
                    <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                        <p style={{ fontSize: '3rem', marginBottom: '1rem' }}>📅</p>
                        <h3 style={{ marginBottom: '0.5rem' }}>No Rotas Found</h3>
                        <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
                            {searchQuery
                                ? 'No rotas match your search. Try a different query.'
                                : 'Get started by creating your first duty rota.'}
                        </p>
                        <Button variant="primary" onClick={() => navigate('/create-rota')}>
                            Create New Rota
                        </Button>
                    </div>
                )}

                {/* Quick Links */}
                <div className="section-divider" />
                <div className="section-header">
                    <h2 className="section-title">Quick Actions</h2>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                    <div className="card" style={{ cursor: 'pointer' }} onClick={() => navigate('/create-unit')}>
                        <div className="card-body" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <div style={{
                                width: '48px',
                                height: '48px',
                                borderRadius: 'var(--radius-lg)',
                                background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '1.5rem'
                            }}>
                                🏢
                            </div>
                            <div>
                                <h4 style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Create New Unit</h4>
                                <p className="text-muted text-small">Define staff and shift codes</p>
                            </div>
                        </div>
                    </div>
                    <div className="card" style={{ cursor: 'pointer' }} onClick={() => navigate('/create-rota')}>
                        <div className="card-body" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <div style={{
                                width: '48px',
                                height: '48px',
                                borderRadius: 'var(--radius-lg)',
                                background: 'linear-gradient(135deg, var(--color-teal-400) 0%, var(--color-teal-500) 100%)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '1.5rem'
                            }}>
                                📅
                            </div>
                            <div>
                                <h4 style={{ fontWeight: 600, marginBottom: '0.25rem' }}>Schedule New Rota</h4>
                                <p className="text-muted text-small">Start the optimization process</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default Dashboard;
