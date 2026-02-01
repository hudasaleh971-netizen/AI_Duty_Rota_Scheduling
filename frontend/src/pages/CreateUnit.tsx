import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { TextArea } from '../components/ui/TextArea';
import type { UnitState, Staff, ShiftCode } from '../types';
import { createEmptyUnitState, createEmptyStaff, createEmptyShiftCode } from '../types';
import { unitService, defaultShiftCodes } from '../services/unitService';

const CreateUnit = () => {
    const navigate = useNavigate();

    // Single Source of Truth - Unit State
    const [unitState, setUnitState] = useState<UnitState>(createEmptyUnitState());
    const [saving, setSaving] = useState(false);

    // Update unit info helper
    const updateUnitInfo = (field: keyof UnitState['unitInfo'], value: string | number) => {
        setUnitState((prev) => ({
            ...prev,
            unitInfo: {
                ...prev.unitInfo,
                [field]: value,
            },
            updatedAt: new Date().toISOString(),
        }));
    };

    // Staff table helpers
    const addStaffRow = () => {
        setUnitState((prev) => ({
            ...prev,
            staff: [...prev.staff, createEmptyStaff()],
            updatedAt: new Date().toISOString(),
        }));
    };

    const updateStaff = (index: number, field: keyof Staff, value: string | number) => {
        setUnitState((prev) => ({
            ...prev,
            staff: prev.staff.map((s, i) =>
                i === index ? { ...s, [field]: value } : s
            ),
            updatedAt: new Date().toISOString(),
        }));
    };

    const removeStaff = (index: number) => {
        setUnitState((prev) => ({
            ...prev,
            staff: prev.staff.filter((_, i) => i !== index),
            updatedAt: new Date().toISOString(),
        }));
    };

    // Shift code table helpers
    const addShiftCodeRow = () => {
        setUnitState((prev) => ({
            ...prev,
            shiftCodes: [...prev.shiftCodes, createEmptyShiftCode()],
            updatedAt: new Date().toISOString(),
        }));
    };

    const updateShiftCode = (index: number, field: keyof ShiftCode, value: string | number) => {
        setUnitState((prev) => ({
            ...prev,
            shiftCodes: prev.shiftCodes.map((sc, i) =>
                i === index ? { ...sc, [field]: value } : sc
            ),
            updatedAt: new Date().toISOString(),
        }));
    };

    const removeShiftCode = (index: number) => {
        setUnitState((prev) => ({
            ...prev,
            shiftCodes: prev.shiftCodes.filter((_, i) => i !== index),
            updatedAt: new Date().toISOString(),
        }));
    };

    // Load default shift codes
    const loadDefaultShiftCodes = () => {
        setUnitState((prev) => ({
            ...prev,
            shiftCodes: defaultShiftCodes,
            updatedAt: new Date().toISOString(),
        }));
    };

    // Save handler - now saves to Supabase
    const handleSave = async () => {
        if (!unitState.unitInfo.name) {
            alert('Please enter a unit name');
            return;
        }

        try {
            setSaving(true);
            await unitService.saveUnit(unitState);
            alert('Unit configuration saved successfully!');
            navigate('/');
        } catch (error) {
            console.error('Failed to save unit:', error);
            alert('Failed to save unit. Please try again.');
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
                        <h1 className="page-title">Create New Unit</h1>
                        <p className="page-subtitle">Define unit details, staff members, and shift codes</p>
                    </div>
                    <div className="flex gap-3">
                        <Button variant="secondary" onClick={() => navigate('/')}>
                            Cancel
                        </Button>
                        <Button variant="primary" onClick={handleSave} disabled={saving}>
                            {saving ? '⏳ Saving...' : '💾 Save Unit Configuration'}
                        </Button>
                    </div>
                </div>
            </header>

            {/* Page Body */}
            <div className="page-body">
                {/* Section A: Unit Details */}
                <div className="card animate-fadeIn mb-6">
                    <div className="card-header">
                        <h3 className="card-title">🏢 Unit Details</h3>
                    </div>
                    <div className="card-body">
                        <div className="form-row">
                            <Input
                                label="Unit Name"
                                placeholder="e.g., ICU - Floor 3"
                                value={unitState.unitInfo.name}
                                onChange={(e) => updateUnitInfo('name', e.target.value)}
                            />
                            <Input
                                label="Department/Specialty"
                                placeholder="e.g., Critical Care"
                                value={unitState.unitInfo.department}
                                onChange={(e) => updateUnitInfo('department', e.target.value)}
                            />
                        </div>
                        <div className="form-row">
                            <Input
                                label="Unit Manager/In-charge"
                                placeholder="e.g., Dr. Sarah Ahmed"
                                value={unitState.unitInfo.manager}
                                onChange={(e) => updateUnitInfo('manager', e.target.value)}
                            />
                            <Input
                                label="Min Direct Nurses per Shift"
                                type="number"
                                min={1}
                                value={unitState.unitInfo.minNursesPerShift}
                                onChange={(e) => updateUnitInfo('minNursesPerShift', parseInt(e.target.value) || 1)}
                            />
                        </div>
                        <TextArea
                            label="Unit-Specific Rules"
                            placeholder="Enter any specific rules or requirements for this unit..."
                            value={unitState.unitInfo.rules}
                            onChange={(e) => updateUnitInfo('rules', e.target.value)}
                            hint="e.g., At least 2 Level 3 nurses per shift. Maximum 3 consecutive night shifts."
                        />
                    </div>
                </div>

                {/* Section B: Staff Entry Table */}
                <div className="card animate-fadeIn stagger-1 mb-6">
                    <div className="card-header">
                        <h3 className="card-title">👥 Staff Members</h3>
                        <Button variant="primary" size="sm" onClick={addStaffRow}>
                            + Add Staff
                        </Button>
                    </div>
                    <div className="card-body" style={{ padding: 0 }}>
                        {unitState.staff.length === 0 ? (
                            <div style={{ padding: '3rem', textAlign: 'center' }}>
                                <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>👥</p>
                                <p className="text-muted">No staff members added yet.</p>
                                <Button variant="secondary" size="sm" className="mt-4" onClick={addStaffRow}>
                                    Add Your First Staff Member
                                </Button>
                            </div>
                        ) : (
                            <div className="table-container">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th>Staff Name</th>
                                            <th>Staff ID</th>
                                            <th>Position/Grade</th>
                                            <th>Staff Type</th>
                                            <th>Hours/Month</th>
                                            <th>Comments</th>
                                            <th style={{ width: '80px' }}>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {unitState.staff.map((staff, index) => (
                                            <tr key={staff.id}>
                                                <td>
                                                    <input
                                                        type="text"
                                                        className="table-input"
                                                        placeholder="Full name"
                                                        value={staff.name}
                                                        onChange={(e) => updateStaff(index, 'name', e.target.value)}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        type="text"
                                                        className="table-input"
                                                        placeholder="e.g., N12345"
                                                        value={staff.staffId}
                                                        onChange={(e) => updateStaff(index, 'staffId', e.target.value)}
                                                    />
                                                </td>
                                                <td>
                                                    <select
                                                        className="table-select"
                                                        value={staff.position}
                                                        onChange={(e) => updateStaff(index, 'position', e.target.value)}
                                                    >
                                                        <option value="Level 1">Level 1</option>
                                                        <option value="Level 2">Level 2</option>
                                                        <option value="Level 3">Level 3</option>
                                                    </select>
                                                </td>
                                                <td>
                                                    <select
                                                        className="table-select"
                                                        value={staff.type}
                                                        onChange={(e) => updateStaff(index, 'type', e.target.value)}
                                                    >
                                                        <option value="Direct Care">Direct Care</option>
                                                        <option value="Non-Direct Care">Non-Direct Care</option>
                                                    </select>
                                                </td>
                                                <td>
                                                    <input
                                                        type="number"
                                                        className="table-input"
                                                        style={{ width: '80px' }}
                                                        value={staff.contractedHours}
                                                        onChange={(e) => updateStaff(index, 'contractedHours', parseInt(e.target.value) || 0)}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        type="text"
                                                        className="table-input"
                                                        placeholder="Notes..."
                                                        value={staff.comments}
                                                        onChange={(e) => updateStaff(index, 'comments', e.target.value)}
                                                    />
                                                </td>
                                                <td>
                                                    <Button
                                                        variant="danger"
                                                        size="sm"
                                                        className="btn-icon"
                                                        onClick={() => removeStaff(index)}
                                                        title="Remove staff member"
                                                    >
                                                        🗑️
                                                    </Button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>

                {/* Section C: Shift Codes Table */}
                <div className="card animate-fadeIn stagger-2 mb-6">
                    <div className="card-header">
                        <h3 className="card-title">🕐 Shift Codes</h3>
                        <div className="flex gap-2">
                            <Button variant="secondary" size="sm" onClick={loadDefaultShiftCodes}>
                                Load Default Codes
                            </Button>
                            <Button variant="primary" size="sm" onClick={addShiftCodeRow}>
                                + Add Shift Code
                            </Button>
                        </div>
                    </div>
                    <div className="card-body" style={{ padding: 0 }}>
                        {unitState.shiftCodes.length === 0 ? (
                            <div style={{ padding: '3rem', textAlign: 'center' }}>
                                <p style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🕐</p>
                                <p className="text-muted">No shift codes defined yet.</p>
                                <div className="flex gap-2 justify-center mt-4">
                                    <Button variant="secondary" size="sm" onClick={loadDefaultShiftCodes}>
                                        Load Default Codes
                                    </Button>
                                    <Button variant="primary" size="sm" onClick={addShiftCodeRow}>
                                        Add Custom Code
                                    </Button>
                                </div>
                            </div>
                        ) : (
                            <div className="table-container">
                                <table className="table">
                                    <thead>
                                        <tr>
                                            <th style={{ width: '80px' }}>Code</th>
                                            <th>Definition</th>
                                            <th>Description</th>
                                            <th style={{ width: '80px' }}>Hours</th>
                                            <th>Type</th>
                                            <th>Remarks</th>
                                            <th style={{ width: '80px' }}>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {unitState.shiftCodes.map((shiftCode, index) => (
                                            <tr key={index}>
                                                <td>
                                                    <input
                                                        type="text"
                                                        className="table-input"
                                                        style={{ width: '60px', textTransform: 'uppercase', fontWeight: 600 }}
                                                        maxLength={3}
                                                        value={shiftCode.code}
                                                        onChange={(e) => updateShiftCode(index, 'code', e.target.value.toUpperCase())}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        type="text"
                                                        className="table-input"
                                                        placeholder="e.g., Morning"
                                                        value={shiftCode.definition}
                                                        onChange={(e) => updateShiftCode(index, 'definition', e.target.value)}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        type="text"
                                                        className="table-input"
                                                        placeholder="e.g., Day shift 7:00 AM - 3:00 PM"
                                                        value={shiftCode.description}
                                                        onChange={(e) => updateShiftCode(index, 'description', e.target.value)}
                                                    />
                                                </td>
                                                <td>
                                                    <input
                                                        type="number"
                                                        className="table-input"
                                                        style={{ width: '60px' }}
                                                        min={0}
                                                        value={shiftCode.hours}
                                                        onChange={(e) => updateShiftCode(index, 'hours', parseInt(e.target.value) || 0)}
                                                    />
                                                </td>
                                                <td>
                                                    <select
                                                        className="table-select"
                                                        value={shiftCode.type}
                                                        onChange={(e) => updateShiftCode(index, 'type', e.target.value)}
                                                    >
                                                        <option value="Direct Care">Direct Care</option>
                                                        <option value="Non-Direct Care">Non-Direct Care</option>
                                                        <option value="-">-</option>
                                                    </select>
                                                </td>
                                                <td>
                                                    <input
                                                        type="text"
                                                        className="table-input"
                                                        placeholder="Notes..."
                                                        value={shiftCode.remarks}
                                                        onChange={(e) => updateShiftCode(index, 'remarks', e.target.value)}
                                                    />
                                                </td>
                                                <td>
                                                    <Button
                                                        variant="danger"
                                                        size="sm"
                                                        className="btn-icon"
                                                        onClick={() => removeShiftCode(index)}
                                                        title="Remove shift code"
                                                    >
                                                        🗑️
                                                    </Button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="flex justify-between items-center mt-6">
                    <Button variant="ghost" onClick={() => navigate('/')}>
                        ← Back to Dashboard
                    </Button>
                    <Button variant="primary" size="lg" onClick={handleSave} disabled={saving}>
                        {saving ? '⏳ Saving...' : '💾 Save Unit Configuration'}
                    </Button>
                </div>
            </div>
        </>
    );
};

export default CreateUnit;
