import networkx as nx
from app.schemas.flowchart import FlowchartDataSchema, FlowchartNodeSchema
from app.codegen.interfaces import CodeGenerator
from app.codegen.base import EducationalCodeGeneratorBase
from typing import List, Dict, Set

class EducationalCodeGenerator:
    """
    Base class for educational code generation with common utility methods.
    Focuses on generating code that teaches programming concepts to beginners.
    """
    
    def _clean_identifier(self, text: str) -> str:
        """
        Converts flowchart text to valid programming identifiers.
        """
        if not text:
            return "unknownValue"
        
        # Remove special characters and replace with underscores
        import re
        cleaned = re.sub(r'[^a-zA-Z0-9_]', '_', text.strip())
        cleaned = re.sub(r'_{2,}', '_', cleaned)  # Replace multiple underscores with single
        cleaned = cleaned.strip('_')  # Remove leading/trailing underscores
        
        # Ensure it starts with a letter
        if not cleaned or cleaned[0].isdigit():
            cleaned = f"var_{cleaned}" if cleaned else "unknownValue"
            
        return cleaned[:30]  # Limit length
    
    def _extract_variables_from_text(self, text: str) -> List[str]:
        """
        Extracts potential variable names from flowchart text.
        """
        if not text:
            return []
        
        import re
        # Look for patterns like "x = 5", "input number", "read value", etc.
        patterns = [
            r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*=',  # assignment patterns
            r'(?:input|read|enter|get)\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # input patterns
            r'(?:print|output|display|show)\s+([a-zA-Z_][a-zA-Z0-9_]*)',  # output patterns
        ]
        
        variables = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            variables.extend(matches)
        
        return [self._clean_identifier(var) for var in variables if var]
    
    def _get_educational_comment(self, node: FlowchartNodeSchema) -> str:
        """
        Generates educational comments explaining what each flowchart element does,
        with a hyperlink back to the node ID.
        """
        comments = {
            'start': "🚀 PROGRAM START: This is where our program begins execution",
            'end': "🏁 PROGRAM END: This is where our program finishes execution",
            'process': "⚙️ PROCESS: This step performs a calculation or operation",
            'input': "📥 INPUT: This step gets data from the user",
            'output': "📤 OUTPUT: This step displays information to the user",
            'decision': "🤔 DECISION: This step makes a choice based on a condition",
            'subroutine': "🔧 SUBROUTINE: This step calls or defines a reusable function"
        }
        
        base_comment = comments.get(node.type, "📋 STEP: This is a flowchart step")
        
        # Append hyperlink to the node ID
        hyperlink = f"(Flowchart Node: {node.id})"
        
        if node.value:
            # Combine the base comment, the user's text, and the hyperlink
            return f"{base_comment}\n    // Flowchart says: \"{node.value}\"\n    // {hyperlink}"
        
        return f"{base_comment}\n    // {hyperlink}"

