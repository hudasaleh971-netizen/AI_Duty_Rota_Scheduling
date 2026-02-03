import { useState, useMemo, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Select } from '../components/ui/Select';
import { TextArea } from '../components/ui/TextArea';
import { AICopilotSidebar } from '../components/AICopilotSidebar';
import type { RotaState, SpecialRequest, UnitState } from '../types';
import { createEmptyRotaState } from '../types';
import { unitService } from '../services/unitService';
import { rotaService } from '../services/rotaService';

const CreateRota = () => {
    const navigate = useNavigate();

    // Single Source of Truth - Rota State
    const [rotaState, setRotaState] = useState<RotaState>(createEmptyRotaState());

    // Units loaded from Supabase
    const [units, setUnits] = useState<UnitState[]>([]);
    const [loadingUnits, setLoadingUnits] = useState(true);

    // Current step (1 = Configuration, 2 = Pre-Schedule)
    const [currentStep, setCurrentStep] = useState(1);
    const [saving, setSaving] = useState(false);

    // Load units from Supabase on mount
    useEffect(() => {
        const loadUnits = async () => {
            try {
                setLoadingUnits(true);
                const data = await unitService.getUnits();
                setUnits(data);
            } catch (error) {
                console.error('Failed to load units:', error);
            } finally {
                setLoadingUnits(false);
            }
        };

        loadUnits();
    }, []);

    // Get selected unit data
    const selectedUnit = useMemo(() => {
        return rotaState.metadata.unitId
            ? units.find(u => u.id === rotaState.metadata.unitId)
            : null;
    }, [rotaState.metadata.unitId, units]);

    // Generate date range for the rota grid
    const dateRange = useMemo(() => {
        if (!rotaState.metadata.startDate || !rotaState.metadata.endDate) return [];

        const start = new Date(rotaState.metadata.startDate);
        const end = new Date(rotaState.metadata.endDate);
        const dates: Date[] = [];

        const current = new Date(start);
        while (current <= end) {
            dates.push(new Date(current));
            current.setDate(current.getDate() + 1);
        }

        return dates;
    }, [rotaState.metadata.startDate, rotaState.metadata.endDate]);

    // Update metadata helper
    const updateMetadata = (field: keyof RotaState['metadata'], value: string) => {
        setRotaState((prev) => {
            const updated = {
                ...prev,
                metadata: {
                    ...prev.metadata,
                    [field]: value,
                },
                updatedAt: new Date().toISOString(),
            };

            // If unit is selected, also update the unit name
            if (field === 'unitId') {
                const unit = units.find(u => u.id === value);
                if (unit) {
                    updated.metadata.unitName = unit.unitInfo.name;
                }
            }

            return updated;
        });
    };

    // Get shift code for a specific cell
    const getCellValue = (staffId: string, date: string): string => {
        const request = rotaState.specialRequests.find(
            (r) => r.staffId === staffId && r.date === date
        );
        return request?.shiftCode || '';
    };

    // Check if a cell is locked
    const getCellLocked = (staffId: string, date: string): boolean => {
        const request = rotaState.specialRequests.find(
            (r) => r.staffId === staffId && r.date === date
        );
        return request?.isLocked || false;
    };

    // Toggle lock status for a cell
    const toggleCellLock = (staffId: string, date: string) => {
        setRotaState((prev) => {
            const newRequests = prev.specialRequests.map((r) =>
                r.staffId === staffId && r.date === date
                    ? { ...r, isLocked: !r.isLocked }
                    : r
            );
            return {
                ...prev,
                specialRequests: newRequests,
                updatedAt: new Date().toISOString(),
            };
        });
    };

    // Update cell value
    const updateCellValue = (staffId: string, date: string, shiftCode: string) => {
        setRotaState((prev) => {
            const existingIndex = prev.specialRequests.findIndex(
                (r) => r.staffId === staffId && r.date === date
            );

            let newRequests: SpecialRequest[];

            if (shiftCode === '') {
                // Remove the request if empty
                newRequests = prev.specialRequests.filter(
                    (r) => !(r.staffId === staffId && r.date === date)
                );
            } else if (existingIndex >= 0) {
                // Update existing request
                newRequests = prev.specialRequests.map((r, i) =>
                    i === existingIndex ? { ...r, shiftCode: shiftCode.toUpperCase() } : r
                );
            } else {
                // Add new request
                newRequests = [
                    ...prev.specialRequests,
                    {
                        staffId,
                        date,
                        shiftCode: shiftCode.toUpperCase(),
                        isLocked: false,
                    },
                ];
            }

            return {
                ...prev,
                specialRequests: newRequests,
                updatedAt: new Date().toISOString(),
            };
        });
    };

    // Update comments
    const updateComments = (comments: string) => {
        setRotaState((prev) => ({
            ...prev,
            comments,
            updatedAt: new Date().toISOString(),
        }));
    };

    // Get owing hours for a staff member
    const getOwingHours = (staffId: string): number => {
        return rotaState.staffOwingHours[staffId] || 0;
    };

    // Update owing hours for a staff member
    const updateOwingHours = (staffId: string, hours: number) => {
        setRotaState((prev) => ({
            ...prev,
            staffOwingHours: {
                ...prev.staffOwingHours,
                [staffId]: hours,
            },
            updatedAt: new Date().toISOString(),
        }));
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

    // Validation for step 1
    const canProceedToStep2 = () => {
        return (
            rotaState.metadata.unitId &&
            rotaState.metadata.startDate &&
            rotaState.metadata.endDate &&
            new Date(rotaState.metadata.startDate) <= new Date(rotaState.metadata.endDate)
        );
    };

    // Save handler - now saves to Supabase
    const handleSave = async () => {
        if (!selectedUnit) return;

        try {
            setSaving(true);

            // Calculate target hours for each staff member before saving
            const targetHours: { [staffId: string]: number } = {};
            for (const staff of selectedUnit.staff) {
                const owing = rotaState.staffOwingHours[staff.id] || 0;
                targetHours[staff.id] = staff.contractedHours + owing;
            }

            // Save rota with calculated target hours
            const savedRota = await rotaService.saveRota({
                ...rotaState,
                staffTargetHours: targetHours,
            });

            // Navigate to schedule page to generate and view the optimized schedule
            navigate(`/schedule/${savedRota.id}`);
        } catch (error) {
            console.error('Failed to save rota:', error);
            alert('Failed to save rota. Please try again.');
        } finally {
            setSaving(false);
        }
    };


    return (
        <>
            {/* Page Header */}
            <header className="page-header">
                <div className="page-header-content">
                    <div>
                        <h1 className="page-title">Create New Duty Rota</h1>
                        <p className="page-subtitle">
                            {currentStep === 1
                                ? 'Step 1: Select unit and planning period'
                                : 'Step 2: Enter pre-schedule requests and constraints'}
                        </p>
                    </div>
                    <div className="flex gap-3">
                        <Button variant="secondary" onClick={() => navigate('/')}>
                            Cancel
                        </Button>
                        {currentStep === 2 && (
                            <Button variant="primary" onClick={handleSave} disabled={saving}>
                                {saving ? '⏳ Saving...' : '💾 Save & Continue to Scheduling'}
                            </Button>
                        )}
                    </div>
                </div>
            </header>

            {/* Page Body */}
            <div className="page-body">
                {/* Stepper */}
                <div className="stepper mb-6 animate-fadeIn">
                    <div className={`step ${currentStep >= 1 ? 'active' : ''} ${currentStep > 1 ? 'completed' : ''}`}>
                        <div className="step-number">{currentStep > 1 ? '✓' : '1'}</div>
                        <span className="step-label">Configuration</span>
                    </div>
                    <div className={`step-connector ${currentStep > 1 ? 'completed' : ''}`} />
                    <div className={`step ${currentStep >= 2 ? 'active' : ''}`}>
                        <div className="step-number">2</div>
                        <span className="step-label">Pre-Schedule</span>
                    </div>
                </div>

                {/* Step 1: Configuration */}
                {currentStep === 1 && (
                    <div className="card animate-fadeIn">
                        <div className="card-header">
                            <h3 className="card-title">📋 Rota Configuration</h3>
                        </div>
                        <div className="card-body">
                            <div className="form-row">
                                <Select
                                    label="Select Unit"
                                    placeholder={loadingUnits ? 'Loading units...' : 'Choose a unit...'}
                                    options={units.map((unit) => ({
                                        value: unit.id,
                                        label: `${unit.unitInfo.name} (${unit.staff.length} staff)`,
                                    }))}
                                    value={rotaState.metadata.unitId}
                                    onChange={(e) => updateMetadata('unitId', e.target.value)}
                                />
                                <div className="form-group">
                                    <span className="form-label">Or create a new unit</span>
                                    <Button
                                        variant="secondary"
                                        className="w-full mt-2"
                                        onClick={() => navigate('/create-unit')}
                                    >
                                        + Create New Unit
                                    </Button>
                                </div>
                            </div>

                            <div className="section-divider" />

                            <div className="form-row">
                                <div className="form-group">
                                    <label className="form-label">Start Date</label>
                                    <input
                                        type="date"
                                        className="form-input"
                                        value={rotaState.metadata.startDate}
                                        onChange={(e) => updateMetadata('startDate', e.target.value)}
                                    />
                                </div>
                                <div className="form-group">
                                    <label className="form-label">End Date</label>
                                    <input
                                        type="date"
                                        className="form-input"
                                        value={rotaState.metadata.endDate}
                                        min={rotaState.metadata.startDate}
                                        onChange={(e) => updateMetadata('endDate', e.target.value)}
                                    />
                                </div>
                            </div>

                            {selectedUnit && (
                                <div
                                    className="mt-4"
                                    style={{
                                        padding: '1rem',
                                        background: 'var(--color-slate-50)',
                                        borderRadius: 'var(--radius-lg)',
                                        border: '1px solid var(--color-slate-200)',
                                    }}
                                >
                                    <div className="flex items-center gap-3 mb-2">
                                        <span className="badge badge-teal">{selectedUnit.staff.length} Staff</span>
                                        <span className="badge badge-blue">{selectedUnit.shiftCodes.length} Shift Codes</span>
                                    </div>
                                    <p className="text-small text-muted">
                                        <strong>Manager:</strong> {selectedUnit.unitInfo.manager}
                                        {selectedUnit.unitInfo.rules && (
                                            <>
                                                <br />
                                                <strong>Rules:</strong> {selectedUnit.unitInfo.rules}
                                            </>
                                        )}
                                    </p>
                                </div>
                            )}

                            <div className="flex justify-between items-center mt-6">
                                <Button variant="ghost" onClick={() => navigate('/')}>
                                    ← Back to Dashboard
                                </Button>
                                <Button
                                    variant="primary"
                                    size="lg"
                                    disabled={!canProceedToStep2()}
                                    onClick={() => setCurrentStep(2)}
                                >
                                    Continue to Pre-Schedule →
                                </Button>
                            </div>
                        </div>
                    </div>
                )}

                {/* Step 2: Pre-Schedule Grid */}
                {currentStep === 2 && selectedUnit && (
                    <>
                        <div className="card animate-fadeIn mb-6">
                            <div className="card-header">
                                <div>
                                    <h3 className="card-title">📅 Pre-Schedule Grid</h3>
                                    <p className="text-small text-muted mt-1">
                                        Enter known constraints: leave requests (AL), training days (TR), day offs (DO), etc.
                                    </p>
                                </div>
                                <div className="flex gap-2">
                                    <span className="badge badge-teal">{selectedUnit.unitInfo.name}</span>
                                    <span className="badge badge-gray">
                                        {rotaState.metadata.startDate} → {rotaState.metadata.endDate}
                                    </span>
                                </div>
                            </div>
                            <div className="card-body" style={{ padding: 0 }}>
                                <div className="rota-grid">
                                    <table className="rota-table">
                                        <thead>
                                            <tr>
                                                <th>Staff Member</th>
                                                <th style={{ minWidth: '80px' }}>Prev. Owing</th>
                                                <th style={{ minWidth: '80px' }}>Target Hrs</th>
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
                                            {selectedUnit.staff.map((staff) => (
                                                <tr key={staff.id}>
                                                    <td>
                                                        <div style={{ fontWeight: 600 }}>{staff.name}</div>
                                                        <div style={{ fontSize: '0.75rem', color: 'var(--color-slate-500)' }}>
                                                            {staff.staffId} · {staff.position}
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <input
                                                            type="number"
                                                            className="table-input"
                                                            style={{ width: '70px', textAlign: 'center' }}
                                                            value={getOwingHours(staff.id)}
                                                            onChange={(e) => updateOwingHours(staff.id, parseInt(e.target.value) || 0)}
                                                            title="Balance from previous month (positive = extra hours worked, negative = hours owed)"
                                                        />
                                                    </td>
                                                    <td>
                                                        <div
                                                            style={{
                                                                width: '70px',
                                                                textAlign: 'center',
                                                                fontWeight: 600,
                                                                color: 'var(--color-teal-600)',
                                                                background: 'var(--color-teal-50)',
                                                                padding: '0.5rem',
                                                                borderRadius: 'var(--radius-md)',
                                                            }}
                                                            title={`Contracted: ${staff.contractedHours} + Owing: ${getOwingHours(staff.id)} = Target`}
                                                        >
                                                            {staff.contractedHours + getOwingHours(staff.id)}
                                                        </div>
                                                    </td>
                                                    {dateRange.map((date) => {
                                                        const dateStr = formatDateForData(date);
                                                        const value = getCellValue(staff.id, dateStr);
                                                        const isLocked = getCellLocked(staff.id, dateStr);
                                                        return (
                                                            <td key={dateStr} style={{ position: 'relative' }}>
                                                                <div style={{ display: 'flex', alignItems: 'center', gap: '2px' }}>
                                                                    <input
                                                                        type="text"
                                                                        className={`rota-cell-input ${value ? 'has-value' : ''} ${isLocked ? 'is-locked' : ''}`}
                                                                        maxLength={3}
                                                                        value={value}
                                                                        onChange={(e) =>
                                                                            updateCellValue(staff.id, dateStr, e.target.value)
                                                                        }
                                                                        placeholder="-"
                                                                        style={{
                                                                            borderColor: isLocked ? 'var(--color-coral-500)' : undefined,
                                                                            background: isLocked ? 'var(--color-coral-50)' : undefined,
                                                                        }}
                                                                    />
                                                                    {value && (
                                                                        <button
                                                                            type="button"
                                                                            onClick={() => toggleCellLock(staff.id, dateStr)}
                                                                            title={isLocked ? 'Unlock (click to allow changes)' : 'Lock (click to prevent changes)'}
                                                                            style={{
                                                                                background: 'none',
                                                                                border: 'none',
                                                                                cursor: 'pointer',
                                                                                fontSize: '0.75rem',
                                                                                padding: '2px',
                                                                                opacity: isLocked ? 1 : 0.4,
                                                                            }}
                                                                        >
                                                                            {isLocked ? '🔒' : '🔓'}
                                                                        </button>
                                                                    )}
                                                                </div>
                                                            </td>
                                                        );
                                                    })}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>

                        {/* Shift Code Legend */}
                        <div className="card animate-fadeIn stagger-1 mb-6">
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
                                    {selectedUnit.shiftCodes.map((code) => (
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
                                                style={{
                                                    fontWeight: 700,
                                                    fontSize: '0.875rem',
                                                    color: 'var(--color-teal-500)',
                                                    minWidth: '30px',
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

                        {/* Comments */}
                        <div className="card animate-fadeIn stagger-2 mb-6">
                            <div className="card-header">
                                <h3 className="card-title">💬 Comments & Notes</h3>
                            </div>
                            <div className="card-body">
                                <TextArea
                                    placeholder="Enter any comments or special considerations for this scheduling period..."
                                    value={rotaState.comments}
                                    onChange={(e) => updateComments(e.target.value)}
                                />
                            </div>
                        </div>

                        {/* Footer Actions */}
                        <div className="flex justify-between items-center mt-6">
                            <Button variant="ghost" onClick={() => setCurrentStep(1)}>
                                ← Back to Configuration
                            </Button>
                            <Button variant="primary" size="lg" onClick={handleSave} disabled={saving}>
                                {saving ? '⏳ Saving...' : '💾 Save & Continue to Scheduling'}
                            </Button>
                        </div>
                    </>
                )}
            </div>

            {/* AI Copilot Sidebar for form assistance */}
            <AICopilotSidebar
                agentType="rota"
                onFileProcessed={(data) => {
                    console.log('Rota file processed:', data);
                    // TODO: Apply extracted data to form
                }}
                onSuggestionsReceived={(suggestions) => {
                    console.log('Rota suggestions:', suggestions);
                }}
            />
        </>
    );
};

export default CreateRota;
