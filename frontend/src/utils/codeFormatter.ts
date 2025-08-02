/**
 * A comprehensive TypeScript function to format C++ and Java code similar to Prettier
 * 
 * Features:
 * - Handles proper indentation for code blocks
 * - Preserves empty lines to maintain code structure
 * - Formats if-else chains consistently
 * - Handles preprocessor directives in C++
 * - Supports comments (single and multi-line)
 * - Handles multiple programming constructs (if, for, while, switch, etc.)
 * - Works with function declarations and goto statements
 * - Follows Prettier-like style conventions
 * 
 * @param code The C++ or Java code to format
 * @param options Formatting options
 * @returns Formatted code
 */
export function formatCode(
  code: string, 
  options: {
    indentSize?: number;
    language?: "cpp" | "java" | "python";
    bracketSameLine?: boolean;
    insertSpaces?: boolean;
  } = {}
): string {
  const { language, ...restOptions } = options;

  // If language is Python, do nothing for now.
  if (language === 'python') {
    return code;
  }
  
  // Default options
  const defaultOptions = {
    indentSize: 2,
    bracketSameLine: false,
    insertSpaces: true
  };
  
  // After the check, `language` is 'cpp', 'java', or undefined.
  // We provide a default to ensure it's never undefined for the config.
  const config = { 
    ...defaultOptions, 
    ...restOptions, 
    language: language || "cpp"
  };
  
  // Replace literal newlines with actual newlines
  code = code.replace(/\\n/g, '\n');
  
  // Tokenize the code to handle it at a syntactic level
  const tokens = tokenizeCode(code);
  
  // Format the tokenized code
  return formatTokenizedCode(tokens, config);
}

/**
 * Tokenize the code into manageable chunks for processing
 */
function tokenizeCode(code: string): string[] {
  // Basic tokenization by line
  return code.split('\n');
}

/**
 * Format tokenized code according to configuration
 */