class CppCodeGenerator(CodeGenerator, EducationalCodeGeneratorBase):
    '''
    Generates educational C++ code from a flowchart with extensive comments and explanations.
    '''
    def generate_code(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph, idiomatic: bool = False) -> str:
        if idiomatic:
            return self._generate_educational_cpp(flowchart_data, graph)
        else:
            return self._generate_educational_cpp(flowchart_data, graph)

    def _generate_educational_cpp(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> str:
        code_lines: List[str] = []
        
        # Header with explanation
        code_lines.extend([
            "/*",
            " * 🎓 EDUCATIONAL C++ CODE GENERATED FROM FLOWCHART",
            " * ================================================",
            " * This code was automatically generated from your flowchart.",
            " * Each comment explains what the code does and how it relates",
            " * to your flowchart elements.",
            " *",
            " * 📚 LEARNING NOTES:",
            " * - #include statements bring in code libraries we need",
            " * - Variables are like boxes that hold information",
            " * - Programs run from top to bottom, line by line",
            " * - Comments (like this) explain what code does",
            " * Learn more: https://www.khanacademy.org/computing/computer-programming/programming/intro-to-programming/a/what-is-programming",
            " */",
            ""
        ])

        # Include statements with explanations
        code_lines.extend([
            "// 📚 INCLUDE LIBRARIES: These give us access to useful functions",
            "#include <iostream>  // For input/output (cin, cout)",
            "#include <string>    // For working with text",
            "#include <vector>    // For lists of data", 
            "#include <cstdlib>   // For system functions like exit()",
            ""
        ])

        # Collect variables from flowchart
        all_variables = set()
        subroutines = {}  # Dictionary to store subroutine definitions
        
        for node in flowchart_data.nodes:
            if node.value:
                vars_in_node = self._extract_variables_from_text(node.value)
                all_variables.update(vars_in_node)
            
            # Check if this is a subroutine node
            node_attrs = graph.nodes.get(node.id, {})
            if node_attrs.get('type') == 'subroutine':
                func_name = node_attrs.get('subroutine_name')
                params = node_attrs.get('subroutine_params', [])
                if func_name:
                    subroutines[func_name] = {
                        'name': func_name,
                        'params': params,
                        'node_id': node.id,
                        'node_value': node.value,
                        'color': node.color
                    }

        # Generate subroutine function declarations
        if subroutines:
            code_lines.extend([
                "// 🔧 SUBROUTINE DECLARATIONS: These are reusable functions",
                "// Basic concept: Functions let us organize code into named blocks",
                "// Learn more: https://www.khanacademy.org/computing/computer-programming/programming/functions/a/functions",
                ""
            ])
            
            for func_name, sub_info in subroutines.items():
                params_str = ', '.join([f'std::string {p}' for p in sub_info['params']]) if sub_info['params'] else ''
                code_lines.extend([
                    f"void {func_name}({params_str}) {{",
                    f"    // 📋 SUBROUTINE: {sub_info['node_value'] or func_name}",
                    f"    // This function was defined in your flowchart (Node: {sub_info['node_id']})",
                    f"    std::cout << \"🔧 Executing subroutine: {func_name}\" << std::endl;",
                    "    // TODO: Add the actual logic for this subroutine here",
                    "}",
                    ""
                ])
        
        # Main function with all logic inline
        code_lines.extend([
            "// 🚀 MAIN FUNCTION: This is where every C++ program starts",
            "int main() {",
            "    // The main function contains all the logic from your flowchart",
            "    std::cout << \"=== FLOWCHART PROGRAM STARTING ===\" << std::endl;",
            "    std::cout << \"This program follows your flowchart step by step!\" << std::endl;",
            "    std::cout << std::endl;",
            ""
        ])

        # Declare variables at the top of main
        if all_variables:
            code_lines.extend([
                "    // 📦 VARIABLES: These are like boxes that store information",
                "    // Basic concept: Variables hold data we can use later",
                "    // Learn more: https://www.khanacademy.org/computing/computer-programming/programming/variables/a/intro-to-variables"
            ])
            for var in sorted(all_variables):
                code_lines.append(f"    std::string {var};  // Will store: {var}")
            code_lines.append("")

        # Use topological sort to get linear order of nodes
        try:
            # Get topological order of nodes
            topo_order = list(nx.topological_sort(graph))
            
            # Create a mapping from node ID to node object
            node_map = {node.id: node for node in flowchart_data.nodes}
            
            # Generate linear code for each node in topological order
            for i, node_id in enumerate(topo_order):
                if node_id in node_map:
                    node = node_map[node_id]
                    self._generate_inline_cpp_logic(node, graph, code_lines, i, len(topo_order))
                    
        except Exception as e:
            # If graph has cycles or other issues, fall back to original node order
            code_lines.append(f"    // ⚠️ Note: Flowchart has cycles or structural issues, using original order")
            code_lines.append(f"    // Debug: {str(e)}")
            for i, node in enumerate(flowchart_data.nodes):
                self._generate_inline_cpp_logic(node, graph, code_lines, i, len(flowchart_data.nodes))

        code_lines.extend([
            "",
            "    // 🏁 If we get here, the program completed normally",
            "    std::cout << std::endl << \"=== PROGRAM COMPLETED ===\" << std::endl;",
            "    return 0;  // Tell the system: \"Program finished successfully\"",
            "}",
            ""
        ])

        return '\n'.join(code_lines)

    def _generate_inline_cpp_logic(self, node: FlowchartNodeSchema, graph: nx.DiGraph, 
                                  code_lines: List[str], node_index: int, total_nodes: int):
        """
        Generates inline logic for a single flowchart node within the main function.
        """
        node_color = getattr(node, 'color', '#f0f0f0')  # Default to light gray
        
        # Add a creative step header with node color
        readable_color = self._ensure_readable_color(node_color)
        bg_color = self._get_subtle_background(node_color)
        step_header_style = f"color: {readable_color}; background-color: {bg_color}; border: 2px solid {readable_color}; padding: 4px 8px; font-weight: bold; border-radius: 4px;"
        step_header = f'<span style="{step_header_style}">🔹 STEP {node_index + 1}/{total_nodes} - {node.type.upper() if node.type else "STEP"}: {node.value or "Unknown"}</span>'
        code_lines.append(step_header)
        code_lines.append("")
        
        # Add educational comment for this step (in gray)
        comment = self._get_educational_comment(node)
        comment_lines = []
        for line in comment.split('\n'):
            comment_lines.append(f"    // {line.strip()}")
        comment_lines.append("")
        
        # Wrap comment lines with consistent gray color
        colored_comments = self._wrap_with_color(comment_lines, node_color, is_comment=True)
        code_lines.extend(colored_comments)

        node_type = node.type or 'process'

        if node_type == 'start':
            node_code = [
                "    std::cout << \"🚀 Starting the program...\" << std::endl;",
                "    // Basic concept: Every program needs a starting point",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
        elif node_type == 'end':
            node_code = [
                "    std::cout << \"🏁 Program is ending...\" << std::endl;",
                f"    std::cout << \"Final message: {node.value or 'Program complete'}\" << std::endl;",
                "    // Basic concept: Programs should end cleanly",
                "    return 0;  // Exit the main function",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
        elif node_type == 'process':
            variables = self._extract_variables_from_text(node.value or "")
            node_code = [
                f"    std::cout << \"⚙️ Processing: {node.value or 'Calculation step'}\" << std::endl;",
                "    // Basic concept: This is where we do calculations or work",
            ]
            if variables:
                node_code.append(f"    // TODO: Replace this with actual processing logic for: {', '.join(variables)}")
                for var in variables:
                    node_code.append(f"    // Example: {var} = \"someValue\";  // Set {var} to a value")
            else:
                node_code.append("    // TODO: Add your processing logic here")
                node_code.append("    // This represents a calculation or operation from your flowchart")
            node_code.append("")
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
        elif node_type == 'input':
            variables = self._extract_variables_from_text(node.value or "")
            if variables:
                var_name = variables[0]
                node_code = [
                    f"    std::cout << \"📥 Input needed: {node.value}\" << std::endl;",
                    f"    std::cout << \"Please enter {var_name}: \";",
                    f"    std::getline(std::cin, {var_name});  // Read user input into {var_name}",
                    f"    std::cout << \"You entered: \" << {var_name} << std::endl;",
                    "    // Basic concept: Input lets users give data to our program",
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            else:
                node_code = [
                    f"    std::cout << \"📥 {node.value or 'Please enter data'}\" << std::endl;",
                    "    std::string userInput;  // Variable to store what user types",
                    "    std::cout << \"Enter value: \";",
                    "    std::getline(std::cin, userInput);  // Read user input",
                    "    std::cout << \"You entered: \" << userInput << std::endl;",
                    "    // Basic concept: Input lets users give data to our program",
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            code_lines.append("")
            
        elif node_type == 'output':
            variables = self._extract_variables_from_text(node.value or "")
            node_code = [
                f"    std::cout << \"📤 Output: {node.value or 'Displaying result'}\" << std::endl;",
                "    // Basic concept: Output shows results to users",
            ]
            if variables:
                for var in variables:
                    node_code.append(f"    // std::cout << {var} << std::endl;  // Display {var}")
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            code_lines.append("")
            
        elif node_type == 'decision':
            successors = list(graph.successors(node.id))
            node_code = [
                f"    std::cout << \"🤔 Decision point: {node.value or 'Making a choice'}\" << std::endl;",
                "    // Basic concept: Decisions are like yes/no questions",
                "    // TODO: Replace 'true' with your actual condition",
                f"    bool decision_result = true;  // Condition: {node.value or 'Some condition'}",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
            if len(successors) >= 2:
                node_code = [
                    "    if (decision_result) {  // If condition is TRUE",
                    "        std::cout << \"→ Condition is TRUE, taking YES path\" << std::endl;",
                    "        // Continue with YES path logic here",
                    "    } else {  // If condition is FALSE", 
                    "        std::cout << \"→ Condition is FALSE, taking NO path\" << std::endl;",
                    "        // Continue with NO path logic here",
                    "    }",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            elif len(successors) == 1:
                node_code = [
                    "    if (decision_result) {  // If condition is TRUE",
                    "        std::cout << \"→ Condition is TRUE, continuing\" << std::endl;",
                    "        // Continue with next step",
                    "    } else {",
                    "        std::cout << \"→ Condition is FALSE, program ends\" << std::endl;",
                    "        return 0;",
                    "    }",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            else:
                node_code = [
                    "    std::cout << \"⚠️ Warning: Decision has no paths to follow!\" << std::endl;",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
        elif node_type == 'subroutine':
            # Get subroutine information from graph attributes
            node_attrs = graph.nodes.get(node.id, {})
            func_name = node_attrs.get('subroutine_name')
            params = node_attrs.get('subroutine_params', [])
            
            if func_name:
                node_code = [
                    f"    std::cout << \"🔧 Calling subroutine: {func_name}\" << std::endl;",
                    "    // Basic concept: Subroutines are reusable blocks of code",
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
                
                if params:
                    node_code = [
                        f"    // TODO: Pass actual arguments for parameters: {', '.join(params)}",
                        f"    // {func_name}()  // Call with appropriate arguments"
                    ]
                    colored_code = self._wrap_with_color(node_code, node_color)
                    code_lines.extend(colored_code)
                else:
                    node_code = [
                        f"    // {func_name}()  // Call the subroutine"
                    ]
                    colored_code = self._wrap_with_color(node_code, node_color)
                    code_lines.extend(colored_code)
                code_lines.append("")
            else:
                node_code = [
                    f"    std::cout << \"🔧 Subroutine call: {node.value or 'Unknown subroutine'}\" << std::endl;",
                    "    // TODO: Replace with actual subroutine call",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
        else:
            node_code = [
                f"    std::cout << \"📋 Generic step: {node.value or 'Unknown step'}\" << std::endl;",
                "    // This is a general flowchart element",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)

    def _generate_direct_cpp(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> str:
        # Keep the old version for backward compatibility, but redirect to educational
        return self._generate_educational_cpp(flowchart_data, graph)

class JavaCodeGenerator(CodeGenerator, EducationalCodeGeneratorBase):
    '''
    Generates educational Java code from a flowchart with extensive comments and explanations.
    '''
    def generate_code(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph, idiomatic: bool = False) -> str:
        if idiomatic:
            return self._generate_educational_java(flowchart_data, graph)
        else:
            return self._generate_educational_java(flowchart_data, graph)

    def _generate_educational_java(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> str:
        code_lines: List[str] = []
        class_name = "FlowchartProgram"
        
        # Header with explanation
        code_lines.extend([
            "/*",
            " * 🎓 EDUCATIONAL JAVA CODE GENERATED FROM FLOWCHART",
            " * ================================================",
            " * This code was automatically generated from your flowchart.",
            " * Each comment explains what the code does and how it relates",
            " * to your flowchart elements.",
            " *",
            " * 📚 LEARNING NOTES:",
            " * - import statements bring in Java libraries we need",
            " * - Variables are like boxes that hold information",
            " * - Programs run from top to bottom, line by line",
            " * - Comments (like this) explain what code does",
            " * - System.out.println() displays text to the user",
            " * Learn more: https://www.khanacademy.org/computing/computer-programming/programming/intro-to-programming/a/what-is-programming",
            " */",
            ""
        ])

        # Import statements with explanations
        code_lines.extend([
            "// 📚 IMPORT LIBRARIES: These give us access to useful Java classes",
            "import java.util.Scanner;  // For reading user input",
            ""
        ])

        # Collect variables from flowchart
        all_variables = set()
        subroutines = {}  # Dictionary to store subroutine definitions
        
        for node in flowchart_data.nodes:
            if node.value:
                vars_in_node = self._extract_variables_from_text(node.value)
                all_variables.update(vars_in_node)
            
            # Check if this is a subroutine node
            node_attrs = graph.nodes.get(node.id, {})
            if node_attrs.get('type') == 'subroutine':
                func_name = node_attrs.get('subroutine_name')
                params = node_attrs.get('subroutine_params', [])
                if func_name:
                    subroutines[func_name] = {
                        'name': func_name,
                        'params': params,
                        'node_id': node.id,
                        'node_value': node.value,
                        'color': node.color
                    }

        # Class declaration with explanations
        code_lines.extend([
            f"// 🏛️ CLASS DEFINITION: In Java, everything goes inside a class",
            f"public class {class_name} {{",
            "    // 📊 SCANNER: This helps us read input from the user",
            "    private static Scanner scanner = new Scanner(System.in);",
            ""
        ])

        # Generate subroutine methods
        if subroutines:
            code_lines.extend([
                "    // 🔧 SUBROUTINE METHODS: These are reusable pieces of code",
                "    // Basic concept: Methods let us organize code into named blocks",
                "    // Learn more: https://www.khanacademy.org/computing/computer-programming/programming/functions/a/functions",
                ""
            ])
            
            for func_name, sub_info in subroutines.items():
                params_str = ', '.join([f'String {p}' for p in sub_info['params']]) if sub_info['params'] else ''
                code_lines.extend([
                    f"    public static void {func_name}({params_str}) {{",
                    f"        // 📋 SUBROUTINE: {sub_info['node_value'] or func_name}",
                    f"        // This method was defined in your flowchart (Node: {sub_info['node_id']})",
                    f"        System.out.println(\"🔧 Executing subroutine: {func_name}\");",
                    "        // TODO: Add the actual logic for this subroutine here",
                    "    }",
                    ""
                ])

        # Main method with all logic inline
        code_lines.extend([
            "    // 🚀 MAIN METHOD: This is where every Java program starts",
            "    public static void main(String[] args) {",
            "        // The main method contains all the logic from your flowchart",
            "        System.out.println(\"=== FLOWCHART PROGRAM STARTING ===\");",
            "        System.out.println(\"This program follows your flowchart step by step!\");",
            "        System.out.println();",
            ""
        ])

        # Declare variables at the top of main
        if all_variables:
            code_lines.extend([
                "        // 📦 VARIABLES: These are like boxes that store information",
                "        // Basic concept: Variables hold data we can use later",
                "        // Learn more: https://www.khanacademy.org/computing/computer-programming/programming/variables/a/intro-to-variables"
            ])
            for var in sorted(all_variables):
                code_lines.append(f"        String {var} = null;  // Will store: {var}")
            code_lines.append("")

        # Use topological sort to get linear order of nodes
        try:
            # Get topological order of nodes
            topo_order = list(nx.topological_sort(graph))
            
            # Create a mapping from node ID to node object
            node_map = {node.id: node for node in flowchart_data.nodes}
            
            # Generate linear code for each node in topological order
            for i, node_id in enumerate(topo_order):
                if node_id in node_map:
                    node = node_map[node_id]
                    self._generate_inline_java_logic(node, graph, code_lines, i, len(topo_order))
                    
        except Exception as e:
            # If graph has cycles or other issues, fall back to original node order
            code_lines.append(f"        // ⚠️ Note: Flowchart has cycles or structural issues, using original order")
            code_lines.append(f"        // Debug: {str(e)}")
            for i, node in enumerate(flowchart_data.nodes):
                self._generate_inline_java_logic(node, graph, code_lines, i, len(flowchart_data.nodes))

        code_lines.extend([
            "",
            "        // 🏁 If we get here, the program completed normally",
            "        System.out.println();",
            "        System.out.println(\"=== PROGRAM COMPLETED ===\");",
            "        scanner.close();  // Clean up the scanner",
            "    }",
            "}",  # Close the class
            ""
        ])

        return '\n'.join(code_lines)

    def _generate_inline_java_logic(self, node: FlowchartNodeSchema, graph: nx.DiGraph, 
                                   code_lines: List[str], node_index: int, total_nodes: int):
        """
        Generates inline logic for a single flowchart node within the main method.
        """
        node_color = getattr(node, 'color', '#f0f0f0')  # Default to light gray
        
        # Add a creative step header with node color
        readable_color = self._ensure_readable_color(node_color)
        bg_color = self._get_subtle_background(node_color)
        step_header_style = f"color: {readable_color}; background-color: {bg_color}; border: 2px solid {readable_color}; padding: 4px 8px; font-weight: bold; border-radius: 4px;"
        step_header = f'<span style="{step_header_style}">🔹 STEP {node_index + 1}/{total_nodes} - {node.type.upper() if node.type else "STEP"}: {node.value or "Unknown"}</span>'
        code_lines.append(step_header)
        code_lines.append("")
        
        # Add educational comment for this step (in gray)
        comment = self._get_educational_comment(node)
        comment_lines = []
        for line in comment.split('\n'):
            comment_lines.append(f"        // {line.strip()}")
        comment_lines.append("")
        
        # Wrap comment lines with consistent gray color
        colored_comments = self._wrap_with_color(comment_lines, node_color, is_comment=True)
        code_lines.extend(colored_comments)

        node_type = node.type or 'process'

        if node_type == 'start':
            node_code = [
                "        System.out.println(\"🚀 Starting the program...\");",
                "        // Basic concept: Every program needs a starting point",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
        elif node_type == 'end':
            node_code = [
                "        System.out.println(\"🏁 Program is ending...\");",
                f"        System.out.println(\"Final message: {node.value or 'Program complete'}\");",
                "        // Basic concept: Programs should end cleanly",
                "        return;  // Exit the main method",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
        elif node_type == 'process':
            variables = self._extract_variables_from_text(node.value or "")
            node_code = [
                f"        System.out.println(\"⚙️ Processing: {node.value or 'Calculation step'}\");",
                "        // Basic concept: This is where we do calculations or work",
            ]
            
            if variables:
                node_code.append(f"        // TODO: Replace this with actual processing logic for: {', '.join(variables)}")
                for var in variables:
                    node_code.append(f"        // Example: {var} = \"someValue\";  // Set {var} to a value")
            else:
                node_code.append("        // TODO: Add your processing logic here")
                node_code.append("        // This represents a calculation or operation from your flowchart")
            node_code.append("")
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
        elif node_type == 'input':
            variables = self._extract_variables_from_text(node.value or "")
            if variables:
                var_name = variables[0]
                node_code = [
                    f"        System.out.println(\"📥 Input needed: {node.value}\");",
                    f"        System.out.print(\"Please enter {var_name}: \");",
                    f"        {var_name} = scanner.nextLine();  // Read user input into {var_name}",
                    f"        System.out.println(\"You entered: \" + {var_name});",
                    "        // Basic concept: Input lets users give data to our program",
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            else:
                node_code = [
                    f"        System.out.println(\"📥 {node.value or 'Please enter data'}\");",
                    "        String userInput;  // Variable to store what user types",
                    "        System.out.print(\"Enter value: \");",
                    "        userInput = scanner.nextLine();  // Read user input",
                    "        System.out.println(\"You entered: \" + userInput);",
                    "        // Basic concept: Input lets users give data to our program",
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            code_lines.append("")
            
        elif node_type == 'output':
            variables = self._extract_variables_from_text(node.value or "")
            node_code = [
                f"        System.out.println(\"📤 Output: {node.value or 'Displaying result'}\");",
                "        // Basic concept: Output shows results to users",
            ]
            if variables:
                for var in variables:
                    node_code.append(f"        // System.out.println({var});  // Display {var}")
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            code_lines.append("")
            
        elif node_type == 'decision':
            successors = list(graph.successors(node.id))
            node_code = [
                f"        System.out.println(\"🤔 Decision point: {node.value or 'Making a choice'}\");",
                "        // Basic concept: Decisions are like yes/no questions",
                "        // TODO: Replace 'true' with your actual condition",
                f"        boolean decision_result = true;  // Condition: {node.value or 'Some condition'}",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
            if len(successors) >= 2:
                node_code = [
                    "        if (decision_result) {  // If condition is TRUE",
                    "            System.out.println(\"→ Condition is TRUE, taking YES path\");",
                    "            // Continue with YES path logic here",
                    "        } else {  // If condition is FALSE", 
                    "            System.out.println(\"→ Condition is FALSE, taking NO path\");",
                    "            // Continue with NO path logic here",
                    "        }",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            elif len(successors) == 1:
                node_code = [
                    "        if (decision_result) {  // If condition is TRUE",
                    "            System.out.println(\"→ Condition is TRUE, continuing\");",
                    "            // Continue with next step",
                    "        } else {",
                    "            System.out.println(\"→ Condition is FALSE, program ends\");",
                    "            return;",
                    "        }",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            else:
                node_code = [
                    "        System.out.println(\"⚠️ Warning: Decision has no paths to follow!\");",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
        elif node_type == 'subroutine':
            # Get subroutine information from graph attributes
            node_attrs = graph.nodes.get(node.id, {})
            func_name = node_attrs.get('subroutine_name')
            params = node_attrs.get('subroutine_params', [])
            
            if func_name:
                node_code = [
                    f"        System.out.println(\"🔧 Calling subroutine: {func_name}\");",
                    "        // Basic concept: Subroutines are reusable blocks of code",
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
                
                if params:
                    node_code = [
                        f"        // TODO: Pass actual arguments for parameters: {', '.join(params)}",
                        f"        // {func_name}()  // Call with appropriate arguments"
                    ]
                    colored_code = self._wrap_with_color(node_code, node_color)
                    code_lines.extend(colored_code)
                else:
                    node_code = [
                        f"        // {func_name}()  // Call the subroutine"
                    ]
                    colored_code = self._wrap_with_color(node_code, node_color)
                    code_lines.extend(colored_code)
                code_lines.append("")
            else:
                node_code = [
                    f"        System.out.println(\"🔧 Subroutine call: {node.value or 'Unknown subroutine'}\");",
                    "        // TODO: Replace with actual subroutine call",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
        else:
            node_code = [
                f"        System.out.println(\"📋 Generic step: {node.value or 'Unknown step'}\");",
                "        // This is a general flowchart element",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)

    def _generate_direct_java(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> str:
        # Keep the old version for backward compatibility, but redirect to educational
        return self._generate_educational_java(flowchart_data, graph)

class PythonCodeGenerator(CodeGenerator, EducationalCodeGeneratorBase):
    """
    Generates educational Python code from a flowchart, focusing on clarity
    and direct correlation to the flowchart structure.
    """
    def generate_code(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph, idiomatic: bool = False) -> str:
        if idiomatic:
            return self._generate_educational_python(flowchart_data, graph) # Placeholder
        else:
            return self._generate_educational_python(flowchart_data, graph)

    def _generate_educational_python(self, flowchart_data: FlowchartDataSchema, graph: nx.DiGraph) -> str:
        code_lines = [
            "# 🎓 EDUCATIONAL PYTHON CODE GENERATED FROM FLOWCHART",
            "# ==================================================",
            "# This code was generated from your flowchart. Comments explain each part.",
            "#",
            "# 📚 LEARNING NOTES:",
            "# - Variables are like boxes that hold information",
            "# - 'print()' displays text to the user",
            "# - 'input()' gets information from the user",
            "# - '#' creates a comment (notes for humans)",
            "# - Programs run from top to bottom, line by line",
            "# Learn more: https://www.khanacademy.org/computing/computer-programming/programming/intro-to-programming/a/what-is-programming",
            ""
        ]

        # Collect all variables from flowchart
        all_variables = set()
        subroutines = {}  # Dictionary to store subroutine definitions
        
        for node in flowchart_data.nodes:
            if node.value:
                all_variables.update(self._extract_variables_from_text(node.value))
            
            # Check if this is a subroutine node
            node_attrs = graph.nodes.get(node.id, {})
            if node_attrs.get('type') == 'subroutine':
                func_name = node_attrs.get('subroutine_name')
                params = node_attrs.get('subroutine_params', [])
                if func_name:
                    subroutines[func_name] = {
                        'name': func_name,
                        'params': params,
                        'node_id': node.id,
                        'node_value': node.value,
                        'color': node.color
                    }

        # Generate subroutine definitions first
        if subroutines:
            code_lines.extend([
                "# 🔧 SUBROUTINES: These are reusable pieces of code",
                "# Basic concept: Functions let us organize code into named blocks",
                "# Learn more: https://www.khanacademy.org/computing/computer-programming/programming/functions/a/functions",
                ""
            ])
            
            for func_name, sub_info in subroutines.items():
                params_str = ', '.join(sub_info['params']) if sub_info['params'] else ''
                sub_color = sub_info.get('color', '#f0f0f0')
                
                sub_code = [
                    f"def {func_name}({params_str}):",
                    f"    \"\"\"📋 SUBROUTINE: {sub_info['node_value'] or func_name}\"\"\"",
                    f"    # This function was defined in your flowchart (Node: {sub_info['node_id']})",
                    "    print(f'🔧 Executing subroutine: {func_name}')",
                    "    # TODO: Add the actual logic for this subroutine here",
                    "    pass  # Placeholder - replace with actual implementation",
                    ""
                ]
                colored_sub_code = self._wrap_with_color(sub_code, sub_color)
                code_lines.extend(colored_sub_code)

        # Generate main function with all logic inline
        code_lines.extend([
            "def main():",
            "    \"\"\"🚀 MAIN FUNCTION: Program execution starts here.\"\"\"",
            "    print('=== FLOWCHART PROGRAM STARTING ===')",
            "    print('This program follows your flowchart step by step!')",
            "    print()",
            ""
        ])

        # Declare variables at the top of main
        if all_variables:
            code_lines.append("    # 📦 VARIABLES: These are like boxes that store information")
            code_lines.append("    # Basic concept: Variables hold data we can use later")
            code_lines.append("    # Learn more: https://www.khanacademy.org/computing/computer-programming/programming/variables/a/intro-to-variables")
            for var in sorted(list(all_variables)):
                code_lines.append(f"    {var} = None  # Will store: {var}")
            code_lines.append("")

        # Use topological sort to get linear order of nodes
        try:
            # Get topological order of nodes
            topo_order = list(nx.topological_sort(graph))
            
            # Create a mapping from node ID to node object
            node_map = {node.id: node for node in flowchart_data.nodes}
            
            # Generate linear code for each node in topological order
            for i, node_id in enumerate(topo_order):
                if node_id in node_map:
                    node = node_map[node_id]
                    self._generate_inline_node_logic(node, graph, code_lines, i, len(topo_order))
                    
        except Exception as e:
            # If graph has cycles or other issues, fall back to original node order
            code_lines.append(f"    # ⚠️ Note: Flowchart has cycles or structural issues, using original order")
            code_lines.append(f"    # Debug: {str(e)}")
            for i, node in enumerate(flowchart_data.nodes):
                self._generate_inline_node_logic(node, graph, code_lines, i, len(flowchart_data.nodes))

        code_lines.extend([
            "",
            "    print()",
            "    print('=== PROGRAM COMPLETED ===')",
            "",
            "",
            "# 🎯 PROGRAM ENTRY POINT",
            "# Basic concept: This line makes the program start when you run it",
            "# Learn more: https://realpython.com/python-main-function/",
            "if __name__ == '__main__':",
            "    main()",
            ""
        ])
        
        return '\n'.join(code_lines)

    def _generate_inline_node_logic(self, node: FlowchartNodeSchema, graph: nx.DiGraph, 
                                   code_lines: List[str], node_index: int, total_nodes: int):
        """
        Generates inline logic for a single flowchart node within the main function.
        """
        node_color = getattr(node, 'color', '#f0f0f0')  # Default to light gray
        
        # Add a creative step header with node color
        readable_color = self._ensure_readable_color(node_color)
        bg_color = self._get_subtle_background(node_color)
        step_header_style = f"color: {readable_color}; background-color: {bg_color}; border: 2px solid {readable_color}; padding: 4px 8px; font-weight: bold; border-radius: 4px;"
        step_header = f'<span style="{step_header_style}">🔹 STEP {node_index + 1}/{total_nodes} - {node.type.upper() if node.type else "STEP"}: {node.value or "Unknown"}</span>'
        code_lines.append(step_header)
        code_lines.append("")
        
        # Add educational comment for this step (in gray)
        comment = self._get_educational_comment(node)
        comment_lines = []
        for line in comment.split('\n'):
            comment_lines.append(f"    # {line.strip()}")
        comment_lines.append("")
        
        # Wrap comment lines with consistent gray color
        colored_comments = self._wrap_with_color(comment_lines, node_color, is_comment=True)
        code_lines.extend(colored_comments)

        node_type = node.type or 'process'

        if node_type == 'start':
            node_code = [
                "    print('🚀 Starting the program...')",
                "    # Basic concept: Every program needs a starting point",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
        elif node_type == 'end':
            node_code = [
                "    print('🏁 Program is ending...')",
                f"    print('Final message: {node.value or 'Program complete'}')",
                "    # Basic concept: Programs should end cleanly",
                "    return  # Exit the main function",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
        elif node_type == 'process':
            variables = self._extract_variables_from_text(node.value or "")
            node_code = [
                f"    print('⚙️ Processing: {node.value or 'Calculation step'}')",
                "    # Basic concept: This is where we do calculations or work",
            ]
            if variables:
                node_code.append(f"    # TODO: Replace this with actual processing logic for: {', '.join(variables)}")
                for var in variables:
                    node_code.append(f"    # Example: {var} = some_calculation()  # Set {var} to a calculated value")
            else:
                node_code.append("    # TODO: Add your processing logic here")
                node_code.append("    # This represents a calculation or operation from your flowchart")
            node_code.append("")
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
        elif node_type == 'input':
            variables = self._extract_variables_from_text(node.value or "")
            if variables:
                var_name = variables[0]
                node_code = [
                    f"    print('📥 Input needed: {node.value}')",
                    f"    {var_name} = input('Please enter {var_name}: ')",
                    f"    print(f'You entered: {{{var_name}}}')",
                    "    # Basic concept: Input lets users give data to our program",
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            else:
                node_code = [
                    f"    print('📥 {node.value or 'Please enter data'}')",
                    "    user_input = input('Enter value: ')",
                    "    print(f'You entered: {user_input}')",
                    "    # Basic concept: Input lets users give data to our program",
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            code_lines.append("")
            
        elif node_type == 'output':
            variables = self._extract_variables_from_text(node.value or "")
            node_code = [
                f"    print('📤 Output: {node.value or 'Displaying result'}')",
                "    # Basic concept: Output shows results to users",
            ]
            if variables:
                for var in variables:
                    node_code.append(f"    # print(f'Result: {{{var}}}')  # Display {var}")
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            code_lines.append("")
            
        elif node_type == 'decision':
            successors = list(graph.successors(node.id))
            node_code = [
                f"    print('🤔 Decision point: {node.value or 'Making a choice'}')",
                "    # Basic concept: Decisions are like yes/no questions",
                "    # TODO: Replace 'True' with your actual condition",
                f"    decision_result = True  # Condition: {node.value or 'Some condition'}",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code)
            
            if len(successors) >= 2:
                node_code = [
                    "    if decision_result:",
                    "        print('→ Condition is TRUE, taking YES path')",
                    "        # Continue with YES path logic here",
                    "    else:",
                    "        print('→ Condition is FALSE, taking NO path')",
                    "        # Continue with NO path logic here",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            elif len(successors) == 1:
                node_code = [
                    "    if decision_result:",
                    "        print('→ Condition is TRUE, continuing')",
                    "        # Continue with next step",
                    "    else:",
                    "        print('→ Condition is FALSE, program ends')",
                    "        return",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
            else:
                node_code = [
                    "    print('⚠️ Warning: Decision has no paths to follow!')",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
        elif node_type == 'subroutine':
            # Get subroutine information from graph attributes
            node_attrs = graph.nodes.get(node.id, {})
            func_name = node_attrs.get('subroutine_name')
            params = node_attrs.get('subroutine_params', [])
            
            if func_name:
                node_code = [
                    f"    print('🔧 Calling subroutine: {func_name}')",
                    "    # Basic concept: Subroutines are reusable blocks of code",
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
                
                if params:
                    node_code = [
                        f"    # TODO: Pass actual arguments for parameters: {', '.join(params)}",
                        f"    # {func_name}()  # Call with appropriate arguments"
                    ]
                    colored_code = self._wrap_with_color(node_code, node_color)
                    code_lines.extend(colored_code)
                else:
                    node_code = [
                        f"    # {func_name}()  # Call the subroutine"
                    ]
                    colored_code = self._wrap_with_color(node_code, node_color)
                    code_lines.extend(colored_code)
                code_lines.append("")
            else:
                node_code = [
                    f"    print('🔧 Subroutine call: {node.value or 'Unknown subroutine'}')",
                    "    # TODO: Replace with actual subroutine call",
                    ""
                ]
                colored_code = self._wrap_with_color(node_code, node_color)
                code_lines.extend(colored_code)
        else:
            node_code = [
                f"    print('📋 Generic step: {node.value or 'Unknown step'}')",
                "    # This is a general flowchart element",
                ""
            ]
            colored_code = self._wrap_with_color(node_code, node_color)
            code_lines.extend(colored_code) 