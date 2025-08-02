import { parseDrawioXml, extractFlowchartElements, decodeDiagramContent, extractXmlFromSvg } from './flowchartParser';

describe('flowchartParser', () => {
  describe('extractFlowchartElements', () => {
    it('should correctly extract node geometry', () => {
      const xml = `
        <mxGraphModel>
          <root>
            <mxCell id="0" />
            <mxCell id="1" parent="0" />
            <mxCell id="2" value="Start" style="ellipse" vertex="1" parent="1">
              <mxGeometry x="10" y="20" width="80" height="40" as="geometry" />
            </mxCell>
          </root>
        </mxGraphModel>
      `;
      const doc = parseDrawioXml(xml);
      const elements = extractFlowchartElements(doc);
      expect(elements).not.toBeNull();
      expect(elements?.nodes).toHaveLength(1);
      const node = elements!.nodes[0];
      expect(node.geometry).toBeDefined();
      expect(node.geometry?.x).toBe(10);
      expect(node.geometry?.y).toBe(20);
      expect(node.geometry?.width).toBe(80);
      expect(node.geometry?.height).toBe(40);
    });

    it('should correctly parse MathML content in a node value', () => {
        const xml = `
          <mxGraphModel>
            <root>
              <mxCell id="0" />
              <mxCell id="1" parent="0" />
              <mxCell id="2" value="&lt;math xmlns=&quot;http://www.w3.org/1998/Math/MathML&quot;&gt;&lt;mn&gt;123&lt;/mn&gt;&lt;/math&gt;" style="rectangle" vertex="1" parent="1">
                <mxGeometry as="geometry" />
              </mxCell>
            </root>
          </mxGraphModel>
        `;
        const doc = parseDrawioXml(xml);
        const elements = extractFlowchartElements(doc);
        expect(elements).not.toBeNull();
        expect(elements?.nodes).toHaveLength(1);
        const node = elements!.nodes[0];
        expect(node.value).toBe('123');
      });
  });

  describe('decodeDiagramContent', () => {
    // This is a real compressed string from a draw.io diagram
    const compressed = 'jZJNc5swDIZ/DcdJgfHYdjvtpE4dO3U6TpOe2DBGrJkQE6d+/VRiNC2HnW46k+EX+PLeF8sSks/OK8tV1kGKnIMyD1xGkQF5GzifwG+KJBJtISklO4oUuI9IURM5M6C6hG22x0T40c4y7pC6bs6S1MvS1JtSInEwM1tWvHkFf2K4lXkL1mZl2LzYg/b0hLd3HkI9NwefeR0N+Tdj4Nv7DwefX8N+3J/n9PuyLhN4J+aV9Wb0gP/4/w2+SSTpB5uD6/RAG/dI0C5vN9a19S6L2bK05oD1cR1vUvX2f0q8X7M4a8qAFc1DqA3W3zH4AIjA+L0h8kE0a/QY=';
    const expectedXml = '<mxGraphModel dx="816" dy="611" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/><mxCell id="2" value="Start" style="ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1"><mxGeometry x="360" y="100" width="120" height="80" as="geometry"/></mxCell></root></mxGraphModel>';
    
    it('should decode base64+deflate encoded content', () => {
      const decoded = decodeDiagramContent(compressed);
      expect(decoded).toBe(expectedXml);
    });

    it('should decode URI-encoded, base64+deflate content', () => {
        const uriEncoded = encodeURIComponent(compressed);
        const decoded = decodeDiagramContent(uriEncoded);
        expect(decoded).toBe(expectedXml);
    });

    it('should decode HTML-escaped content', () => {
        const htmlEscaped = '&lt;mxGraphModel&gt;&lt;root&gt;&lt;mxCell id="0"/&gt;&lt;/root&gt;&lt;/mxGraphModel&gt;';
        const expected = '<mxGraphModel><root><mxCell id="0"/></root></mxGraphModel>';
        const decoded = decodeDiagramContent(htmlEscaped);
        expect(decoded).toBe(expected);
    });
  });

  describe('extractXmlFromSvg', () => {
    it('should extract embedded XML from an SVG', () => {
        const svgContent = `
            <svg xmlns="http://www.w3.org/2000/svg" content="&lt;mxfile host=&quot;app.diagrams.net&quot;&gt;&lt;diagram id=&quot;...&quot; name=&quot;Page-1&quot;&gt;jZJNc5swDIZ/DcdJgfHYdjvtpE4dO3U6TpOe2DBGrJkQE6d+/VRiNC2HnW46k+EX+PLeF8sSks/OK8tV1kGKnIMyD1xGkQF5GzifwG+KJBJtISklO4oUuI9IURM5M6C6hG22x0T40c4y7pC6bs6S1MvS1JtSInEwM1tWvHkFf2K4lXkL1mZl2LzYg/b0hLd3HkI9NwefeR0N+Tdj4Nv7DwefX8N+3J/n9PuyLhN4J+aV9Wb0gP/4/w2+SSTpB5uD6/RAG/dI0C5vN9a19S6L2bK05oD1cR1vUvX2f0q8X7M4a8qAFc1DqA3W3zH4AIjA+L0h8kE0a/QY=&lt;/diagram&gt;&lt;/mxfile&gt;">
            </svg>
        `;
        const extracted = extractXmlFromSvg(svgContent);
        // We might get the decoded content directly, let's parse that to be sure
        const doc = parseDrawioXml(extracted!);
        const finalXml = new XMLSerializer().serializeToString(doc!);
        //This is a bit of a hacky way to test this, but it works for now.
        //A better way would be to compare the objects, but the XML serialization is not stable.
        expect(finalXml.includes('<mxCell id="2" value="Start" style="ellipse;whiteSpace=wrap;html=1;" vertex="1" parent="1">')).toBe(true);
    });
  });
}); 