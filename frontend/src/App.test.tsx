import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import App from './App';

// Mock the FlowchartEditor to control its behavior in tests
// The mock should provide the captureCurrentState method and simulate an initial state
jest.mock('./components/FlowchartEditor', () => {
  return React.forwardRef((props: any, ref) => {
    // Simulate initial load by calling onSave with some data
    React.useEffect(() => {
      if(props.onSave) {
        props.onSave('<mxGraphModel><root><mxCell id="0"/></root></mxGraphModel>');
      }
    }, []);

    React.useImperativeHandle(ref, () => ({
      captureCurrentState: jest.fn().mockResolvedValue('<mxGraphModel><root><mxCell id="1"/></root></mxGraphModel>')
    }));

    return <div data-testid="mock-flowchart-editor"></div>;
  });
});

// Mock the global fetch function
global.fetch = jest.fn();

const mockFetch = global.fetch as jest.Mock;

describe('App component analysis feature', () => {

  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should display both structured results and feedback messages on successful analysis', async () => {
    // 1. Mock the successful API response
    const mockAnalysisResponse = {
      analysis_results: [
        { rule_id: 'test-rule', message: 'This is a test error message.', severity: 'error', elements: ['node1'] }
      ],
      feedback_messages: [
        'This is a helpful feedback suggestion.'
      ]
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockAnalysisResponse,
    });

    // 2. Render the App component
    render(<App />);

    // 3. Simulate clicking the "Analyze Flowchart" button
    const analyzeButton = screen.getByRole('button', { name: /analyze flowchart/i });
    
    // The button starts enabled because we mock a valid editor state
    expect(analyzeButton).not.toBeDisabled();

    await act(async () => {
      fireEvent.click(analyzeButton);
    });

    // 4. Assert that the feedback is displayed correctly
    // Use findBy queries to wait for the async state update
    const errorMessage = await screen.findByText(/This is a test error message/i);
    const suggestionMessage = await screen.findByText(/This is a helpful feedback suggestion/i);
    const severityLabel = await screen.findByText(/ERROR:/i);

    expect(errorMessage).toBeInTheDocument();
    expect(suggestionMessage).toBeInTheDocument();
    expect(severityLabel).toBeInTheDocument();

    // Check that fetch was called correctly
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/analysis/analyze_flowchart', expect.any(Object));
  });

  it('should display a generic error message if the analysis fetch fails', async () => {
    // 1. Mock a failed API response
    mockFetch.mockRejectedValueOnce(new Error('Network failure'));

    // 2. Render the App
    render(<App />);

    // 3. Click the button
    const analyzeButton = screen.getByRole('button', { name: /analyze flowchart/i });
    await act(async () => {
      fireEvent.click(analyzeButton);
    });

    // 4. Assert that a user-friendly error message is shown
    const errorMessage = await screen.findByText(/Error: Network failure/i);
    expect(errorMessage).toBeInTheDocument();
  });

});

describe('App component code generation feature', () => {

  beforeEach(() => {
    mockFetch.mockClear();
  });

  it('should call the codegen endpoint with the correct payload including language and style', async () => {
    // 1. Mock the successful API response for code generation
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ code: 'print("hello world from python")' }),
    });

    // 2. Render the App component
    render(<App />);

    // 3. Select Python from the dropdown
    const languageSelect = screen.getByLabelText(/programming language/i);
    await act(async () => {
        fireEvent.change(languageSelect, { target: { value: 'python' } });
    });

    // 4. Click the "Generate Code" button
    const generateButton = screen.getByRole('button', { name: /generate code/i });
    await act(async () => {
      fireEvent.click(generateButton);
    });

    // 5. Assert that fetch was called with the correct payload
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/codegen/generate_code',
      expect.objectContaining({
        body: JSON.stringify({
          nodes: [],
          edges: [],
          language: 'python',
          style: 'educational'
        })
      })
    );
    
    // 6. Assert that the generated code is displayed
    const codeElement = await screen.findByText(/hello world from python/i);
    expect(codeElement).toBeInTheDocument();
  });
}); 