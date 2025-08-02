import React, { useState, useEffect, useRef } from 'react'
import FlowchartEditor, { type FlowchartEditorRef } from './components/FlowchartEditor'
import CodeOptions from './components/CodeOptions';
import Feedback from './components/Feedback';
import OnboardingModal from './components/OnboardingModal';
import Snackbar from './components/Snackbar';
// Import parsing utilities and types
import {
  parseDrawioXml,
  extractFlowchartElements,
  extractXmlFromSvg,
  type FlowchartNode,
  type FlowchartEdge
} from './utils/flowchartParser'
// Import the advanced code formatter
import { formatCode } from './utils/codeFormatter'

// Define a type for the structured data state
interface StructuredFlowchartData {
  nodes: FlowchartNode[];
  edges: FlowchartEdge[];
}

// Frontend type for AnalysisResult, matching backend Pydantic model
interface AnalysisResult {
  rule_id: string;
  message: string;
  severity: 'error' | 'warning' | 'info' | 'system_error'; // System_error is handled as a generic error
  elements?: string[]; 
}

// Type for the combined analysis response from the backend
interface CombinedAnalysisResponse {
  analysis_results: AnalysisResult[];
  feedback_messages: string[];
}

// Configuration for the Draw.io editor
const editorConfig = {
  defaultLibraries: "flowchart;general", // Prioritize flowchart and general shapes
  // To strictly limit available libraries via "More Shapes...", use enabledLibraries:
  // enabledLibraries: ["flowchart", "general", "basic"],
  defaultEdgeStyle: { 
    "endArrow": "classic", 
    "html": "1", // Important for certain styles/arrowheads to render correctly
    "rounded": "0" // Use straight lines for connectors by default
  }
  // Add other configurations like custom fonts, colors, etc. as needed
};

