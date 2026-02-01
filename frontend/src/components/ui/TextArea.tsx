import React from 'react';

interface TextAreaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
    label?: string;
    hint?: string;
}

export const TextArea: React.FC<TextAreaProps> = ({
    label,
    hint,
    id,
    className = '',
    ...props
}) => {
    const textareaId = id || `textarea-${Math.random().toString(36).substr(2, 9)}`;

    return (
        <div className="form-group">
            {label && (
                <label htmlFor={textareaId} className="form-label">
                    {label}
                </label>
            )}
            <textarea
                id={textareaId}
                className={`form-textarea ${className}`}
                {...props}
            />
            {hint && <p className="form-hint">{hint}</p>}
        </div>
    );
};

export default TextArea;