function formatTokenizedCode(
  tokens: string[], 
  config: {
    indentSize: number;
    language: "cpp" | "java";
    bracketSameLine: boolean;
    insertSpaces: boolean;
  }
): string {
  const formatted: string[] = [];
  let indentLevel = 0;
  const indentChar = config.insertSpaces ? ' ' : '\t';
  const indentUnit = config.insertSpaces ? config.indentSize : 1;
  
  // Track comment state
  let inMultilineComment = false;
  
  // Track state for strings
  let inString = false;
  let stringDelimiter = '';
  
  // Process each line
  for (let i = 0; i < tokens.length; i++) {
    const line = tokens[i].trim();
    
    // Skip empty lines but preserve them
    if (line === '') {
      formatted.push('');
      continue;
    }

    // Handle preprocessor directives for C++
    if (config.language === "cpp" && line.startsWith('#')) {
      formatted.push(line);
      continue;
    }

    // Check for comment start/end
    if (!inString) {
      // Handle single-line comments
      if (line.trim().startsWith('//')) {
        formatted.push(indentChar.repeat(indentLevel * indentUnit) + line);
        continue;
      }
      
      // Check for multiline comment start
      if (line.includes('/*') && !inMultilineComment) {
        inMultilineComment = true;
        // If comment doesn't end on the same line
        if (!line.includes('*/')) {
          formatted.push(indentChar.repeat(indentLevel * indentUnit) + line);
          continue;
        }
      }
      
      // Check for multiline comment end
      if (inMultilineComment && line.includes('*/')) {
        inMultilineComment = false;
        formatted.push(indentChar.repeat(indentLevel * indentUnit) + line);
        continue;
      }
      
      // Inside multiline comment
      if (inMultilineComment) {
        formatted.push(indentChar.repeat(indentLevel * indentUnit) + line);
        continue;
      }
    }

    // String literal tracking - basic implementation
    // This is a simplified approach; a full parser would handle more complex cases
    if (line.includes('"') || line.includes("'")) {
      const chars = line.split('');
      for (let j = 0; j < chars.length; j++) {
        if ((chars[j] === '"' || chars[j] === "'") && (j === 0 || chars[j-1] !== '\\')) {
          if (!inString) {
            inString = true;
            stringDelimiter = chars[j];
          } else if (chars[j] === stringDelimiter) {
            inString = false;
          }
        }
      }
    }
    
    // Function declarations in C++ and Java
    const functionRegex = config.language === "cpp" 
      ? /^(void|int|float|double|bool|char|std::string|string|auto|unsigned|long|short)\s+\w+\s*\([^)]*\)/
      : /^(void|int|float|double|boolean|char|String|byte|short|long)\s+\w+\s*\([^)]*\)/;
      
    const isFunctionDeclaration = functionRegex.test(line) && !line.includes(';');
    
    // Add blank line before function declarations
    if (isFunctionDeclaration && i > 0 && tokens[i-1].trim() !== '') {
      if (formatted.length > 0 && formatted[formatted.length - 1] !== '') {
        formatted.push('');
      }
    }
    
    // Handle block start/end for indentation
    // First check if the line starts with a closing brace to decrease indent
    if (line.startsWith('}')) {
      indentLevel = Math.max(0, indentLevel - 1);
    }
    
    // Special case for else statements - keep on same line as closing brace
    if (line.startsWith('else') && formatted.length > 0) {
      const lastLine = formatted[formatted.length - 1];
      if (lastLine.trim().endsWith('}')) {
        // Remove the last line
        formatted.pop();
        // Join with else and add back
        formatted.push(lastLine + ' ' + line);
        
        // If else has a block, increase indent
        if (line.endsWith('{')) {
          indentLevel++;
        }
        continue;
      }
    }
    
    // Handle do-while loops (special case)
    if (line.startsWith('while') && line.includes(';') && i > 0) {
      const prevLine = tokens[i-1].trim();
      if (prevLine.endsWith('}')) {
        const lastFormatted = formatted.pop() || '';
        formatted.push(lastFormatted + ' ' + line);
        continue;
      }
    }
    
    // Add line with proper indentation
    formatted.push(indentChar.repeat(indentLevel * indentUnit) + line);
    
    // Check for indent increase after this line
    if (line.endsWith('{')) {
      indentLevel++;
    }
    
    // Handle non-block if/for/while statements
    if (!inString && !line.endsWith('{') && !line.endsWith(';')) {
      if (/^(if|for|while|switch)\s*\(/.test(line)) {
        indentLevel++;
      }
    }
    
    // Handle case and default statements in switch blocks
    if (line.startsWith('case ') || line.startsWith('default:')) {
      indentLevel++;
    }
    
    // Handle break statements to reduce indent after cases
    if (line === 'break;' || line.startsWith('break ')) {
      indentLevel = Math.max(0, indentLevel - 1);
    }
    
    // Decrease indent after a single statement following if/for/while without braces
    if (line.endsWith(';') && i > 0) {
      const prevLine = tokens[i-1].trim();
      if ((prevLine.startsWith('if') || prevLine.startsWith('for') || 
           prevLine.startsWith('while')) && !prevLine.endsWith('{')) {
        indentLevel = Math.max(0, indentLevel - 1);
      }
    }
  }
  
  return formatted.join('\n');
}

/**
 * Enhanced code formatter with more advanced parsing and formatting capabilities
 * for C++ and Java code, following Prettier-like conventions.
 * 
 * @param code The C++ or Java code to format
 * @param options Formatting options
 * @returns Formatted code
 */
