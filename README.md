# Flowchart-to-Code Learning Tool

An educational tool that helps students learn programming concepts by creating flowcharts and generating code from them. Students can visualize their algorithmic thinking through flowcharts, get instant feedback on their logic, and see how their flowcharts translate into actual code.

## What This Tool Does

### 🎨 Visual Flowchart Editor
- Drag-and-drop flowchart editor powered by Draw.io
- Standard flowchart symbols (start/end, process, decision, input/output)
- Real-time editing with automatic saving

### 🔍 Intelligent Analysis
- **Structural validation**: Checks for proper start/end nodes, connections, and flow
- **Logic analysis**: Detects infinite loops, unreachable code, and missing branches
- **Pedagogical feedback**: Provides educational suggestions for better flowchart design
- **Real-time feedback**: Instant analysis results with detailed explanations

### 💻 Multi-Language Code Generation
- **Supported languages**: Python, C++, Java  
- **Educational focus**: Generated code includes extensive comments explaining each step
- **Learning resources**: Comments include links to educational materials
- **Syntax highlighting**: Clean, readable code output with proper formatting

## Quick Start

### Prerequisites
- **Backend**: Python 3.8+
- **Frontend**: Node.js 16+ and npm

### Running the Application

1. **Clone the repository**
   ```bash
   git clone https://github.com/qais-mle7y/Research.git
   cd Research
   ```

2. **Start the Backend API**
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
   The API will be available at `http://localhost:8000`

3. **Start the Frontend** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   The web app will be available at `http://localhost:5173`

### Using the Tool

1. **Create a Flowchart**: Use the visual editor to drag and drop flowchart symbols
2. **Analyze Your Logic**: Click "Analyze Flowchart" to get instant feedback
3. **Generate Code**: Once your flowchart passes analysis, select a programming language and click "Generate Code"
4. **Learn**: Review the generated code with its educational comments and explanations

## API Endpoints

- `POST /api/v1/analysis/analyze_flowchart` - Analyze flowchart structure and logic
- `POST /api/v1/codegen/generate_code` - Generate code from validated flowcharts
- `GET /health` - Health check endpoint

## Development

### Backend Testing
```bash
cd backend
pytest
```

### Frontend Testing  
```bash
cd frontend
npm test
```

## Educational Focus

This tool is designed specifically for learning programming concepts:
- **Algorithmic thinking**: Students plan their logic visually before coding
- **Error prevention**: Analysis catches common logic errors early
- **Code understanding**: Generated code explains programming concepts step-by-step
- **Multiple languages**: Compare how the same logic looks in different programming languages

## Technology Stack

- **Backend**: FastAPI, NetworkX, Pydantic
- **Frontend**: React, TypeScript, Draw.io integration
- **Analysis**: Custom rule engine for flowchart validation
- **Code Generation**: Educational code generators with extensive commenting 
