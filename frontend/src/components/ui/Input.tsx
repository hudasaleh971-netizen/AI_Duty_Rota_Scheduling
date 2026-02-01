import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    hint?: string;
    error?: string;
}

export const Input: React.FC<InputProps> = ({
    label,
    hint,
    error,
    id,
    className = '',
    ...props
}) => {
    const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

    return (
        <div className="form-group">
            {label && (
                <label htmlFor={inputId} className="form-label">
                    {label}
                </label>
            )}
            <input
                id={inputId}
                className={`form-input ${error ? 'border-red-500' : ''} ${className}`}
                {...props}
            />
            {hint && !error && <p className="form-hint">{hint}</p>}
            {error && <p className="form-hint text-red-500">{error}</p>}
        </div>
    );
};

export default Input;
