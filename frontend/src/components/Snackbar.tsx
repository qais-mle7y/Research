import React from 'react';
import './Snackbar.css';

interface SnackbarProps {
  message: string;
  show: boolean;
  type?: 'success' | 'error';
}

const Snackbar: React.FC<SnackbarProps> = ({ message, show, type = 'success' }) => {
  if (!show) {
    return null;
  }

  return (
    <div className={`snackbar show ${type}`}>
      {message}
    </div>
  );
};

export default Snackbar; 