function App() {
  const [flowchartXml, setFlowchartXml] = useState<string>(''); // Start with empty flowchart
  const [structuredData, setStructuredData] = useState<StructuredFlowchartData | null>(null);
  const [analysisFeedback, setAnalysisFeedback] = useState<CombinedAnalysisResponse | string | null>(null);
  const [analysisHasErrors, setAnalysisHasErrors] = useState<boolean>(true); // Start with true to disable generation initially

  // State for Code Generation
  const [selectedLanguage, setSelectedLanguage] = useState<"cpp" | "java" | "python" | "">("");
  const [codeStyle, setCodeStyle] = useState<'educational' | 'direct'>('educational');
  const [generatedCode, setGeneratedCode] = useState<string | null>(null);
  const [generatedCodeLanguage, setGeneratedCodeLanguage] = useState<"cpp" | "java" | "python" | null>(null);
  const [codeGenerationError, setCodeGenerationError] = useState<string | null>(null);
  const [isGeneratingCode, setIsGeneratingCode] = useState<boolean>(false);
  const codeRef = useRef<HTMLPreElement>(null);
  
  // Add ref for FlowchartEditor to trigger manual capture
  const flowchartEditorRef = useRef<FlowchartEditorRef>(null);
  const [showOnboarding, setShowOnboarding] = useState<boolean>(false);

  // Snackbar state
  const [snackbarMessage, setSnackbarMessage] = useState<string>('');
  const [showSnackbar, setShowSnackbar] = useState<boolean>(false);
  const [snackbarType, setSnackbarType] = useState<'success' | 'error'>('success');

  const handleEditorLoad = () => {
    // console.log("App: FlowchartEditor has loaded.");
    // Perform any actions needed once the editor is ready
  };

  const handleFlowchartChange = (newXml: string) => {
    // console.log('App: handleFlowchartChange received:', newXml ? newXml.substring(0, 100) + '...' : 'null or empty string');
    let xmlToSet: string = '';

    if (newXml && typeof newXml === 'string' && newXml.trim().startsWith('<')) {
      // Primarily expect plain XML from react-drawio's onSave event
      xmlToSet = newXml;
      // console.log('App: Received plain XML from editor.');
    } else if (newXml && typeof newXml === 'string' && newXml.startsWith('data:image/svg+xml;base64,')) {
      // This case might be less common for onSave, more for onExport if that were wired here.
      // Keeping it for now for robustness, but primary expectation is plain XML.
      console.warn('App: Received data URI, attempting to decode. This is unexpected for onSave.');
      try {
        const base64Data = newXml.substring('data:image/svg+xml;base64,'.length);
        if (base64Data) {
          const decodedSvg = atob(base64Data); // Decode base64
          // console.log('App: Decoded SVG from data URI:', decodedSvg.substring(0,100) + '...');
          
          // Try to extract embedded draw.io XML from the SVG
          const embeddedXml = extractXmlFromSvg(decodedSvg);
          if (embeddedXml) {
            xmlToSet = embeddedXml;
            // console.log('App: Extracted embedded XML from SVG:', xmlToSet.substring(0,100) + '...');
          } else {
            // If no embedded XML found, the SVG itself might not contain draw.io data
            console.warn('App: No embedded draw.io XML found in SVG');
            setAnalysisFeedback("Warning: SVG does not contain embedded draw.io flowchart data.");
            xmlToSet = '';
          }
        } else {
          console.warn('App: Empty base64 data in URI.');
          setAnalysisFeedback("Error: Empty flowchart data received from editor (data URI).");
        }
      } catch (e) {
        console.error('App: Error decoding base64 data URI:', e);
        setAnalysisFeedback("Error: Could not decode flowchart data from editor (data URI).");
      }
    } else if (newXml === null || (typeof newXml === 'string' && newXml.trim() === '')) {
      console.warn('App: Received empty or null string from editor.');
      setAnalysisFeedback("Warning: Flowchart editor returned empty data.");
    } else {
      console.warn('App: Received data is not a known XML string or supported data URI. Clearing data.');
      setAnalysisFeedback("Error: Invalid flowchart data format from editor.");
    }

    setFlowchartXml(xmlToSet);
    // Always clear analysis when flowchart changes
    setAnalysisFeedback(null);
    setGeneratedCode(null);
    setGeneratedCodeLanguage(null);
    setCodeGenerationError(null);
  };

  useEffect(() => {
    // console.log('useEffect: flowchartXml state changed, current value:', flowchartXml ? flowchartXml.substring(0,100) : 'null_or_empty_string');
    if (flowchartXml && flowchartXml.trim().startsWith('<')) {
      const doc = parseDrawioXml(flowchartXml);
      const elements = extractFlowchartElements(doc);
      if (elements) {
        setStructuredData(elements);
        // console.log('useEffect: Structured data updated from flowchartXml state.', elements);
        // If parsing was successful, but previous state was an error message for parsing, clear it.
        if (typeof analysisFeedback === 'string' && analysisFeedback.startsWith('Error: Flowchart data could not be parsed')) {
            setAnalysisFeedback(null); 
        }
      } else {
        setStructuredData(null);
        // console.log('useEffect: Failed to parse XML from flowchartXml state, structured data cleared.');
        setAnalysisFeedback("Error: Flowchart data could not be parsed (useEffect).");
      }
    } else {
        // flowchartXml is null, empty, or doesn't look like XML.
        // This can happen on initial load if default is bad, or if handleFlowchartChange set an empty xmlToSet.
        setStructuredData(null);
        // console.log('useEffect: flowchartXml is null, empty, or not valid XML. Structured data cleared.');
        // Avoid overwriting specific error messages from handleFlowchartChange unless it's a generic parsing failure of valid-looking but bad XML
        if (flowchartXml === '') { // Specifically if it was cleared by handleFlowchartChange
            setAnalysisHasErrors(true);
        } else if (flowchartXml !== null && !flowchartXml.trim().startsWith('<')) {
            // It's not null, not empty, but doesn't start with '<'
            // setAnalysisFeedback("Error: Invalid flowchart data in state (useEffect).");
            setAnalysisHasErrors(true);
        }
    }
  }, [flowchartXml]); // Removed analysisFeedback from dependency array

  useEffect(() => {
    // Check if the user has seen the onboarding before
    const hasSeenOnboarding = localStorage.getItem('hasSeenOnboarding');
    if (!hasSeenOnboarding) {
      setShowOnboarding(true);
    }
  }, []);

  const handleAnalyzeFlowchart = async () => {
    setAnalysisFeedback("Capturing and analyzing...");
    setGeneratedCode(null);
    setGeneratedCodeLanguage(null);
    setCodeGenerationError(null);

    if (!flowchartEditorRef.current) {
      setAnalysisFeedback("Error: Editor is not available.");
      return;
    }

    try {
      // Step 1: Capture the current state from the editor, which returns the latest XML.
      // console.log('🔄 Capturing current flowchart state...');
      const latestXml = await flowchartEditorRef.current.captureCurrentState();

      // Step 2: Immediately parse the fresh XML to get up-to-date structured data.
              // console.log('📄 Parsing captured XML for analysis...');
      const doc = parseDrawioXml(latestXml);
      const elements = extractFlowchartElements(doc);

      // Also trigger the main state update, though we won't rely on it for this immediate action.
      handleFlowchartChange(latestXml);

      if (!elements) {
        setAnalysisFeedback("Error: Failed to parse flowchart data after capture.");
        return;
      }
      
      // DEBUG: Log what we're about to send
              // console.log("🔍 DEBUG: About to analyze flowchart");
        // console.log("📊 Structured data:", elements);
        // console.log("📋 Nodes being sent:");
        // elements.nodes.forEach((node, index) => {
        //   console.log(`   ${index + 1}. ${node.id}: "${node.value}" (type: ${node.type || 'UNDEFINED'})`);
        // });
        // console.log("📋 Edges being sent:", elements.edges.length);

      // Step 3: Send the fresh data to the backend for analysis.
      const response = await fetch("/api/v1/analysis/analyze_flowchart", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(elements),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText || response.statusText}`);
      }

      const results: CombinedAnalysisResponse = await response.json();

      if (results && (results.analysis_results.length > 0 || results.feedback_messages.length > 0)) {
        setAnalysisFeedback(results);
      } else {
        // No issues found, provide descriptive feedback
        let description = "✅ Validated successfully! Your flowchart has correct structure and follows all required rules.";
        
        const nodeCount = elements.nodes.length;
        const edgeCount = elements.edges.length;
        description += `\n\n📊 Your flowchart contains ${nodeCount} nodes and ${edgeCount} connections.`;
        
        setAnalysisFeedback(description);
      }
      
      // Update error state for code generation guard
      setAnalysisHasErrors(results.analysis_results.some(r => r.severity === 'error' || r.severity === 'system_error' || r.severity === 'warning'));

    } catch (error) {
      console.error("Error during analysis:", error);
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
      setAnalysisFeedback(`Error: ${errorMessage}`);
      setAnalysisHasErrors(true); // Treat analysis failure as an error state
    }
  };

  const handleGenerateCode = async () => {
    // Guard: Prevent code generation if there are known analysis errors or no language is selected.
    if (analysisHasErrors) {
      setCodeGenerationError("Please fix the errors and warnings identified in the analysis before generating code.");
      return;
    }
    if (!selectedLanguage) {
      setCodeGenerationError("Please select a programming language before generating code.");
      return;
    }

    setIsGeneratingCode(true);
    setGeneratedCode(null);
    setGeneratedCodeLanguage(null);
    setCodeGenerationError(null);
    setAnalysisFeedback(null); // Clear analysis feedback when generating code

    if (!flowchartEditorRef.current) {
      setCodeGenerationError("Error: Editor is not available.");
      setIsGeneratingCode(false);
      return;
    }

    try {
      // Step 1: Capture the current state from the editor.
              // console.log('🔄 Capturing current flowchart state before code generation...');
      const latestXml = await flowchartEditorRef.current.captureCurrentState();

      // Step 2: Parse the fresh XML to get data for code generation.
              // console.log('📄 Parsing captured XML for code generation...');
      const doc = parseDrawioXml(latestXml);
      const elements = extractFlowchartElements(doc);

      // Also trigger the main state update.
      handleFlowchartChange(latestXml);

      if (!elements) {
        setCodeGenerationError("Error: Failed to parse flowchart data after capture.");
        setIsGeneratingCode(false);
        return;
      }

      // Step 3: Send the fresh data to the backend for code generation.
      const payload = {
        nodes: elements.nodes,
        edges: elements.edges,
        language: selectedLanguage,
        style: codeStyle,
      };

        // console.log("Generating code with payload:", payload);

      const response = await fetch("/api/v1/codegen/generate_code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status} - ${errorText || response.statusText}`);
      }

      const data = await response.json();
      
      // Handle both backend response shapes (raw string or {code: "..."}) for compatibility
      const codeText = typeof data === "string" ? data : (data && typeof data.code === "string") ? data.code : null;

      if (codeText) {
        const formattedCode = await formatCode(codeText, { language: selectedLanguage });
        setGeneratedCode(formattedCode);
        setGeneratedCodeLanguage(selectedLanguage);
      } else {
        const errorDetail = data ? (data.error || data.detail || "Backend did not return generated code.") : "Backend did not return generated code.";
        throw new Error(errorDetail);
      }
    } catch (error) {
      console.error("Error during code generation:", error);
      const errorMessage = error instanceof Error ? error.message : "An unknown error occurred.";
      setCodeGenerationError(`Error: ${errorMessage}`);
    } finally {
      setIsGeneratingCode(false);
    }
  };

  const handleCopyCode = () => {
    if (generatedCode && codeRef.current) {
      navigator.clipboard.writeText(generatedCode)
        .then(() => {
          setSnackbarMessage('Code copied to clipboard!');
          setSnackbarType('success');
          setShowSnackbar(true);
          setTimeout(() => setShowSnackbar(false), 3000);
        })
        .catch(err => {
          console.error('Failed to copy code: ', err);
          setSnackbarMessage('Failed to copy code.');
          setSnackbarType('error');
          setShowSnackbar(true);
          setTimeout(() => setShowSnackbar(false), 3000);
        });
    }
  };

  const handleCloseOnboarding = () => {
    setShowOnboarding(false);
    localStorage.setItem('hasSeenOnboarding', 'true');
  };

  // Helper to render action buttons, avoiding repetition
  const renderActionButtons = () => (
    <>
      <button
        onClick={handleAnalyzeFlowchart}
        className="button button--secondary"
        disabled={isGeneratingCode}
      >
        Analyze Flowchart
      </button>
      <button
        onClick={handleGenerateCode}
        className="button button--primary"
        disabled={isGeneratingCode || analysisHasErrors || !selectedLanguage}
        title={
          analysisHasErrors 
            ? "Fix errors and warnings from analysis to enable code generation" 
            : !selectedLanguage 
            ? "Select a programming language to enable code generation" 
            : "Generate Code"
        }
      >
        {isGeneratingCode ? 'Generating...' : 'Generate Code'}
      </button>
    </>
  );

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Flowchart-to-Code Converter</h1>
        {/* Future elements like user auth could go here */}
      </header>

      <main className="app-main">
        <section className="app-section editor-section">
          <FlowchartEditor
            ref={flowchartEditorRef}
            xml={flowchartXml}
            onSave={handleFlowchartChange}
            onLoad={handleEditorLoad}
            configuration={editorConfig}
          />
        </section>

        <section className="app-section controls-section">
          <div className="controls-group">
            <h2 className="controls-header">Actions</h2>
            <div className="desktop-cta-bar" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)'}}>
              {renderActionButtons()}
            </div>
          </div>

          <div className="controls-group">
            <h2 className="controls-header">Code Generation Options</h2>
            <CodeOptions
              language={selectedLanguage}
              onLanguageChange={setSelectedLanguage}
              isGeneratingCode={isGeneratingCode}
            />
          </div>

          {(analysisFeedback || generatedCode || codeGenerationError) && (
            <div className="controls-group">
               {analysisFeedback && (
                <div className="feedback-section">
                  <h3 className="feedback-header">Analysis Feedback</h3>
                  <Feedback feedback={analysisFeedback} />
                </div>
              )}

              {generatedCode && generatedCodeLanguage && (
                <div className="code-display-container">
                  <div className="code-header">
                    <span className="language-label">{generatedCodeLanguage}</span>
                    <button onClick={handleCopyCode} className="copy-button">
                      Copy
                    </button>
                  </div>
                  <pre className="code-display" ref={codeRef}>
                    <code dangerouslySetInnerHTML={{ __html: formatCode(generatedCode, { language: generatedCodeLanguage }) }} />
                  </pre>
                </div>
              )}

              {codeGenerationError && (
                <div className="feedback-section">
                   <h3 className="feedback-header">Error</h3>
                   <div className="feedback-error">{codeGenerationError}</div>
                </div>
              )}
            </div>
          )}
        </section>
      </main>

      {/* Mobile-only sticky bar */}
      <div className="mobile-cta-bar">
        {renderActionButtons()}
      </div>

      <OnboardingModal show={showOnboarding} onClose={handleCloseOnboarding} />
      <Snackbar message={snackbarMessage} show={showSnackbar} type={snackbarType} />
    </div>
  );
}

// Removed React.CSSProperties style objects as they will be moved to App.css

export default App
