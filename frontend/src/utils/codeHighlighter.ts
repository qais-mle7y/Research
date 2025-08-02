/**
 * Function to add syntax highlighting to C++ and Java code
 * @param code The code to highlight
 * @param language The programming language ('cpp' or 'java')
 * @returns HTML string with syntax highlighting classes
 */
export function applySyntaxHighlighting(code: string, language: string): string {
  if (!code) return '';
  
  // Define regex patterns for syntax highlighting
  const patterns: { [key: string]: { pattern: RegExp, className: string }[] } = {
    cpp: [
      // Preprocessor directives
      { pattern: /^(#include|#define|#ifdef|#ifndef|#endif|#else|#elif|#pragma)(\s+)([^\n]+)/gm, 
        className: '<span class="preprocessor">$1</span>$2<span class="string">$3</span>' },
      
      // Keywords
      { pattern: /\b(auto|break|case|catch|class|const|continue|default|delete|do|else|enum|explicit|export|extern|for|friend|goto|if|inline|namespace|new|operator|private|protected|public|return|sizeof|static|struct|switch|template|this|throw|try|typedef|typename|union|using|virtual|volatile|while)\b/g, 
        className: '<span class="keyword">$1</span>' },
      
      // Types
      { pattern: /\b(bool|char|double|float|int|long|short|signed|unsigned|void|string|vector|map|set|queue|stack|deque|list|pair|array|tuple|shared_ptr|unique_ptr|weak_ptr|nullptr_t|size_t|std::string|std::vector|std::map|std::set)\b/g, 
        className: '<span class="type">$1</span>' },
      
      // Numbers
      { pattern: /\b(\d+(\.\d+)?[fFlL]?)\b/g, 
        className: '<span class="number">$1</span>' },
      
      // Functions
      { pattern: /(\w+)(?=\s*\()/g, 
        className: '<span class="function">$1</span>' },
      
      // Comments (single line)
      { pattern: /(\/\/[^\n]*)/g, 
        className: '<span class="comment">$1</span>' },
      
      // Comments (multi line) - simplistic approach, might not work for all cases
      { pattern: /(\/\*[\s\S]*?\*\/)/g, 
        className: '<span class="comment">$1</span>' },
      
      // Strings
      { pattern: /("(?:\\.|[^"\\])*")/g, 
        className: '<span class="string">$1</span>' },
      
      // Characters
      { pattern: /('(?:\\.|[^'\\])*')/g, 
        className: '<span class="string">$1</span>' },
      
      // Operators
      { pattern: /(\+|-|\*|\/|%|=|==|!=|&lt;|&gt;|&lt;=|&gt;=|&&|\|\||!|\^|&|~|&lt;&lt;|&gt;&gt;|\+\+|--|\+=|-=|\*=|\/=|%=|&=|\|=|\^=|&lt;&lt;=|&gt;&gt;=)/g, 
        className: '<span class="operator">$1</span>' }
    ],
    
    java: [
      // Keywords
      { pattern: /\b(abstract|assert|boolean|break|byte|case|catch|char|class|const|continue|default|do|double|else|enum|extends|final|finally|float|for|goto|if|implements|import|instanceof|int|interface|long|native|new|package|private|protected|public|return|short|static|strictfp|super|switch|synchronized|this|throw|throws|transient|try|void|volatile|while)\b/g, 
        className: '<span class="keyword">$1</span>' },
      
      // Types and classes
      { pattern: /\b(String|Integer|Double|Boolean|Object|List|Map|Set|Collection|ArrayList|HashMap|HashSet|LinkedList|Vector|Queue|Deque|Stack)\b/g, 
        className: '<span class="type">$1</span>' },
      
      // Numbers
      { pattern: /\b(\d+(\.\d+)?[fFlLdD]?)\b/g, 
        className: '<span class="number">$1</span>' },
      
      // Functions
      { pattern: /(\w+)(?=\s*\()/g, 
        className: '<span class="function">$1</span>' },
      
      // Comments (single line)
      { pattern: /(\/\/[^\n]*)/g, 
        className: '<span class="comment">$1</span>' },
      
      // Comments (multi line)
      { pattern: /(\/\*[\s\S]*?\*\/)/g, 
        className: '<span class="comment">$1</span>' },
      
      // Strings
      { pattern: /("(?:\\.|[^"\\])*")/g, 
        className: '<span class="string">$1</span>' },
      
      // Characters
      { pattern: /('(?:\\.|[^'\\])*')/g, 
        className: '<span class="string">$1</span>' },
      
      // Annotations
      { pattern: /(@\w+)/g, 
        className: '<span class="preprocessor">$1</span>' },
      
      // Operators
      { pattern: /(\+|-|\*|\/|%|=|==|!=|&lt;|&gt;|&lt;=|&gt;=|&&|\|\||!|\^|&|~|\+\+|--|\+=|-=|\*=|\/=|%=|&=|\|=|\^=)/g, 
        className: '<span class="operator">$1</span>' }
    ]
  };
  
  // Escape HTML characters
  let htmlCode = code
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Apply syntax highlighting based on language
  const langPatterns = patterns[language] || patterns['cpp']; // default to cpp if language not found
  
  // Apply each pattern
  langPatterns.forEach(item => {
    htmlCode = htmlCode.replace(item.pattern, item.className);
  });
  
  // Add line numbers by splitting into lines
  const lines = htmlCode.split('\n');
  
  // Join back with line numbers
  return lines.map((line, index) => 
    `<span class="line-number" data-line-number="${index + 1}"></span>${line}`
  ).join('\n');
}

/**
 * Simpler version that just adds basic syntax highlighting 
 * without attempting to parse complex constructs
 */
export function simpleHighlight(code: string, language: string): string {
  if (!code) return '';
  
  // Escape HTML characters
  let htmlCode = code
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  
  // Define some simple patterns for common syntax elements
  const patterns = [
    // Keywords (common to many languages)
    { pattern: /\b(if|else|for|while|return|break|continue|switch|case|default|class|function|var|let|const|public|private|protected|static|void|int|float|double|string|bool|true|false|null|undefined|this|new|try|catch|throw|finally)\b/g, 
      className: '<span class="keyword">$1</span>' },
    
    // Numbers
    { pattern: /\b(\d+(\.\d+)?)\b/g, 
      className: '<span class="number">$1</span>' },
    
    // Strings with double quotes
    { pattern: /("(?:\\.|[^"\\])*")/g, 
      className: '<span class="string">$1</span>' },
    
    // Strings with single quotes
    { pattern: /('(?:\\.|[^'\\])*')/g, 
      className: '<span class="string">$1</span>' },
    
    // Comments (single line)
    { pattern: /(\/\/[^\n]*)/g, 
      className: '<span class="comment">$1</span>' }
  ];
  
  // Add language-specific patterns
  if (language === 'cpp') {
    patterns.push(
      // C++ preprocessor directives
      { pattern: /^(#include|#define|#ifdef|#ifndef|#endif)(\s+)([^\n]*)/gm, 
        className: '<span class="preprocessor">$1</span>$2<span class="string">$3</span>' }
    );
  } else if (language === 'java') {
    patterns.push(
      // Java annotations
      { pattern: /(@\w+)/g, 
        className: '<span class="preprocessor">$1</span>' }
    );
  }
  
  // Apply each pattern
  patterns.forEach(item => {
    htmlCode = htmlCode.replace(item.pattern, item.className);
  });
  
  return htmlCode;
} 