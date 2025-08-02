import pako from 'pako';

export interface FlowchartNode {
  id: string;
  value?: string;
  style?: string;
  type?: string;
  vertex?: boolean;
  parentId?: string;
  color?: string; // Hex color extracted from style
  geometry?: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
}

export interface FlowchartEdge {
  id: string;
  value?: string;
  style?: string;
  edge?: boolean;
  parentId?: string;
  sourceId?: string;
  targetId?: string;
}

export interface FlowchartAnalysis {
  totalElements: number;
  startNodes: FlowchartNode[];
  endNodes: FlowchartNode[];
  decisionNodes: FlowchartNode[];
  processNodes: FlowchartNode[];
  ioNodes: FlowchartNode[]; // Combining input/output
  connections: FlowchartEdge[];
  issues: string[];
}

/**
 * Decodes the most common HTML entities that appear in Draw.io files.
 * We purposefully keep this lightweight instead of adding a full dependency.
 */
const decodeHtml = (raw: string): string =>
  raw
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&'); // run last to avoid double-decoding

/**
 * Parses a Draw.io XML string into an XMLDocument.
 * The function is tolerant to the various encodings Draw.io can use:
 *   1. Plain XML
 *   2. HTML-escaped XML (&lt;mxGraphModel&gt;...)
 *   3. URL/Base64/Deflate encoded content handled by `decodeDiagramContent`
 * If every attempt fails we return null and log the problem.
 */
export const parseDrawioXml = (raw: string): XMLDocument | null => {
  if (!raw || raw.trim() === '') {
    console.error('parseDrawioXml received an empty string');
    return null;
  }

  const attempts: string[] = [
    raw,
    decodeHtml(raw),
  ];

  // `decodeDiagramContent` covers URL, Base64 and deflate cases.
  const decodedViaHelper = decodeDiagramContent(raw);
  if (decodedViaHelper) {
    attempts.push(decodedViaHelper);
  }

  const parser = new DOMParser();

  for (const candidate of attempts) {
    try {
      const doc = parser.parseFromString(candidate, 'text/xml');
      if (doc.getElementsByTagName('parsererror').length === 0) {
        return doc;
      }
    } catch (err) {
      // Continue to next attempt.
    }
  }

  console.error('All parse attempts failed in parseDrawioXml');
  return null;
};

/**
 * A simple demonstration function to show basic interaction with the parsed XML.
 * This will be expanded in later subtasks.
 * @param xmlDoc The parsed XML Document.
 * @returns A simple object with some info, or null.
 */
export const getBasicDiagramInfo = (xmlDoc: XMLDocument | null): { rootTagName?: string; cellCount?: number } | null => {
  if (!xmlDoc || !xmlDoc.documentElement) {
    return null;
  }
  const rootElement = xmlDoc.documentElement;
  const cells = rootElement.getElementsByTagName('mxCell');
  return {
    rootTagName: rootElement.tagName,
    cellCount: cells.length,
  };
};

/**
 * Determines the flowchart node type based on shape styles from Draw.io
 * @param style The style string from Draw.io
 * @returns The detected shape type
 */
const detectShapeType = (style: string): string => {
  const lowerStyle = style.toLowerCase();
  
  // Oval/Ellipse shapes (terminals)
  if (lowerStyle.includes('ellipse') || lowerStyle.includes('oval')) {
    return 'oval';
  }
  
  // Diamond shapes (decisions)
  if (lowerStyle.includes('rhombus') || lowerStyle.includes('diamond')) {
    return 'diamond';
  }
  
  // Parallelogram shapes (input/output)
  if (lowerStyle.includes('parallelogram')) {
    return 'parallelogram';
  }
  
  // Rectangle shapes (processes)
  if (lowerStyle.includes('rounded=0') || 
      lowerStyle.includes('whiteSpace=wrap') || 
      lowerStyle.includes('rectangle') ||
      !lowerStyle.includes('ellipse') && !lowerStyle.includes('rhombus') && !lowerStyle.includes('parallelogram')) {
    return 'rectangle';
  }
  
  return 'rectangle'; // Default to rectangle for unknown shapes
};

