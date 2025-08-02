import React from 'react';

type Language = "cpp" | "java" | "python" | "";
// The 'style' prop seems unused in the refactored App.tsx, can be simplified.
// type CodeStyle = "educational" | "direct";

interface CodeOptionsProps {
  language: Language;
  onLanguageChange: (lang: Language) => void;
  isGeneratingCode: boolean;
}

const CodeOptions: React.FC<CodeOptionsProps> = ({
  language,
  onLanguageChange,
  isGeneratingCode
}) => {
  return (
    // No need for a separate container, will be placed in a .controls-group
    <div className="form-group">
      <label htmlFor="languageSelect">Programming Language</label>
      <select 
        id="languageSelect" 
        value={language} 
        onChange={(e) => onLanguageChange(e.target.value as Language)} 
        className="select"
        disabled={isGeneratingCode}
        aria-label="Select programming language for code generation"
      >
        <option value="" disabled>Select a language...</option>
        <option value="cpp">C++</option>
        <option value="java">Java</option>
        <option value="python">Python</option>
      </select>
    </div>
  );
};

export default CodeOptions; 