import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { scheduleService } from '../services/scheduleService';
import { rotaService } from '../services/rotaService';
import { unitService } from '../services/unitService';
import type { ScheduleResult, RotaState, UnitState } from '../types';

const ViewSchedule = () => {
    const { rotaId } = useParams<{ rotaId: string }>();
    const navigate = useNavigate();

    const [scheduleResult, setScheduleResult] = useState<ScheduleResult | null>(null);
    const [rota, setRota] = useState<RotaState | null>(null);
    const [unit, setUnit] = useState<UnitState | null>(null);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Generate date range for the schedule grid
    const dateRange = useMemo(() => {
        if (!rota?.metadata.startDate || !rota?.metadata.endDate) return [];

        const start = new Date(rota.metadata.startDate);
        const end = new Date(rota.metadata.endDate);
        const dates: Date[] = [];

        const current = new Date(start);
        while (current <= end) {
            dates.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }

        return dates;
    }, [rota]);

    // Parse schedule result into staff -> date -> shiftCode map
    const scheduleByStaff = useMemo(() => {
        if (!scheduleResult) return new Map<string, Map<string, string>>();
        return scheduleService.parseScheduleByStaff(scheduleResult);
    }, [scheduleResult]);

    // Load rota and unit data
    useEffect(() => {
        const loadData = async () => {
            if (!rotaId) return;

            try {
                setLoading(true);
                setError(null);

                // Load rota config
                const rotaData = await rotaService.getRotaById(rotaId);
                if (!rotaData) {
                    setError('Rota not found');
                    return;
                }
                setRota(rotaData);

                // Load unit data
                const unitData = await unitService.getUnitById(rotaData.metadata.unitId);
                if (unitData) {
                    setUnit(unitData);
                }
            } catch (err) {
                console.error('Failed to load data:', err);
                setError(err instanceof Error ? err.message : 'Failed to load data');
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, [rotaId]);

    // Generate schedule using AI
    const handleGenerate = async () => {
        if (!rotaId) return;

        try {
            setGenerating(true);
            setError(null);
            const result = await scheduleService.generateSchedule(rotaId);
            setScheduleResult(result);

            if (result.status === 'error') {
                setError(result.error || 'Failed to generate schedule');
            }
        } catch (err) {
            console.error('Failed to generate schedule:', err);
            setError(err instanceof Error ? err.message : 'Failed to generate schedule');
        } finally {
            setGenerating(false);
        }
    };

    // Format date for display
    const formatDateHeader = (date: Date) => {
        const day = date.getDate();
        const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
        return { day, dayName };
    };

    // Check if date is weekend
    const isWeekend = (date: Date) => {
        const day = date.getDay();
        return day === 0 || day === 6;
    };

    // Format date for data (YYYY-MM-DD)
    const formatDateForData = (date: Date) => {
        return date.toISOString().split('T')[0];
    };

    // Get shift code color class
    const getShiftCodeColor = (code: string): string => {
        const codeUpper = code.toUpperCase();
        if (codeUpper === 'M') return 'shift-morning';
        if (codeUpper === 'E') return 'shift-evening';
        if (codeUpper === 'N') return 'shift-night';
        if (codeUpper === 'AL') return 'shift-leave';
        if (codeUpper === 'SL') return 'shift-sick';
        if (codeUpper === 'TR') return 'shift-training';
        if (codeUpper === 'DO' || codeUpper === 'O') return 'shift-off';
        return 'shift-default';
    };

    // Get shift for a staff member on a specific date
    const getShiftForStaff = (staffName: string, date: string): string => {
        const staffSchedule = scheduleByStaff.get(staffName);
        if (!staffSchedule) return '-';
        return staffSchedule.get(date) || '-';
    };

    if (loading) {
        return (
            <div className="page-body">
                <div className="card" style={{ textAlign: 'center', padding: '4rem' }}>
                    <div className="text-large">⏳ Loading schedule data...</div>
                </div>
            </div>
        );
    }

    if (error && !rota) {
        return (
            <div className="page-body">
                <div className="card" style={{ textAlign: 'center', padding: '4rem' }}>
                    <div className="text-large text-muted">❌ {error}</div>
                    <Button variant="secondary" onClick={() => navigate('/')} className="mt-4">
                        Back to Dashboard
                    </Button>
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
                        <h1 className="page-title">📅 Optimized Schedule</h1>
                        <p className="page-subtitle">
                            {rota?.metadata.unitName} · {rota?.metadata.startDate} → {rota?.metadata.endDate}
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <Button variant="secondary" onClick={() => navigate('/')}>
                            ← Dashboard
                        </Button>
                        <Button
                            variant="primary"
                            onClick={handleGenerate}
                            disabled={generating}
                        >
                            {generating ? '🤖 Generating...' : '🔄 Generate Schedule'}
                        </Button>
                    </div>
                </div>
            </header>

            {/* Page Body */}
            <div className="page-body">
                {/* Status Banner */}
                {scheduleResult && (
                    <div
                        className="card mb-6 animate-fadeIn"
                        style={{
                            background: scheduleResult.status === 'success'
                                ? 'linear-gradient(135deg, var(--color-teal-50), var(--color-teal-100))'
                                : 'linear-gradient(135deg, var(--color-coral-50), var(--color-coral-100))',
                            borderColor: scheduleResult.status === 'success'
                                ? 'var(--color-teal-200)'
                                : 'var(--color-coral-200)',
                        }}
                    >
                        <div className="card-body">
                            <div className="flex items-center justify-between">
                                <div>
                                    <h3 style={{ margin: 0 }}>
                                        {scheduleResult.status === 'success' ? '✅ Schedule Generated' : '❌ Generation Failed'}
                                    </h3>
                                    {scheduleResult.score && (
                                        <p className="text-small" style={{ margin: '0.5rem 0 0 0' }}>
                                            Score: <strong>{scheduleResult.score}</strong>
                                        </p>
                                    )}
                                </div>
                                {scheduleResult.summary && (
                                    <div className="flex gap-4">
                                        <div style={{ textAlign: 'center' }}>
                                            <div className="text-large font-bold">{scheduleResult.summary.totalShifts}</div>
                                            <div className="text-small text-muted">Total Shifts</div>
                                        </div>
                                        <div style={{ textAlign: 'center' }}>
                                            <div className="text-large font-bold" style={{ color: 'var(--color-teal-500)' }}>
                                                {scheduleResult.summary.assignedShifts}
                                            </div>
                                            <div className="text-small text-muted">Assigned</div>
                                        </div>
                                        <div style={{ textAlign: 'center' }}>
                                            <div className="text-large font-bold" style={{ color: 'var(--color-coral-500)' }}>
                                                {scheduleResult.summary.unassignedShifts}
                                            </div>
                                            <div className="text-small text-muted">Unassigned</div>
                                        </div>
                                    </div>
                                )}
                            </div>
                            {error && (
                                <p className="text-small" style={{ color: 'var(--color-coral-600)', marginTop: '0.5rem' }}>
                                    {error}
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {/* No Schedule Yet */}
                {!scheduleResult && !generating && (
                    <div className="card mb-6" style={{ textAlign: 'center', padding: '4rem' }}>
                        <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🤖</div>
                        <h2>Ready to Generate Schedule</h2>
                        <p className="text-muted mb-4">
                            Click the button below to run the AI optimization and generate an optimized duty rota.
                        </p>
                        <Button variant="primary" size="lg" onClick={handleGenerate}>
                            🚀 Generate Optimized Schedule
                        </Button>
                    </div>
                )}

                {/* Generating Animation */}
                {generating && (
                    <div className="card mb-6" style={{ textAlign: 'center', padding: '4rem' }}>
                        <div style={{ fontSize: '4rem', marginBottom: '1rem', animation: 'pulse 2s infinite' }}>🤖</div>
                        <h2>AI is Optimizing Your Schedule...</h2>
                        <p className="text-muted">
                            This may take up to 2 minutes. The AI is analyzing constraints and finding the best assignments.
                        </p>
                        <div className="mt-4" style={{ width: '200px', margin: '1rem auto', height: '4px', background: 'var(--color-slate-200)', borderRadius: '2px', overflow: 'hidden' }}>
                            <div style={{ width: '100%', height: '100%', background: 'var(--color-teal-500)', animation: 'loading 1.5s ease-in-out infinite' }} />
                        </div>
                    </div>
                )}

                {/* Schedule Grid */}
                {scheduleResult?.status === 'success' && scheduleResult.schedule && unit && (
                    <div className="card animate-fadeIn mb-6">
                        <div className="card-header">
                            <h3 className="card-title">📊 Full Schedule View</h3>
                            <div className="flex gap-2">
                                <span className="badge badge-teal">{unit.staff.length} Staff</span>
                                <span className="badge badge-gray">{dateRange.length} Days</span>
                            </div>
                        </div>
                        <div className="card-body" style={{ padding: 0 }}>
                            <div className="rota-grid">
                                <table className="rota-table">
                                    <thead>
                                        <tr>
                                            <th>Staff Member</th>
                                            <th style={{ minWidth: '80px' }}>Hours</th>
                                            {dateRange.map((date) => {
                                                const { day, dayName } = formatDateHeader(date);
                                                return (
                                                    <th
                                                        key={formatDateForData(date)}
                                                        className={isWeekend(date) ? 'weekend' : ''}
                                                    >
                                                        <div style={{ fontSize: '0.7rem', opacity: 0.8 }}>{dayName}</div>
                                                        <div>{day}</div>
                                                    </th>
                                                );
                                            })}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {unit.staff.map((staff) => {
                                            const hours = scheduleResult.summary?.employeeHours?.[staff.name] || 0;
                                            return (
                                                <tr key={staff.id}>
                                                    <td>
                                                        <div style={{ fontWeight: 600 }}>{staff.name}</div>
                                                        <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-500)' }}>
                                                            {staff.staffId} · {staff.position}
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <div
                                                            style={{
                                                                textAlign: 'center',
                                                                fontWeight: 600,
                                                                color: hours > 0 ? 'var(--color-teal-600)' : 'var(--color-slate-400)',
                                                                background: hours > 0 ? 'var(--color-teal-50)' : 'transparent',
                                                                padding: '0.5rem',
                                                                borderRadius: 'var(--radius-md)',
                                                            }}
                                                        >
                                                            {hours}h
                                                        </div>
                                                    </td>
                                                    {dateRange.map((date) => {
                                                        const dateStr = formatDateForData(date);
                                                        const shiftCode = getShiftForStaff(staff.name, dateStr);
                                                        return (
                                                            <td key={dateStr} className={isWeekend(date) ? 'weekend' : ''}>
                                                                <div
                                                                    className={`schedule-cell ${getShiftCodeColor(shiftCode)}`}
                                                                    style={{
                                                                        textAlign: 'center',
                                                                        padding: '0.5rem',
                                                                        borderRadius: 'var(--radius-sm)',
                                                                        fontWeight: 600,
                                                                        fontSize: '0.875rem',
                                                                    }}
                                                                >
                                                                    {shiftCode}
                                                                </div>
                                                            </td>
                                                        );
                                                    })}
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                )}

                {/* Employee Hours Summary */}
                {scheduleResult?.status === 'success' && scheduleResult.summary?.employeeHours && (
                    <div className="card animate-fadeIn stagger-1 mb-6">
                        <div className="card-header">
                            <h3 className="card-title">📈 Hours Summary</h3>
                        </div>
                        <div className="card-body">
                            <div
                                style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                                    gap: '1rem',
                                }}
                            >
                                {Object.entries(scheduleResult.summary.employeeHours).map(([name, hours]) => (
                                    <div
                                        key={name}
                                        style={{
                                            padding: '1rem',
                                            background: 'var(--color-slate-50)',
                                            borderRadius: 'var(--radius-lg)',
                                            display: 'flex',
                                            justifyContent: 'space-between',
                                            alignItems: 'center',
                                        }}
                                    >
                                        <span style={{ fontWeight: 500 }}>{name}</span>
                                        <span
                                            style={{
                                                fontWeight: 700,
                                                color: hours > 0 ? 'var(--color-teal-600)' : 'var(--color-slate-400)',
                                                fontSize: '1.125rem',
                                            }}
                                        >
                                            {hours}h
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                {/* Shift Code Legend */}
                {unit && (
                    <div className="card animate-fadeIn stagger-2">
                        <div className="card-header">
                            <h3 className="card-title">🔤 Shift Code Reference</h3>
                        </div>
                        <div className="card-body">
                            <div
                                style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))',
                                    gap: '0.75rem',
                                }}
                            >
                                {unit.shiftCodes.map((code) => (
                                    <div
                                        key={code.code}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '0.5rem',
                                            padding: '0.5rem 0.75rem',
                                            background: 'var(--color-slate-50)',
                                            borderRadius: 'var(--radius-md)',
                                        }}
                                    >
                                        <span
                                            className={`schedule-cell ${getShiftCodeColor(code.code)}`}
                                            style={{
                                                fontWeight: 700,
                                                fontSize: '0.875rem',
                                                minWidth: '35px',
                                                textAlign: 'center',
                                                padding: '0.25rem',
                                                borderRadius: 'var(--radius-sm)',
                                            }}
                                        >
                                            {code.code}
                                        </span>
                                        <span className="text-small">
                                            {code.definition} ({code.hours}h)
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* CSS for shift colors and animations */}
            <style>{`
                .shift-morning { background: #e0f7fa; color: #00695c; }
                .shift-evening { background: #fff3e0; color: #e65100; }
                .shift-night { background: #e8eaf6; color: #283593; }
                .shift-leave { background: #e8f5e9; color: #2e7d32; }
                .shift-sick { background: #ffebee; color: #c62828; }
                .shift-training { background: #f3e5f5; color: #6a1b9a; }
                .shift-off { background: #f5f5f5; color: #757575; }
                .shift-default { background: transparent; color: var(--color-slate-400); }
                
                @keyframes loading {
                    0% { transform: translateX(-100%); }
                    100% { transform: translateX(100%); }
                }
                
                @keyframes pulse {
                    0%, 100% { opacity: 1; transform: scale(1); }
                    50% { opacity: 0.7; transform: scale(1.1); }
                }
            `}</style>
        </>
    );
};

export default ViewSchedule;
