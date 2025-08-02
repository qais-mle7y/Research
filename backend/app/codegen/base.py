from app.schemas.flowchart import FlowchartNodeSchema
from typing import List
import re

class EducationalCodeGeneratorBase:
    """
    Provides base functionality for educational code generators, including
    identifier cleaning, variable extraction, and educational comment generation.
    """
    
    def _clean_identifier(self, text: str) -> str:
        """
        Converts arbitrary flowchart text into a valid, safe programming identifier.
        """
        if not text:
            return "unnamed_variable"
        
        # Keep only letters, numbers, and underscores
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', text.strip())
        # Collapse multiple consecutive underscores
        cleaned = re.sub(r'_{2,}', '_', cleaned)
        # Remove leading/trailing underscores
        cleaned = cleaned.strip('_')
        
        # Ensure the identifier does not start with a number
        if not cleaned or cleaned[0].isdigit():
            cleaned = f"var_{cleaned}" if cleaned else "unnamed_variable"
            
        return cleaned[:50]  # Enforce a reasonable length limit

    def _extract_variables_from_text(self, text: str) -> List[str]:
        """
        A simple heuristic to extract potential variable names from node text.
        Looks for common assignment and I/O keywords.
        """
        if not text:
            return []
        
        # Regex to find words following assignment or I/O keywords.
        # e.g., "x = 10", "set value", "input name", "print result"
        patterns = [
            r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=',  # Assignment: my_var = ...
            r'(?:let|set|const|var)\s+([a-zA-Z_][a-zA-Z0-9_]*)', # Declaration: let my_var
            r'(?:input|read|get|enter)\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # Input: input my_var
            r'(?:print|display|show|output)\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # Output: print my_var
        ]
        
        variables = []
        for pattern in patterns:
            # Find all non-overlapping matches
            matches = re.findall(pattern, text.lower())
            variables.extend(matches)
        
        # Clean and return unique variables
        return sorted(list(set([self._clean_identifier(var) for var in variables if var])))

    def _wrap_with_color(self, lines: List[str], color: str, is_comment: bool = False) -> List[str]:
        """
        Wraps code lines with HTML span tags for coloring.
        Creates a visually distinctive system that connects code to flowchart nodes.
        
        Args:
            lines: List of code lines to wrap
            color: Hex color (e.g., '#ff0000')
            is_comment: Whether these are comment lines (for opacity adjustment)
            
        Returns:
            List of HTML-wrapped lines
        """
        if not lines:
            return lines
        
        # Use consistent, readable color for all comments
        if is_comment:
            # Process each comment line to add special styling for educational elements
            wrapped_lines = []
            for line in lines:
                if line.strip():
                    # Check for special educational elements
                    if "Basic concept:" in line:
                        # Use a nice blue color for basic concepts
                        styled_line = self._style_educational_element(line, "#2980b9", "Basic concept:")  # Professional blue
                        wrapped_lines.append(styled_line)
                    elif "Learn more:" in line:
                        # Use green color for learn more links
                        styled_line = self._style_educational_element(line, "#27ae60", "Learn more:")  # Professional green
                        wrapped_lines.append(styled_line)
                    else:
                        # Regular comment styling
                        wrapped_lines.append(f'<span style="color: #666666;">{line}</span>')
                else:
                    wrapped_lines.append(line)  # Keep empty lines as-is
            return wrapped_lines
        else:
            # For code lines, create a creative visual system
            readable_color = self._ensure_readable_color(color)
            # Add a subtle background color and left border for visual connection
            bg_color = self._get_subtle_background(color)
            style = f"color: {readable_color}; background-color: {bg_color}; border-left: 3px solid {readable_color}; padding-left: 8px; margin-left: -8px;"
        
            wrapped_lines = []
            for line in lines:
                if line.strip():  # Only wrap non-empty lines
                    wrapped_lines.append(f'<span style="{style}">{line}</span>')
                else:
                    wrapped_lines.append(line)  # Keep empty lines as-is
            
            return wrapped_lines
    
    def _style_educational_element(self, line: str, element_color: str, element_text: str) -> str:
        """
        Styles educational elements like 'Basic concept:' and 'Learn more:' with special colors.
        Makes 'Learn more:' links clickable when they contain URLs.
        """
        # Split the line to style only the educational element part
        if element_text in line:
            parts = line.split(element_text, 1)
            if len(parts) == 2:
                prefix = parts[0]
                suffix = parts[1]
                
                # Special handling for "Learn more:" to make links clickable
                if element_text == "Learn more:" and suffix.strip():
                    # Extract URL from the suffix
                    url = self._extract_url_from_text(suffix)
                    if url:
                        # Create clickable link
                        clickable_suffix = suffix.replace(url, f'<a href="{url}" target="_blank" style="color: {element_color}; text-decoration: underline;">{url}</a>')
                        return (f'<span style="color: #666666;">{prefix}</span>'
                               f'<span style="color: {element_color}; font-weight: bold;">{element_text}</span>'
                               f'<span style="color: #666666;">{clickable_suffix}</span>')
                
                # Regular styling for non-link elements or Basic concept
                return (f'<span style="color: #666666;">{prefix}</span>'
                       f'<span style="color: {element_color}; font-weight: bold;">{element_text}</span>'
                       f'<span style="color: #666666;">{suffix}</span>')
        
        # Fallback to regular gray styling
        return f'<span style="color: #666666;">{line}</span>'
    
    def _extract_url_from_text(self, text: str) -> str:
        """
        Extracts URL from text. Looks for http:// or https:// patterns.
        """
        import re
        # Pattern to match URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        match = re.search(url_pattern, text)
        return match.group(0) if match else ""

    def _ensure_readable_color(self, color: str) -> str:
        """
        Ensures a color is dark enough to be readable on a white background.
        Converts light colors to darker, more readable versions.
        """
        if not color or not color.startswith('#'):
            return '#333333'  # Default dark gray
        
        try:
            # Remove the # and convert to RGB
            hex_color = color[1:]
            if len(hex_color) == 3:
                # Expand 3-digit hex to 6-digit
                hex_color = ''.join([c*2 for c in hex_color])
            
            if len(hex_color) != 6:
                return '#333333'
            
            # Convert to RGB values
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16) 
            b = int(hex_color[4:6], 16)
            
            # Calculate luminance (perceived brightness)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            
            # Check for problematic bright colors and handle them specially
            # Bright green, bright yellow, bright cyan, bright magenta, etc.
            if (r > 200 and g > 200) or (g > 200 and b > 200) or (r > 200 and b > 200):
                # Very bright colors - darken significantly
                r = max(0, min(120, int(r * 0.3)))
                g = max(0, min(120, int(g * 0.3)))
                b = max(0, min(120, int(b * 0.3)))
                return f'#{r:02x}{g:02x}{b:02x}'
            
            # If too light (luminance > 0.5), darken it
            elif luminance > 0.5:
                # Darken by reducing RGB values
                r = max(0, int(r * 0.5))
                g = max(0, int(g * 0.5))
                b = max(0, int(b * 0.5))
                return f'#{r:02x}{g:02x}{b:02x}'
            
            # If reasonably dark, use as-is
            return color
            
        except ValueError:
            return '#333333'  # Fallback to dark gray

    def _get_subtle_background(self, color: str) -> str:
        """
        Creates a very subtle background color based on the node color.
        This provides visual connection without overwhelming the text.
        """
        if not color or not color.startswith('#'):
            return 'rgba(240, 240, 240, 0.1)'  # Very light gray
        
        try:
            # Remove the # and convert to RGB
            hex_color = color[1:]
            if len(hex_color) == 3:
                # Expand 3-digit hex to 6-digit
                hex_color = ''.join([c*2 for c in hex_color])
            
            if len(hex_color) != 6:
                return 'rgba(240, 240, 240, 0.1)'
            
            # Convert to RGB values
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16) 
            b = int(hex_color[4:6], 16)
            
            # Create a very subtle background (5% opacity)
            return f'rgba({r}, {g}, {b}, 0.05)'
            
        except ValueError:
            return 'rgba(240, 240, 240, 0.1)'

    def _get_educational_comment(self, node: FlowchartNodeSchema) -> str:
        """
        Generates a detailed, educational comment explaining a flowchart node's purpose.
        Now includes simpler explanations and hyperlinks to educational resources.
        """
        node_type = node.type or 'process'
        
        # Basic explanations with hyperlinks to educational resources
        comments = {
            'start': "🚀 Let's start here! This is like turning on your flowchart.\n    // Basic concept: Programs run from top to bottom, line by line.\n    // Learn more: https://www.khanacademy.org/computing/computer-programming/programming/intro-to-programming",
            'end': "🏁 Program finished! This is where we stop.\n    // Basic concept: Every program needs a clear ending point.\n    // Learn more: https://www.khanacademy.org/computing/computer-programming/programming/intro-to-programming",
            'process': "⚙️ Processing step: This does work or calculations.\n    // Basic concept: Variables are like boxes that hold information.\n    // Learn more: https://www.khanacademy.org/computing/computer-programming/programming/variables/a/intro-to-variables",
            'input': "📥 Getting information: This asks the user for data.\n    // Basic concept: Input is how we get information from users.\n    // Learn more: https://developer.mozilla.org/en-US/docs/Learn/JavaScript/First_steps/What_is_JavaScript#user_input",
            'output': "📤 Showing results: This displays information to the user.\n    // Basic concept: Output is how we show results to users.\n    // Learn more: https://developer.mozilla.org/en-US/docs/Learn/JavaScript/First_steps/What_is_JavaScript#output",
            'decision': "🤔 Making a choice: This asks a yes/no question.\n    // Basic concept: Decisions are like yes/no questions in real life.\n    // Learn more: https://www.khanacademy.org/computing/computer-programming/programming/logic-if-statements/a/intro-to-if-statements"
        }
        
        base_comment = comments.get(node_type, "📋 A general step in the process.\n    // Basic concept: Every step in a program does something specific.\n    // Learn more: https://www.khanacademy.org/computing/computer-programming/programming/intro-to-programming/a/what-is-programming")
        
        # Add the node's original text and a reference to its ID for traceability.
        comment_lines = [base_comment]
        if node.value:
            comment_lines.append(f"    // Flowchart Text: \"{node.value}\"")
        comment_lines.append(f"    // (Corresponds to Flowchart Element ID: {node.id})")
        
        return "\n    // ".join(comment_lines) 