/**
 * Extracts the fill color from a Draw.io style string
 * @param style The style string from Draw.io
 * @returns The hex color (with #) or default gray color
 */
const extractFillColor = (style: string): string => {
  if (!style) return '#f0f0f0'; // Default light gray
  
  // Look for fillColor=#RRGGBB or fillColor=RRGGBB patterns
  const fillColorMatch = style.match(/fillColor=([#]?[0-9a-fA-F]{6})/);
  if (fillColorMatch) {
    const color = fillColorMatch[1];
    return color.startsWith('#') ? color : `#${color}`;
  }
  
  // Look for fillColor=#RGB patterns (3 digits)
  const fillColorShortMatch = style.match(/fillColor=([#]?[0-9a-fA-F]{3})/);
  if (fillColorShortMatch) {
    const color = fillColorShortMatch[1];
    const hexColor = color.startsWith('#') ? color.slice(1) : color;
    // Expand 3-digit hex to 6-digit hex
    const expandedColor = hexColor.split('').map(c => c + c).join('');
    return `#${expandedColor}`;
  }
  
  // Check for some common named colors that Draw.io might use
  if (style.includes('fillColor=red')) return '#ff0000';
  if (style.includes('fillColor=blue')) return '#0000ff';
  if (style.includes('fillColor=green')) return '#00ff00';
  if (style.includes('fillColor=yellow')) return '#ffff00';
  if (style.includes('fillColor=orange')) return '#ffa500';
  if (style.includes('fillColor=purple')) return '#800080';
  if (style.includes('fillColor=pink')) return '#ffc0cb';
  if (style.includes('fillColor=cyan')) return '#00ffff';
  if (style.includes('fillColor=white')) return '#ffffff';
  if (style.includes('fillColor=black')) return '#000000';
  
  return '#f0f0f0'; // Default light gray
};

/**
 * Analyzes node content to determine semantic type
 * @param value The text content of the node
 * @returns The detected semantic type
 */
const analyzeNodeContent = (value: string): string => {
  if (!value) return 'unknown';
  
  const lowerValue = value.toLowerCase().trim();
  
  // Start keywords
  const startKeywords = ['start', 'begin', 'initialize', 'init', 'launch', 'commence', 'open'];
  if (startKeywords.some(keyword => lowerValue.includes(keyword))) {
    return 'start';
  }
  
  // End keywords  
  const endKeywords = ['end', 'stop', 'finish', 'terminate', 'exit', 'close', 'complete', 'done'];
  if (endKeywords.some(keyword => lowerValue.includes(keyword))) {
    return 'end';
  }
  
  // Input keywords
  const inputKeywords = ['input', 'read', 'enter', 'get', 'scan', 'prompt', 'ask'];
  if (inputKeywords.some(keyword => lowerValue.includes(keyword))) {
    return 'input';
  }
  
  // Output keywords
  const outputKeywords = ['output', 'print', 'display', 'show', 'write', 'say', 'tell'];
  if (outputKeywords.some(keyword => lowerValue.includes(keyword))) {
    return 'output';
  }
  
  // Decision/condition keywords
  const decisionKeywords = ['if', 'while', 'for', 'check', 'test', 'compare', '?', '==', '!=', '<', '>', '<=', '>='];
  if (decisionKeywords.some(keyword => lowerValue.includes(keyword))) {
    return 'decision';
  }
  
  // Process keywords (assignment, calculation, etc.)
  const processKeywords = ['=', 'calculate', 'compute', 'set', 'assign', 'update', 'increment', 'decrement', '+', '-', '*', '/'];
  if (processKeywords.some(keyword => lowerValue.includes(keyword))) {
    return 'process';
  }
  
  return 'process'; // Default to process for text-containing nodes
};

/**
 * Determines final node type by combining shape and content analysis with graph topology
 * @param shapeType The detected shape type
 * @param contentType The detected content type  
 * @param hasIncoming Whether the node has incoming edges
 * @param hasOutgoing Whether the node has outgoing edges
 * @returns The final node type
 */
const determineNodeType = (
  shapeType: string, 
  contentType: string, 
  hasIncoming: boolean, 
  hasOutgoing: boolean
): string => {
  // Oval shapes are typically terminals
  if (shapeType === 'oval') {
    // No incoming edges = start node
    if (!hasIncoming && hasOutgoing) {
      return 'start';
    }
    // No outgoing edges = end node  
    if (hasIncoming && !hasOutgoing) {
      return 'end';
    }
    // Use content analysis for ambiguous cases
    if (contentType === 'start' || contentType === 'end') {
      return contentType;
    }
    // Default for isolated ovals
    return hasIncoming ? 'end' : 'start';
  }
  
  // Diamond shapes are decisions
  if (shapeType === 'diamond') {
    return 'decision';
  }
  
  // Parallelograms are typically I/O
  if (shapeType === 'parallelogram') {
    if (contentType === 'input' || contentType === 'output') {
      return contentType;
    }
    // Default to input for parallelograms
    return 'input';
  }
  
  // Rectangle shapes - use content analysis
  if (shapeType === 'rectangle') {
    // If content suggests it's a terminal and graph position supports it
    if (contentType === 'start' && !hasIncoming) {
      return 'start';
    }
    if (contentType === 'end' && !hasOutgoing) {
      return 'end';
    }
    if (contentType === 'decision') {
      return 'decision';
    }
    if (contentType === 'input' || contentType === 'output') {
      return contentType;
    }
    // Default to process
    return 'process';
  }
  
  return 'process';
};

// TODO: Add unit tests for this function with various compressed diagram samples
// to prevent future regressions in decoding logic.
const b64ToUint8 = (b64: string): Uint8Array =>
  Uint8Array.from(atob(b64), c => c.charCodeAt(0));

export const decodeDiagramContent = (data: string): string => {
  if (!data) return '';

  // 0. If the string already looks like XML just return it
  if (data.trim().startsWith('<')) {
    return data;
  }

  // 1. The "official" Draw.io path:  base64  ->  inflateRaw  ->  URI decode
  try {
    const inflated = pako.inflateRaw(b64ToUint8(data), { to: 'string' });
    const xml = decodeURIComponent(inflated);
    if (xml.trim().startsWith('<')) {
      // console.log('✅ Content decoded via Base64 + inflateRaw.');
      return xml;
    }
  } catch { /* ignore & try fall-backs */ }

  // 2. Sometimes the whole base64 block is first URI-encoded
  try {
    const uriDecoded = decodeURIComponent(data);
    const inflated = pako.inflateRaw(b64ToUint8(uriDecoded), { to: 'string' });
    const xml = decodeURIComponent(inflated);
    if (xml.trim().startsWith('<')) {
      // console.log('✅ Content decoded via URL + Base64 + inflateRaw.');
      return xml;
    }
  } catch { /* ignore & try next fall-back */ }

  // 3. Older, uncompressed diagrams are just HTML-escaped XML
  const htmlDecoded = decodeHtml(data);
  if (htmlDecoded.trim().startsWith('<')) {
    // console.log('✅ Content decoded via HTML entity decoding.');
    return htmlDecoded;
  }

  console.error('All decoding attempts failed in decodeDiagramContent.');
  return ''; // Return empty so caller knows it failed
};

/**
 * Extracts structured node and edge data from a parsed Draw.io XML document.
 * Enhanced version that works with any user-created flowchart and robust decoding.
 * @param xmlDoc The parsed XML Document.
 * @returns An object containing arrays of nodes and edges, or null if input is invalid.
 */
export const extractFlowchartElements = (xmlDoc: XMLDocument | null): { nodes: FlowchartNode[]; edges: FlowchartEdge[] } | null => {
  if (!xmlDoc || !xmlDoc.documentElement) {
    return null;
  }

  try {
    let workingDoc = xmlDoc;
    
    // Check if this is an mxfile format that needs diagram decoding
    if (xmlDoc.documentElement.tagName === 'mxfile') {
      // console.log('🔍 Detected mxfile format, extracting diagram content...');
      const diagramNode = xmlDoc.getElementsByTagName('diagram')[0];
      if (diagramNode) {
        const diagramContent = diagramNode.textContent || '';
        if (diagramContent) {
          const decodedXml = decodeDiagramContent(diagramContent);
          if (decodedXml) {
            // console.log('✅ Successfully decoded diagram content');
            
            // Parse the decoded XML
            const parser = new DOMParser();
            workingDoc = parser.parseFromString(decodedXml, 'text/xml');
            
            if (workingDoc.getElementsByTagName('parsererror').length > 0) {
              console.error('❌ Error parsing decoded diagram XML');
              return null;
            }
          } else {
            console.error('❌ Failed to decode diagram content, it may be empty or invalid.');
            return null;
          }
        }
      }
    }

    const nodes: FlowchartNode[] = [];
    const edges: FlowchartEdge[] = [];
    const cells = workingDoc.getElementsByTagName('mxCell');

    // console.log(`🔍 Enhanced parser starting analysis of ${cells.length} XML cells`);

    // If we still have 0 cells, try fallback decoding methods
    if (cells.length === 0) {
      // console.log('⚠️ Found 0 mxCell elements, attempting fallback decoding...');
      
      // Try to extract and decode any text content that might be encoded
      const allTextNodes = workingDoc.evaluate('//text()', workingDoc, null, XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, null);
      for (let i = 0; i < allTextNodes.snapshotLength; i++) {
        const textNode = allTextNodes.snapshotItem(i);
        if (textNode && textNode.textContent && textNode.textContent.trim().length > 50) {
          const decodedXml = decodeDiagramContent(textNode.textContent.trim());
          if (decodedXml) {
            // console.log('✅ Found and decoded XML from text node');
            const parser = new DOMParser();
            workingDoc = parser.parseFromString(decodedXml, 'text/xml');
            const newCells = workingDoc.getElementsByTagName('mxCell');
            if (newCells.length > 0) {
              // console.log(`🎉 Fallback decoding found ${newCells.length} cells!`);
              break;
            }
          }
        }
      }
    }

    // Re-get cells after potential fallback decoding
    const finalCells = workingDoc.getElementsByTagName('mxCell');
    // console.log(`🔍 Final analysis starting with ${finalCells.length} XML cells`);

    // First pass: extract all nodes and edges
    const nodeMap = new Map<string, { node: FlowchartNode; incoming: Set<string>; outgoing: Set<string> }>();
    
    for (let i = 0; i < finalCells.length; i++) {
      const cell = finalCells[i];
      const id = cell.getAttribute('id');
      if (!id) continue; // Skip cells without ID

      // Handle potential MathML content by extracting text from it
      let value = cell.getAttribute('value') || undefined;
      if (value && value.includes('<math')) {
          const valueDoc = new DOMParser().parseFromString(value, 'text/xml');
          const mathNodes = valueDoc.getElementsByTagName('mn');
          if (mathNodes.length > 0) {
              value = Array.from(mathNodes).map(n => n.textContent).join('');
          }
      }

      const style = cell.getAttribute('style') || undefined;
      const parentId = cell.getAttribute('parent') || undefined;

      if (cell.getAttribute('vertex') === '1') {
        const geometryElement = cell.getElementsByTagName('mxGeometry')[0];
        const geometry = geometryElement ? {
          x: parseFloat(geometryElement.getAttribute('x') || '0'),
          y: parseFloat(geometryElement.getAttribute('y') || '0'),
          width: parseFloat(geometryElement.getAttribute('width') || '0'),
          height: parseFloat(geometryElement.getAttribute('height') || '0'),
        } : undefined;

        const node: FlowchartNode = {
          id,
          value,
          style,
          type: undefined, // Will be determined later
          vertex: true,
          parentId,
          color: extractFillColor(style || ''),
          geometry,
        };
        
        nodeMap.set(id, {
          node,
          incoming: new Set(),
          outgoing: new Set()
        });
      } else if (cell.getAttribute('edge') === '1') {
        const sourceId = cell.getAttribute('source') || undefined;
        const targetId = cell.getAttribute('target') || undefined;
        
        const edge: FlowchartEdge = {
          id,
          value,
          style,
          edge: true,
          parentId,
          sourceId,
          targetId,
        };
        
        edges.push(edge);
        
        // Track incoming/outgoing connections
        if (sourceId && targetId) {
          const sourceData = nodeMap.get(sourceId);
          const targetData = nodeMap.get(targetId);
          
          if (sourceData) {
            sourceData.outgoing.add(targetId);
          }
          if (targetData) {
            targetData.incoming.add(sourceId);
          }
        }
      }
    }

    // console.log(`📊 Found ${nodeMap.size} nodes and ${edges.length} edges`);

    // Second pass: determine types for all nodes using enhanced detection
    const typeStats = { start: 0, end: 0, process: 0, decision: 0, input: 0, output: 0, unknown: 0 };
    
    for (const [nodeId, nodeData] of nodeMap) {
      const { node, incoming, outgoing } = nodeData;
      
      // console.log(
      //   `🔎 Examining node "${nodeId}": value="${node.value}", parent="${node.parentId}", vertex="${node.vertex}"`,
      // );
      // Skip the top-level container nodes (diagram root and default layer)
      // All actual flowchart elements will have a parent of '1' (the default layer)
      if (node.parentId === '0' || node.parentId === '1' && !node.vertex) {
        // console.log(
        //   `  ⚠️ Skipping node "${nodeId}": has parent "${node.parentId}" and is not a vertex (likely a layer or root).`,
        // );
        continue;
      }
      
      // Skip text-only labels that are used for edge annotations
      // These typically have styles containing "text;html=1" and are not actual flowchart shapes
      if (node.style && node.style.includes('text;html=1')) {
        // Additional check: text labels usually have simple text content and are positioned near edges
        // They should not be treated as flowchart nodes
        continue;
      }
      
      // Basic validation: ensure node has a value or is a container
      if ((!node.value || node.value.trim() === '') && (node.style && !node.style.includes('group'))) {
        // console.log(`  ⚠️ Skipping node "${nodeId}": no meaningful content (value: "${node.value}")`);
        continue;
      }
      
      const shapeType = detectShapeType(node.style || '');
      const contentType = analyzeNodeContent(node.value || '');
      const finalType = determineNodeType(shapeType, contentType, incoming.size > 0, outgoing.size > 0);
      
      node.type = finalType;
      nodes.push(node);
      
      // Count types for statistics
      if (Object.prototype.hasOwnProperty.call(typeStats, finalType)) {
        typeStats[finalType as keyof typeof typeStats]++;
      } else {
        typeStats.unknown++;
      }
      
      // console.log(`🏷️ Node "${nodeId}": "${node.value}" → shape:${shapeType}, content:${contentType}, final:${finalType} (in:${incoming.size}, out:${outgoing.size})`);
    }

    // console.log(`✅ Enhanced parser detected: ${typeStats.start} start, ${typeStats.end} end, ${typeStats.decision} decision, ${typeStats.process} process, ${typeStats.input} input, ${typeStats.output} output, ${typeStats.unknown} unknown nodes`);

    return { nodes, edges };
  } catch (error) {
    console.error('❌ Error during flowchart element extraction:', error);
    return null;
  }
};

// Helper to build a graph for cycle detection
const buildGraph = (edges: FlowchartEdge[]): Record<string, string[]> => {
  const graph: Record<string, string[]> = {};
  edges.forEach(edge => {
    if (edge.sourceId && edge.targetId) {
      if (!graph[edge.sourceId]) {
        graph[edge.sourceId] = [];
      }
      graph[edge.sourceId].push(edge.targetId);
    }
  });
  return graph;
};

// Helper for cycle detection using DFS
const detectCycles = (nodes: FlowchartNode[], edges: FlowchartEdge[]): string[] => {
  const graph = buildGraph(edges);
  const visited = new Set<string>();
  const recursionStack = new Set<string>();
  const issues: string[] = [];

  const hasCycle = (nodeId: string): boolean => {
    if (recursionStack.has(nodeId)) {
      return true; // Cycle detected
    }
    if (visited.has(nodeId)) {
      return false; // Already visited and no cycle found from this path
    }

    visited.add(nodeId);
    recursionStack.add(nodeId);

    const neighbors = graph[nodeId] || [];
    for (const neighbor of neighbors) {
      if (hasCycle(neighbor)) {
        return true;
      }
    }

    recursionStack.delete(nodeId);
    return false;
  };
  
  for (const node of nodes) {
    if (!visited.has(node.id)) {
      if (hasCycle(node.id)) {
        issues.push('Potential infinite loop detected in the flowchart.');
        // Once one cycle is found, we can stop to avoid redundant messages.
        break; 
      }
    }
  }
  
  return issues;
};

/**
 * Performs a comprehensive analysis of the given flowchart elements.
 * @param elements The extracted nodes and edges from the flowchart.
 * @returns An analysis object with categorized nodes and a list of issues.
 */
export const analyzeFlowchart = (
  elements: { nodes: FlowchartNode[]; edges: FlowchartEdge[] } | null
): FlowchartAnalysis | null => {
  if (!elements || elements.nodes.length === 0) {
    return null;
  }
  
  const { nodes, edges } = elements;

  const analysis: FlowchartAnalysis = {
    totalElements: nodes.length + edges.length,
    startNodes: [],
    endNodes: [],
    decisionNodes: [],
    processNodes: [],
    ioNodes: [],
    connections: edges,
    issues: [],
  };

  // 1. Categorize nodes based on their pre-assigned type
  nodes.forEach(node => {
    switch (node.type) {
      case 'start':
        analysis.startNodes.push(node);
        break;
      case 'end':
        analysis.endNodes.push(node);
        break;
      case 'decision':
        analysis.decisionNodes.push(node);
        break;
      case 'input':
      case 'output':
        analysis.ioNodes.push(node);
        break;
      case 'process':
      default:
        analysis.processNodes.push(node);
        break;
    }
  });

  // 2. Perform structural validation
  // Check for start nodes
  if (analysis.startNodes.length === 0) {
    analysis.issues.push('Flowchart must have exactly one start node, but none were found.');
  } else if (analysis.startNodes.length > 1) {
    analysis.issues.push(`Flowchart must have exactly one start node, but ${analysis.startNodes.length} were found.`);
  }

  // Check for end nodes
  if (analysis.endNodes.length === 0) {
    analysis.issues.push('Flowchart must have at least one end node, but none were found.');
  }
  
  // 3. Check for disconnected nodes
  if (nodes.length > 1) {
      const connectedNodeIds = new Set<string>();
      edges.forEach(edge => {
          if (edge.sourceId) connectedNodeIds.add(edge.sourceId);
          if (edge.targetId) connectedNodeIds.add(edge.targetId);
      });

      nodes.forEach(node => {
          if (!connectedNodeIds.has(node.id)) {
              analysis.issues.push(`Node "${node.value || `(ID: ${node.id})`}" is disconnected.`);
          }
      });
  }

  // 4. Check for infinite loops
  const cycleIssues = detectCycles(nodes, edges);
  analysis.issues.push(...cycleIssues);

  // 5. Validate decision branches and dead ends
  const outgoingConnections: Record<string, number> = {};
  edges.forEach(edge => {
    if (edge.sourceId) {
      outgoingConnections[edge.sourceId] = (outgoingConnections[edge.sourceId] || 0) + 1;
    }
  });

  analysis.decisionNodes.forEach(node => {
    const outgoingCount = outgoingConnections[node.id] || 0;
    if (outgoingCount < 2) {
      analysis.issues.push(`Decision node "${node.value || `(ID: ${node.id})`}" should have at least two outgoing branches, but has ${outgoingCount}.`);
    }
  });
  
  // Check for nodes without outgoing paths (dead ends that are not 'end' nodes)
  const deadEndCandidates = [...analysis.processNodes, ...analysis.ioNodes, ...analysis.decisionNodes];
   deadEndCandidates.forEach(node => {
      const outgoingCount = outgoingConnections[node.id] || 0;
      if (outgoingCount === 0) {
          analysis.issues.push(`${node.type?.charAt(0).toUpperCase() + node.type!.slice(1)} node "${node.value || `(ID: ${node.id})`}" is a dead end.`);
      }
  });

  return analysis;
};

/**
 * Extracts the raw XML diagram data embedded within an SVG file.
 * Draw.io stores the diagram source inside a `content` attribute of the `<svg>` tag,
 * @param svgContent The string content of the SVG file.
 * @returns The extracted Draw.io XML string, or null if not found.
 */
export const extractXmlFromSvg = (svgContent: string): string | null => {
  try {
    const parser = new DOMParser();
    const svgDoc = parser.parseFromString(svgContent, 'image/svg+xml');
    const rootSvg = svgDoc.documentElement;

    if (rootSvg && rootSvg.tagName.toLowerCase() === 'svg' && rootSvg.hasAttribute('content')) {
      const content = rootSvg.getAttribute('content');
      if (content) {
        // console.log('🔍 Found content attribute, HTML decoded:', content.substring(0, 150) + '...');
        
        // The content is the actual XML, sometimes compressed.
        // First, check if it's already valid XML.
        const tempDoc = parser.parseFromString(content, 'text/xml');
        if (!tempDoc.getElementsByTagName('parsererror').length) {
            // console.log('🎉 Found draw.io XML directly in content attribute');
            return content;
        }

        // If direct parsing fails, it's likely compressed.
        // console.log('🤔 Direct XML parsing failed, attempting decompression...');
        try {
          const decodedData = atob(content);
          const inflated = pako.inflate(new Uint8Array(decodedData.split('').map(char => char.charCodeAt(0))), { to: 'string' });
          const decodedUri = decodeURIComponent(inflated);

          // console.log('✅ Successfully decompressed XML from content attribute');
          // If the XML is still wrapped inside <mxfile> with encoded <diagram>, unwrap it
          try {
            const doc2 = parser.parseFromString(decodedUri, 'text/xml');
            const mxFile = doc2.documentElement;
            if (mxFile && mxFile.tagName === 'mxfile') {
              const diagramNode = mxFile.getElementsByTagName('diagram')[0];
              if (diagramNode) {
                const diagramContent = diagramNode.textContent || '';
                // decode diagram content
                const decodedB64 = atob(diagramContent);
                const inflated2 = pako.inflate(
                  new Uint8Array(decodedB64.split('').map(c => c.charCodeAt(0))),
                  { to: 'string' }
                );
                const finalXml = decodeURIComponent(inflated2);
                // console.log('✅ Unwrapped mxGraphModel from <diagram>');
                return finalXml;
              }
            }
          } catch (e) {
            console.warn('Could not unwrap <mxfile>: ',e);
          }
          return decodedUri;
        } catch (e) {
          console.error('❌ Decompression failed:', e);
          // Fallback to original content if decompression fails
          return content;
        }
      }
    }
    return null; // No content attribute found
  } catch (error) {
    console.error('❌ Error while extracting XML from SVG:', error);
    return null;
  }
}; 