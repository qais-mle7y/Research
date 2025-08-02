from typing import List
from app.schemas.flowchart import AnalysisResult
import re

def clean_html_from_text(text: str) -> str:
    """
    Removes HTML tags and entities from text to make it user-friendly.
    """
    if not text:
        return text
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    clean_text = clean_text.replace('&lt;', '<')
    clean_text = clean_text.replace('&gt;', '>')
    clean_text = clean_text.replace('&amp;', '&')
    clean_text = clean_text.replace('&quot;', '"')
    clean_text = clean_text.replace('&#39;', "'")
    clean_text = clean_text.replace('&nbsp;', ' ')
    
    return clean_text.strip()

def generate_feedback_messages(analysis_results: List[AnalysisResult]) -> List[str]:
    """
    Generates user-friendly feedback messages from analysis results.
    Focuses on helpful, actionable advice rather than technical details.

    Args:
        analysis_results: A list of AnalysisResult objects from the Assessment Engine.

    Returns:
        A list of user-friendly feedback strings.
    """
    feedback_strings: List[str] = []
    
    if not analysis_results:
        feedback_strings.append("✅ Great! Your flowchart structure looks good and follows all the basic rules.")
        return feedback_strings

    # Group similar errors to provide better feedback
    error_groups = {
        'start_issues': [],
        'end_issues': [],
        'connection_issues': [],
        'other_issues': []
    }
    
    for result in analysis_results:
        if 'START' in result.rule_id:
            error_groups['start_issues'].append(result)
        elif 'END' in result.rule_id:
            error_groups['end_issues'].append(result)
        elif 'UNCONNECTED' in result.rule_id or 'OUTGOING' in result.rule_id or 'INCOMING' in result.rule_id:
            error_groups['connection_issues'].append(result)
        else:
            error_groups['other_issues'].append(result)
    
    # Generate user-friendly messages for each group
    for group_name, results in error_groups.items():
        if not results:
            continue
            
        if group_name == 'start_issues':
            feedback_strings.extend(_generate_start_feedback(results))
        elif group_name == 'end_issues':
            feedback_strings.extend(_generate_end_feedback(results))
        elif group_name == 'connection_issues':
            feedback_strings.extend(_generate_connection_feedback(results))
        else:
            feedback_strings.extend(_generate_other_feedback(results))
    
    return feedback_strings

def _generate_start_feedback(results: List[AnalysisResult]) -> List[str]:
    """Generate user-friendly feedback for start symbol issues."""
    feedback = []
    
    for result in results:
        if result.rule_id == "NO_START_SYMBOL":
            feedback.append("❌ **Missing Start Symbol**: Your flowchart needs exactly one 'Start' symbol to show where the program begins. Please add a start symbol (usually an oval or rounded rectangle).")
        elif result.rule_id == "MULTIPLE_START_SYMBOLS":
            count = result.message.split('but ')[1].split(' were')[0] if 'but ' in result.message else "multiple"
            feedback.append(f"❌ **Too Many Start Symbols**: Your flowchart has {count} start symbols, but it should have exactly one. Please remove the extra start symbols so there's only one entry point.")
        elif "START_SYMBOL_NO_OUTGOING" in result.rule_id:
            feedback.append("⚠️ **Disconnected Start**: Your start symbol isn't connected to anything. Please draw an arrow from the start symbol to the first step of your process.")
    
    return feedback

def _generate_end_feedback(results: List[AnalysisResult]) -> List[str]:
    """Generate user-friendly feedback for end symbol issues."""
    feedback = []
    
    for result in results:
        if result.rule_id == "NO_END_SYMBOL":
            feedback.append("❌ **Missing End Symbol**: Your flowchart needs at least one 'End' symbol to show where the program finishes. Please add an end symbol (usually an oval or rounded rectangle).")
        elif "END_SYMBOL_NO_INCOMING" in result.rule_id:
            feedback.append("⚠️ **Disconnected End**: Your end symbol isn't connected to anything. Please draw an arrow from your last process step to the end symbol.")
    
    return feedback

def _generate_connection_feedback(results: List[AnalysisResult]) -> List[str]:
    """Generate user-friendly feedback for connection issues."""
    feedback = []
    
    for result in results:
        # Clean HTML from node values to make them readable
        if result.message and "Symbol '" in result.message:
            # Extract the symbol text and clean it
            symbol_match = re.search(r"Symbol '([^']+)'", result.message)
            if symbol_match:
                raw_symbol = symbol_match.group(1)
                clean_symbol = clean_html_from_text(raw_symbol)
                
                if result.rule_id == "UNCONNECTED_SYMBOL_BOTH":
                    if clean_symbol and clean_symbol != raw_symbol:
                        feedback.append(f"⚠️ **Floating Element**: The element containing \"{clean_symbol}\" is not connected to your flowchart. Please connect it with arrows to show the flow of your program.")
                    else:
                        feedback.append("⚠️ **Floating Element**: There's an element that's not connected to your flowchart. Please connect it with arrows to show the flow of your program.")
                
                elif result.rule_id == "UNCONNECTED_SYMBOL_NO_INCOMING":
                    if clean_symbol and clean_symbol != raw_symbol:
                        feedback.append(f"⚠️ **Missing Input Connection**: The element \"{clean_symbol}\" has no incoming arrows. Please connect it to the previous step in your process.")
                    else:
                        feedback.append("⚠️ **Missing Input Connection**: There's an element with no incoming arrows. Please connect it to the previous step in your process.")
                
                elif result.rule_id == "UNCONNECTED_SYMBOL_NO_OUTGOING":
                    if clean_symbol and clean_symbol != raw_symbol:
                        feedback.append(f"⚠️ **Missing Output Connection**: The element \"{clean_symbol}\" has no outgoing arrows. Please connect it to the next step in your process or to an end symbol.")
                    else:
                        feedback.append("⚠️ **Missing Output Connection**: There's an element with no outgoing arrows. Please connect it to the next step in your process or to an end symbol.")
            else:
                # Fallback for unmatched patterns
                feedback.append("⚠️ **Connection Issue**: Some elements in your flowchart are not properly connected. Please check that all elements have appropriate arrows showing the flow.")
    
    return feedback

def _generate_other_feedback(results: List[AnalysisResult]) -> List[str]:
    """Generate user-friendly feedback for other types of issues."""
    feedback = []
    
    for result in results:
        severity_icon = "❌" if result.severity == "error" else "⚠️" if result.severity == "warning" else "ℹ️"
        
        # Clean the message of technical details
        clean_message = result.message
        # Remove node ID references like "(18)" or "(node_id)"
        clean_message = re.sub(r'\s*\([^)]*\)\s*', ' ', clean_message)
        # Clean up extra spaces
        clean_message = re.sub(r'\s+', ' ', clean_message).strip()
        
        feedback.append(f"{severity_icon} {clean_message}")
    
    return feedback 