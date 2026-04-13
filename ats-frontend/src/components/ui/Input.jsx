import React from 'react';

const Input = ({ 
  type = 'text',
  placeholder = '',
  value = '',
  onChange,
  className = '',
  disabled = false,
  required = false,
  ...props 
}) => {
  const baseClasses = 'w-full px-3 py-2 border border-gray-300 rounded-md text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent';
  
  const disabledClasses = disabled ? 'bg-gray-100 cursor-not-allowed' : '';
  
  const classes = `${baseClasses} ${disabledClasses} ${className}`;

  return (
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={onChange}
      disabled={disabled}
      required={required}
      className={classes}
      {...props}
    />
  );
};

export default Input;
