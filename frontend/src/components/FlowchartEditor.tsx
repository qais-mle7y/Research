import React, { useRef, useState, useEffect, useImperativeHandle, forwardRef } from 'react';
import {
  DrawIoEmbed,
  type UrlParameters,
  type EventSave,
  type EventAutoSave,
  type DrawIoEmbedRef,
  type EventExport
} from 'react-drawio';
import { parseDrawioXml, getBasicDiagramInfo, extractFlowchartElements, extractXmlFromSvg } from '../utils/flowchartParser';
import pako from 'pako';

// Define a minimal interface for the Draw.io configuration we expect to use
interface MinimalDrawIoConfig {
  defaultLibraries?: string; // e.g., "flowchart;general"
  enabledLibraries?: string[]; // e.g., ["flowchart", "general", "basic"]
  defaultEdgeStyle?: Record<string, string | number | boolean>; // More specific than 'any'
  // Add other configuration keys as needed
}

// Props for the FlowchartEditor component
interface FlowchartEditorProps {
  xml?: string;
  onSave?: (data: string) => void;
  onLoad?: () => void;
  configuration?: MinimalDrawIoConfig; // Use the minimal local interface
  // Add other props as needed based on react-drawio documentation
}

// Exposed methods interface for the ref
export interface FlowchartEditorRef {
  captureCurrentState: () => Promise<string>;
}

const DEFAULT_XML = '<mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel>';

