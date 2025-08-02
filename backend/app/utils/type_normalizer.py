from typing import Optional

# Define canonical types for flowchart nodes to ensure consistency.
CANONICAL_START = "start"
CANONICAL_END = "end"
CANONICAL_PROCESS = "process"
CANONICAL_DECISION = "decision"
CANONICAL_INPUT = "input"
CANONICAL_OUTPUT = "output"
CANONICAL_SUBROUTINE = "subroutine"
CANONICAL_UNKNOWN = "process"  # Default for unrecognized shapes.

def normalize_node_type(style: Optional[str], value: Optional[str], existing_type: Optional[str]) -> str:
    """
    Normalizes a flowchart node's type based on its style, value, and existing type.

    The logic prioritizes specific keywords in the node's style string, which often
    contains shape information like 'ellipse' or 'rhombus'. It falls back to checking
    the node's text value for keywords like 'start' or 'input'. If no specific type
    can be determined, it defaults to a 'process' type.

    Args:
        style: The style string of the node (e.g., 'ellipse;whiteSpace=wrap;...').
        value: The text content of the node.
        existing_type: The type assigned by the frontend, used as a fallback.

    Returns:
        A canonical node type string (e.g., "start", "decision").
    """
    if not style:
        # If style is missing, fall back to existing type or default to unknown
        return existing_type if existing_type else CANONICAL_UNKNOWN

    style_lower = style.lower()
    value_lower = value.lower() if value else ""

    # Subroutine nodes can be identified by keywords in their text
    # Look for function definition patterns like "function name(params)" or "def name" or "void name()"
    if value_lower:
        subroutine_patterns = [
            "function", "def ", "void ", "int ", "float ", "double ", "string ",
            "subroutine", "procedure", "method", "call ", "invoke"
        ]
        # Check for function-like patterns with parentheses
        has_parentheses = "(" in value_lower and ")" in value_lower
        has_subroutine_keyword = any(pattern in value_lower for pattern in subroutine_patterns)
        
        if has_subroutine_keyword or has_parentheses:
            return CANONICAL_SUBROUTINE

    # Decision nodes are typically rhombus or diamond shapes.
    if "rhombus" in style_lower or "diamond" in style_lower:
        return CANONICAL_DECISION

    # Input/Output nodes are often represented by parallelograms.
    if "parallelogram" in style_lower:
        if "input" in value_lower or "read" in value_lower or "get" in value_lower:
            return CANONICAL_INPUT
        if "output" in value_lower or "print" in value_lower or "display" in value_lower:
            return CANONICAL_OUTPUT
        # Default to input if shape is parallelogram but text is ambiguous
        return CANONICAL_INPUT

    # Start/End nodes are typically ellipses.
    if "ellipse" in style_lower:
        if "start" in value_lower:
            return CANONICAL_START
        if "end" in value_lower or "stop" in value_lower:
            return CANONICAL_END
        # If frontend has already typed it as start/end, respect that.
        if existing_type in [CANONICAL_START, CANONICAL_END]:
            return existing_type
        # If it's an ellipse with no other info, assume it's a start node.
        return CANONICAL_START

    # Process nodes are usually rectangles.
    if "rect" in style_lower or "rounded" in style_lower or "square" in style_lower:
        return CANONICAL_PROCESS
    
    # If a known type is already provided, use it as a fallback.
    if existing_type in [CANONICAL_START, CANONICAL_END, CANONICAL_PROCESS, CANONICAL_DECISION, CANONICAL_INPUT, CANONICAL_OUTPUT, CANONICAL_SUBROUTINE]:
        return existing_type

    # Default to process for any other unrecognized shapes.
    return CANONICAL_UNKNOWN 