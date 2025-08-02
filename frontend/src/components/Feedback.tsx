import React from 'react';

// Types can be shared from a central types file in a larger app
interface AnalysisResult {
  rule_id: string;
  message: string;
  severity: 'error' | 'warning' | 'info' | 'system_error';
  elements?: string[];
}

interface CombinedAnalysisResponse {
  analysis_results: AnalysisResult[];
  feedback_messages: string[];
}

interface FeedbackProps {
  feedback: CombinedAnalysisResponse | string | null;
}

// Helper function to convert markdown-style formatting to HTML
const formatMessage = (message: string): string => {
  // Convert **bold** to <strong>
  let formatted = message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Convert line breaks to <br>
  formatted = formatted.replace(/\n/g, '<br>');
  
  return formatted;
};

const Feedback: React.FC<FeedbackProps> = ({ feedback }) => {
  if (!feedback) {
    return null;
  }

  // Handle simple string feedback (e.g., loading states, simple success/error)
  if (typeof feedback === 'string') {
    if (feedback.toLowerCase().includes("analyzing")) {
      return (
        <div className="feedback-loading">
          <div className="loader"></div>
          <p>{feedback}</p>
        </div>
      );
    }
    // Determine severity from string content for basic messages
    const severityClass = feedback.toLowerCase().startsWith('error') ? 'feedback-item--error' :
                          feedback.toLowerCase().startsWith('warning') ? 'feedback-item--warning' :
                          'feedback-item--info';
    return (
      <div className={`feedback-item ${severityClass}`}>
        <p className="feedback-message" dangerouslySetInnerHTML={{ __html: formatMessage(feedback) }}></p>
      </div>
    );
  }

  // Handle the more detailed combined response object
  const { analysis_results, feedback_messages } = feedback;

  // Since we now have user-friendly feedback_messages, prioritize those over raw analysis_results
  // The feedback_messages are the improved, user-friendly versions
  if (feedback_messages.length > 0) {
    return (
      <div className="analysis-results-single-column">
        <h4 className="results-column-header">Flowchart Analysis</h4>
        {feedback_messages.map((msg, index) => {
          // Determine severity from message icons
          const severityClass = msg.startsWith('❌') ? 'feedback-item--error' :
                               msg.startsWith('⚠️') ? 'feedback-item--warning' :
                               'feedback-item--info';
          
          return (
            <div key={`feedback-${index}`} className={`feedback-item ${severityClass}`}>
              <p className="feedback-message" dangerouslySetInnerHTML={{ __html: formatMessage(msg) }}></p>
            </div>
          );
        })}
      </div>
    );
  }

  // Fallback to old format if no feedback_messages (shouldn't happen with new system)
  return (
    <div className="analysis-results-grid">
      {analysis_results.length > 0 && (
        <div className="results-column">
          <h4 className="results-column-header">Analysis Results</h4>
          {analysis_results.map((result, index) => (
            <div key={`result-${index}`} className={`feedback-item feedback-item--${result.severity}`}>
              <p className="feedback-message">
                <strong className="feedback-severity">{result.severity.toUpperCase()}:</strong> {result.message}
              </p>
              {/* Removed the confusing "Affected: elements" display */}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Feedback; 