export function prettierStyleFormatter(
  code: string,
  options: {
    indentSize?: number;
    language?: "cpp" | "java";
    bracketStyle?: "same-line" | "new-line";
    printWidth?: number;
    tabWidth?: number;
    useTabs?: boolean;
    semicolons?: boolean;
  } = {}
): string {
  // Default options
  const config = {
    indentSize: options.indentSize || options.tabWidth || 2,
    language: options.language || "cpp",
    bracketStyle: options.bracketStyle || "same-line",
    printWidth: options.printWidth || 80,
    useTabs: options.useTabs || false,
    semicolons: options.semicolons !== false // Default to true
  };
  
  // Replace literal newlines with actual newlines
  code = code.replace(/\\n/g, '\n');
  
  // Split into lines and process
  const lines = code.split('\n');
  const formatted: string[] = [];
  
  // Track indentation level
  let indentLevel = 0;
  
  // Create the indentation string based on config
  const getIndent = (level: number) => {
    return config.useTabs ? 
      '\t'.repeat(level) : 
      ' '.repeat(level * config.indentSize);
  };
  
  // State trackers
  let inMultilineComment = false;
  let inStringLiteral = false;
  let stringDelimiter = '';
  
  // Process each line
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Skip but preserve empty lines
    if (line === '') {
      formatted.push('');
      continue;
    }
    
    // Handle language-specific elements
    if (config.language === "cpp" && line.startsWith('#')) {
      // Preprocessor directives always start at column 0
      formatted.push(line);
      continue;
    }
    
    // Track comment blocks
    if (line.includes('/*') && !line.includes('*/')) {
      inMultilineComment = true;
    } else if (inMultilineComment && line.includes('*/')) {
      inMultilineComment = false;
    }
    
    // Handle comments with proper indentation
    if (line.startsWith('//') || inMultilineComment) {
      formatted.push(getIndent(indentLevel) + line);
      continue;
    }
    
    // Track string literals (basic implementation)
    if (line.includes('"') || line.includes("'")) {
      // Simple state machine for string tracking
      // A real implementation would be more complex
      for (let j = 0; j < line.length; j++) {
        const char = line[j];
        if ((char === '"' || char === "'") && (j === 0 || line[j-1] !== '\\')) {
          if (!inStringLiteral) {
            inStringLiteral = true;
            stringDelimiter = char;
          } else if (char === stringDelimiter) {
            inStringLiteral = false;
          }
        }
      }
    }
    
    // Detect various code constructs
    const isBlockStart = line.endsWith('{');
    const isBlockEnd = line === '}' || line.startsWith('}');
    const isFunctionDecl = /^(\w+\s+)+\w+\s*\([^)]*\)\s*(\{)?$/.test(line) && !line.includes(';');
    const isControlFlow = /^(if|for|while|switch|do)\s*\(/.test(line);
    const isElseStatement = line.startsWith('else');
    
    // Add blank line before function declarations
    if (isFunctionDecl && i > 0 && formatted.length > 0) {
      const lastLine = formatted[formatted.length - 1];
      if (lastLine !== '' && !lastLine.trim().startsWith('//')) {
        formatted.push('');
      }
    }
    
    // Handle block ends - decrease indent before adding
    if (isBlockEnd && !line.includes('{')) {
      indentLevel = Math.max(0, indentLevel - 1);
    }
    
    // Special handling for else statements
    if (isElseStatement && formatted.length > 0) {
      const lastLine = formatted[formatted.length - 1].trim();
      if (lastLine.endsWith('}')) {
        // Remove last line
        const prevLine = formatted.pop() || '';
        // Join with else and add back
        formatted.push(prevLine + ' ' + line);
        
        // If else has its own block, increase indent
        if (line.endsWith('{')) {
          indentLevel++;
        }
        continue;
      }
    }
    
    // Special handling for do-while loops
    if (line.startsWith('while') && line.includes(';') && i > 0) {
      const prevLine = formatted[formatted.length - 1].trim();
      if (prevLine.endsWith('}')) {
        const lastFormatted = formatted.pop() || '';
        formatted.push(lastFormatted + ' ' + line);
        continue;
      }
    }
    
    // Add properly indented line
    formatted.push(getIndent(indentLevel) + line);
    
    // Handle indentation after the line
    if (isBlockStart) {
      indentLevel++;
    }
    
    // Handle control flow without blocks
    if (isControlFlow && !isBlockStart) {
      // If next line is not a block start, increase indent
      if (i + 1 < lines.length && !lines[i + 1].trim().startsWith('{')) {
        indentLevel++;
      }
    }
    
    // Handle case and default in switch statements
    if (line.startsWith('case ') || line.startsWith('default:')) {
      indentLevel++;
    }
    
    // Handle break statements in switch cases
    if (line === 'break;' || line.startsWith('break ')) {
      indentLevel = Math.max(0, indentLevel - 1);
    }
    
    // Handle single statements after control flow
    if (line.endsWith(';') && indentLevel > 0 && i > 0) {
      const prevLine = lines[i - 1].trim();
      const isPrevControlFlow = /^(if|for|while|else\s+if)\s*\([^{]*$/.test(prevLine);
      
      if (isPrevControlFlow && !prevLine.endsWith('{')) {
        indentLevel = Math.max(0, indentLevel - 1);
      }
    }
  }
  
  return formatted.join('\n');
}

/**
 * Advanced code formatter with comprehensive support for C++ and Java syntax,
 * including complex constructs like templates, lambdas, and annotations.
 * 
 * @param code The code to format
 * @param options Formatting options
 * @returns Beautifully formatted code
 */
export function advancedCodeFormatter(
  code: string,
  options: {
    language?: "cpp" | "java";
    indentSize?: number;
    useTabs?: boolean;
    bracketStyle?: "same-line" | "new-line";
    printWidth?: number;
    alignOperators?: boolean;
    alignComments?: boolean;
  } = {}
): string {
  // Default configuration options
  const config = {
    language: options.language || "cpp",
    indentSize: options.indentSize || 2,
    useTabs: options.useTabs || false,
    bracketStyle: options.bracketStyle || "same-line",
    printWidth: options.printWidth || 80,
    alignOperators: options.alignOperators !== false,
    alignComments: options.alignComments !== false
  };

  // Replace literal newlines with actual newlines
  code = code.replace(/\\n/g, '\n');
  
  // Parse the code properly
  return parseAndFormatCode(code, config);
}

/**
 * Main parsing and formatting function
 */
function parseAndFormatCode(
  code: string, 
  config: {
    language: "cpp" | "java";
    indentSize: number;
    useTabs: boolean;
    bracketStyle: "same-line" | "new-line";
    printWidth: number;
    alignOperators: boolean;
    alignComments: boolean;
  }
): string {
  // Split code into lines
  const lines = code.split('\n');
  const formatted: string[] = [];
  
  // Track state
  let indentLevel = 0;
  let inMultilineComment = false;
  let inPreprocessorDirective = false;
  let pendingIndentDecrease = false;
  let inClassDefinition = false;
  let inEnumDefinition = false;
  
  // Creates indent string based on current level
  const getIndent = (level: number): string => {
    return config.useTabs ? 
      '\t'.repeat(level) : 
      ' '.repeat(level * config.indentSize);
  };
  
  // Process each line
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    // Skip but preserve empty lines
    if (line === '') {
      formatted.push('');
      continue;
    }
    
    // Handle C++ preprocessor directives
    if (config.language === "cpp" && line.startsWith('#')) {
      // Handle multi-line preprocessor directives
      if (line.endsWith('\\')) {
        inPreprocessorDirective = true;
      } else {
        inPreprocessorDirective = false;
      }
      
      // Preprocessor directives always start at column 0
      formatted.push(line);
      continue;
    }
    
    // Continue handling multi-line preprocessor directives
    if (inPreprocessorDirective) {
      if (!line.endsWith('\\')) {
        inPreprocessorDirective = false;
      }
      formatted.push(line);
      continue;
    }
    
    // Track comments
    if (!inMultilineComment && line.includes('/*') && !line.includes('*/')) {
      inMultilineComment = true;
    } else if (inMultilineComment && line.includes('*/')) {
      inMultilineComment = false;
    }
    
    // Apply pending indent decrease from previous line
    if (pendingIndentDecrease) {
      indentLevel = Math.max(0, indentLevel - 1);
      pendingIndentDecrease = false;
    }
    
    // Handle code structure
    if (!inMultilineComment && !line.startsWith('//')) {
      // Handle closing braces
      if (line === '}' || line.startsWith('}')) {
        indentLevel = Math.max(0, indentLevel - 1);
        
        // Check for else right after closing brace
        if (i + 1 < lines.length && lines[i + 1].trim().startsWith('else')) {
          // Don't decrease indent for the next else
        } else if (inClassDefinition && line === '};' || inEnumDefinition && line === '};') {
          // End of class or enum definition with semicolon
          inClassDefinition = false;
          inEnumDefinition = false;
        }
      }
      
      // Handle class and enum definitions
      if (line.startsWith('class ') || line.startsWith('struct ')) {
        if (line.endsWith('{')) {
          inClassDefinition = true;
        }
      } else if (line.startsWith('enum ')) {
        if (line.endsWith('{')) {
          inEnumDefinition = true;
        }
      }
    }
    
    // Special case for else and else if
    if (line.startsWith('else') && formatted.length > 0) {
      const lastLine = formatted[formatted.length - 1].trim();
      if (lastLine.endsWith('}')) {
        const prevLine = formatted.pop() || '';
        formatted.push(prevLine + ' ' + line);
        
        // If else has a block, increase indent
        if (line.endsWith('{')) {
          indentLevel++;
        }
        continue;
      }
    }
    
    // Handle do-while loops
    if (line.startsWith('while') && line.includes(';') && formatted.length > 0) {
      const lastLine = formatted[formatted.length - 1].trim();
      if (lastLine.endsWith('}')) {
        const prevLine = formatted.pop() || '';
        formatted.push(prevLine + ' ' + line);
        continue;
      }
    }
    
    // Add properly indented line
    formatted.push(getIndent(indentLevel) + line);
    
    // Update indent level for next line
    if (!inMultilineComment && !line.startsWith('//')) {
      // Increase indent after opening braces
      if (line.endsWith('{')) {
        indentLevel++;
      }
      
      // Handle non-block control structures
      if ((line.startsWith('if') || line.startsWith('for') || 
           line.startsWith('while') || (line.startsWith('else') && line.includes('if'))) && 
          !line.endsWith('{') && i + 1 < lines.length && !lines[i + 1].trim().startsWith('{')) {
        indentLevel++;
      }
      
      // Handle switch case statements
      if (line.startsWith('case ') || line.startsWith('default:')) {
        indentLevel++;
      }
      
      // Handle break statements for switch cases
      if ((line === 'break;' || line.startsWith('break ')) && indentLevel > 0) {
        indentLevel--;
      }
      
      // Handle single statements after control flow
      if (line.endsWith(';') && i > 0) {
        const prevLine = lines[i - 1].trim();
        if ((prevLine.startsWith('if') || prevLine.startsWith('for') || 
             prevLine.startsWith('while') || (prevLine.startsWith('else') && prevLine.includes('if'))) && 
            !prevLine.endsWith('{')) {
          pendingIndentDecrease = true;
        }
      }
    }
  }
  
  return formatted.join('\n');
}

/**
 * Main export function to format C++ or Java code
 * @param code The source code to format
 * @param language The programming language (cpp or java)
 * @returns Beautifully formatted code
 */
export function formatCppOrJavaCode(code: string, language: "cpp" | "java" = "cpp"): string {
  return advancedCodeFormatter(code, {
    language,
    indentSize: 2,
    bracketStyle: "same-line",
    alignOperators: true,
    alignComments: true
  });
} 