const FlowchartEditor = forwardRef<FlowchartEditorRef, FlowchartEditorProps>(({ xml = DEFAULT_XML, onSave, onLoad, configuration }, ref) => {
  const drawioRef = useRef<DrawIoEmbedRef>(null);
  const capturePromiseResolver = useRef<{ resolve: (xml: string) => void; reject: (error: Error) => void; } | null>(null);
  const [currentXml, setCurrentXml] = useState<string>(xml);

  useEffect(() => {
    // Update internal currentXml if initialXml prop changes externally
    if (xml !== currentXml) {
        setCurrentXml(xml);
        // Note: The DrawIoEmbed component should ideally re-render with the new `xml` prop value.
        // Forcing a load via drawioRef.current?.loadDiagram(initialXml) here can sometimes be tricky
        // with component lifecycle and might not be necessary if `xml` prop correctly drives the editor content.
    }
  }, [xml]); // Only depend on xml to avoid loops if editor updates currentXml internally

  const _processAndLogXml = (xml: string, source: 'save' | 'auto-save' | 'manual-capture') => {
    setCurrentXml(xml);
    if (onSave) {
      onSave(xml);
    }
    
    // Debug: Log the raw XML to see its structure
    // console.log(`🔍 Raw XML from ${source}:`, xml.substring(0, 500) + (xml.length > 500 ? '...' : ''));
    
    // Perform parsing to catch errors early, even if not logging details here
    const doc = parseDrawioXml(xml);
    if (doc) {
      const info = getBasicDiagramInfo(doc); // Keep calls for any internal logic/errors
      const elements = extractFlowchartElements(doc);
      
      // Debug: Show all mxCell elements found
      if (doc.documentElement) {
        const allCells = doc.documentElement.getElementsByTagName('mxCell');
        // console.log(`📋 Found ${allCells.length} total mxCell elements:`);
        for (let i = 0; i < Math.min(allCells.length, 10); i++) {
          const cell = allCells[i];
          // console.log(`  Cell ${i}: id="${cell.getAttribute('id')}", value="${cell.getAttribute('value')}", vertex="${cell.getAttribute('vertex')}", edge="${cell.getAttribute('edge')}", parent="${cell.getAttribute('parent')}"`);
        }
        if (allCells.length > 10) {
          // console.log(`  ... and ${allCells.length - 10} more cells`);
        }
      }
      
      // Simple log to acknowledge parsing without being too verbose
      // console.log(`Editor ${source}: XML processed. Nodes: ${elements?.nodes?.length ?? 0}, Edges: ${elements?.edges?.length ?? 0}. Diagram: ${info?.rootTagName ?? 'N/A'}`);
    } else {
      // console.warn(`Editor ${source}: Failed to parse XML document.`);
    }
  };

  const handleLoad = (/*event: EventLoad*/) => { // event param can be commented if not used
    // console.log('Draw.io editor loaded.');
    if (onLoad) {
      onLoad();
    }
  };

  const handleSave = (event: EventSave) => {
    // console.log('🔥 Draw.io content saved by editor.');

    const data = event.xml; // In some configurations, this might be a data URI

    // Handle cases where onSave returns an SVG data URI instead of plain XML
    if (data && data.startsWith('data:image/svg+xml;base64,')) {
      console.warn('⚠️ Save event returned an SVG data URI, attempting fallback decoding...');
      try {
        const b64 = data.substring('data:image/svg+xml;base64,'.length);
        const svg = atob(b64);
        const embeddedXml = extractXmlFromSvg(svg);
        if (embeddedXml) {
          // console.log('✅ Successfully extracted XML from saved SVG.');
          _processAndLogXml(embeddedXml, 'save');
        } else {
          console.error('❌ Could not extract embedded XML from the saved SVG.');
        }
      } catch (e) {
        // console.error('❌ Failed to decode or process SVG from save event:', e);
      }
    } else if (data) {
      // Process as plain XML as expected
      _processAndLogXml(data, 'save');
    } else {
      console.error('❌ Save event triggered but returned no data.');
    }
  };

  const handleAutoSave = (event: EventAutoSave) => {
    // console.log('⚡ Draw.io content auto-saved by editor.');
    _processAndLogXml(event.xml, 'auto-save');
  };

  const handleOnExport = (event: EventExport) => {
    // console.log('Draw.io export event, format:', event.format, 'data length:', event.data?.length);
    if (!event.data) {
      if (capturePromiseResolver.current) {
        capturePromiseResolver.current.reject(new Error('Export failed, no data received.'));
        capturePromiseResolver.current = null;
      }
      return;
    }

    // Expect plain XML only
    if ((event.format as string) === 'xml' && event.data.trim().startsWith('<')) {
              // console.log('✅ Received plain XML from manual capture');
      _processAndLogXml(event.data, 'manual-capture');
      if (capturePromiseResolver.current) {
        capturePromiseResolver.current.resolve(event.data);
        capturePromiseResolver.current = null;
      }
    } else if (event.format === 'xmlsvg' || event.format === 'svg') {
      // Fallback path when editor only provides SVG export
      if (event.data.startsWith('data:image/svg+xml;base64,')) {
        try {
          const b64 = event.data.substring('data:image/svg+xml;base64,'.length);
          const svg = atob(b64);
          const embedded = extractXmlFromSvg(svg);
          if (embedded) {
            // console.log('✅ Extracted XML from fallback SVG export');
            _processAndLogXml(embedded, 'manual-capture');
            if (capturePromiseResolver.current) {
              capturePromiseResolver.current.resolve(embedded);
              capturePromiseResolver.current = null;
            }
          } else {
            throw new Error('No XML inside SVG');
          }
        } catch (e) {
          if (capturePromiseResolver.current) {
            capturePromiseResolver.current.reject(e instanceof Error ? e : new Error('SVG decode failed'));
            capturePromiseResolver.current = null;
          }
        }
      } else {
        if (capturePromiseResolver.current) {
          capturePromiseResolver.current.reject(new Error('SVG data URI expected'));
          capturePromiseResolver.current = null;
        }
      }
    } else {
      const msg = `Unsupported export format or invalid XML received: ${event.format}`;
      console.error(msg);
      if (capturePromiseResolver.current) {
        capturePromiseResolver.current.reject(new Error(msg));
        capturePromiseResolver.current = null;
      }
    }
  };

  // Manual capture function for external use
  const captureCurrentState = (): Promise<string> => {
    return new Promise((resolve, reject) => {
      // console.log('📤 Manual capture requested');
      if (capturePromiseResolver.current) {
        return reject(new Error('A capture is already in progress.'));
      }
      if (!drawioRef.current) {
        return reject(new Error('DrawIo ref not available'));
      }
      try {
        const inst: any = drawioRef.current;
        // 1️⃣ Try direct getXml() first
        if (typeof inst.getXml === 'function') {
          const xml: string | undefined = inst.getXml();
          if (xml && xml.trim().startsWith('<')) {
            // console.log('✅ Obtained XML via first getXml');
            _processAndLogXml(xml, 'manual-capture');
            return resolve(xml);
          }
        }

        // 1️⃣·b Retry getXml() once after 200 ms (editor sometimes not ready)
        setTimeout(() => {
          try {
            const retryXml: string | undefined = inst.getXml();
            if (retryXml && retryXml.trim().startsWith('<')) {
              // console.log('✅ Obtained XML via retry getXml');
              _processAndLogXml(retryXml, 'manual-capture');
              return resolve(retryXml);
            }
            return reject(new Error('Could not retrieve XML from editor (getXml returned empty).'));
          } catch (e) {
            return reject(e instanceof Error ? e : new Error('getXml retry failed'));
          }
        }, 200);

        // Also set up svg fallback if getXml is truly unavailable
        if (typeof inst.exportDiagram === 'function') {
          capturePromiseResolver.current = { resolve, reject };
          drawioRef.current.exportDiagram({ format: 'xmlsvg' });
        }

        // If we get here synchronously, wait for the retry.
        return;
      } catch (error) {
        reject(error instanceof Error ? error : new Error('Unknown export error'));
      }
    });
  };

  // Expose the captureCurrentState method through ref
  useImperativeHandle(ref, () => ({
    captureCurrentState
  }));

  const urlParams: any = {
    ui: 'kennedy',
    spin: true,
    autosave: 1,
    saveAndExit: 0,
    embed: 1, // Crucial for enabling embedding mode
    proto: 'json', // Crucial for enabling the postMessage API
    // libraries: true,
  };

  if (configuration?.defaultLibraries) {
    urlParams.libs = configuration.defaultLibraries;
  }
  if (configuration?.enabledLibraries) {
    urlParams.enabledLibraries = configuration.enabledLibraries.join(';');
  }

  return (
    <div 
      className="flowchart-editor-container" 
      role="application"
      aria-label="Flowchart diagramming editor"
    >
      <DrawIoEmbed
        ref={drawioRef}
        xml={currentXml}
        onLoad={handleLoad}
        onSave={handleSave}
        onAutoSave={handleAutoSave}
        onExport={handleOnExport}
        urlParameters={urlParams}
        configuration={configuration}
      />
    </div>
  );
});

FlowchartEditor.displayName = 'FlowchartEditor';

export default FlowchartEditor; 