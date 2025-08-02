import React from 'react';
import './OnboardingModal.css';

interface OnboardingModalProps {
  show: boolean;
  onClose: () => void;
}

const OnboardingModal: React.FC<OnboardingModalProps> = ({ show, onClose }) => {
  if (!show) {
    return null;
  }

  return (
    <div className="modal-backdrop">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Welcome to the Flowchart-to-Code Tool!</h2>
          <button onClick={onClose} className="modal-close-button">&times;</button>
        </div>
        <div className="modal-body">
          <p>This tool helps you build algorithmic thinking skills. Here's how to use it:</p>
          <ol>
            <li><strong>Draw Your Flowchart:</strong> Use the editor on the left to drag, drop, and connect shapes. Double-click any shape to add text.</li>
            <li><strong>Analyze Your Logic:</strong> Click the "Analyze Flowchart" button. You'll get instant feedback on its structure and logic.</li>
            <li><strong>Generate Code:</strong> Once your analysis is clear of errors, select a programming language and click "Generate Code" to see the result!</li>
          </ol>
          <p>Ready to start building? Close this window to begin.</p>
        </div>
        <div className="modal-footer">
          <button onClick={onClose} className="button button--primary">
            Get Started
          </button>
        </div>
      </div>
    </div>
  );
};

export default OnboardingModal; 