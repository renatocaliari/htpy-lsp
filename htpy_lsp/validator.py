import ast
from lsprotocol.types import Diagnostic, DiagnosticSeverity, Range, Position, PositionEncodingKind

# common html tags to check
HTPY_TAGS = {
    "a", "abbr", "address", "area", "article", "aside", "audio", "b", "base", "bdi", "bdo", "blockquote", 
    "body", "br", "button", "canvas", "caption", "cite", "code", "col", "colgroup", "data", "datalist", 
    "dd", "del", "details", "dfn", "dialog", "div", "dl", "dt", "em", "embed", "fieldset", "figcaption", 
    "figure", "footer", "form", "h1", "h2", "h3", "h4", "h5", "h6", "head", "header", "hgroup", "hr", 
    "html", "i", "iframe", "img", "input", "ins", "kbd", "label", "legend", "li", "link", "main", "map", 
    "mark", "menu", "meta", "meter", "nav", "noscript", "object", "ol", "optgroup", "option", "output", 
    "p", "picture", "pre", "progress", "q", "rp", "rt", "ruby", "s", "samp", "script", "section", "select", 
    "slot", "small", "source", "span", "strong", "style", "sub", "summary", "sup", "table", "tbody", "td", 
    "template", "textarea", "tfoot", "th", "thead", "time", "title", "tr", "track", "u", "ul", "var", 
    "video", "wbr"
}

class HtpyVisitor(ast.NodeVisitor):
    def __init__(self):
        self.diagnostics = []

    def visit_Call(self, node):
        # Rule: Detect usage of HTMLResponse with htpy elements, suggest HtpyResponse
        if isinstance(node.func, ast.Name) and node.func.id == "HTMLResponse":
            found_htpy = False
            for arg in node.args:
                if self._contains_htpy(arg):
                    found_htpy = True
                    break
            if not found_htpy:
                for kw in node.keywords:
                    if kw.arg == "content" and self._contains_htpy(kw.value):
                        found_htpy = True
                        break
            
            if found_htpy:
                 self.add_diagnostic(
                    node,
                    "Prefer using 'HtpyResponse(...)' instead of manual 'HTMLResponse(...)' with htpy elements."
                )

        # Rule: Detect manual string conversion str(htpy_element)
        if isinstance(node.func, ast.Name) and node.func.id == "str":
            if node.args and self._is_htpy_element(node.args[0]):
                self.add_diagnostic(
                    node, 
                    "Avoid manual string conversion of htpy elements. Use 'HtpyResponse' or return the element directly."
                )

        # We are looking for calls to htpy tags: tag(...)
        is_htpy_tag_call = self._is_htpy_element(node.func)
        
        if is_htpy_tag_call:
            # Rule 1: Content in () is invalid (except .class or data.*)
            for arg in node.args:
                is_valid_positional = False
                
                # Check for class shorthand: ".class"
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith("."):
                    is_valid_positional = True
                
                # Check for Datastar helper: data.on(...), data.attr(...)
                elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
                    if isinstance(arg.func.value, ast.Name) and arg.func.value.id == "data":
                        is_valid_positional = True
                
                if not is_valid_positional:
                     self.add_diagnostic(
                        arg, 
                        f"Content '{self.get_arg_text(arg)}' should be in brackets [], not parentheses (). Parentheses are exclusively for attributes (keyword arguments) or specialized helpers like data.*."
                    )
        
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Check return annotation
        if not node.returns:
            self.generic_visit(node)
            return

        is_htpy_response = False
        if isinstance(node.returns, ast.Name) and node.returns.id == "HtpyResponse":
            is_htpy_response = True
        elif isinstance(node.returns, ast.Attribute) and node.returns.attr == "HtpyResponse":
            is_htpy_response = True
            
        if is_htpy_response:
            for child in ast.walk(node):
                if isinstance(child, ast.Return) and child.value:
                    if self._is_htpy_element(child.value):
                         self.add_diagnostic(
                            child.value,
                            "Function returns a raw htpy Element but is annotated as returning 'HtpyResponse'. Ensure you are wrapping it: return HtpyResponse(div[...])"
                        )
        
        self.generic_visit(node)

    def _is_htpy_element(self, node):
        """Check if a node looks like an htpy element: div, div(...), div[...]"""
        # Case 1: tag -> Name
        if isinstance(node, ast.Name):
            return node.id in HTPY_TAGS
        
        # Case 2: htpy.tag -> Attribute
        if isinstance(node, ast.Attribute):
            return node.attr in HTPY_TAGS

        # Case 3: tag(...) -> Call
        if isinstance(node, ast.Call):
            return self._is_htpy_element(node.func)
            
        # Case 4: tag[...] -> Subscript
        if isinstance(node, ast.Subscript):
            return self._is_htpy_element(node.value)
            
        return False

    def _contains_htpy(self, node):
        if self._is_htpy_element(node):
            return True
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "str":
            if node.args and self._is_htpy_element(node.args[0]):
                return True
        return False

    def get_arg_text(self, node):
        if isinstance(node, ast.Constant):
            return str(node.value)
        return "..."

    def add_diagnostic(self, node, message):
        # ast lines are 1-based, lsp lines are 0-based
        range = Range(
            start=Position(line=node.lineno - 1, character=node.col_offset),
            end=Position(line=node.end_lineno - 1, character=node.end_col_offset)
        )
        self.diagnostics.append(Diagnostic(
            range=range,
            message=message,
            severity=DiagnosticSeverity.Warning,
            source="htpy-lsp"
        ))

def validate_document(doc):
    try:
        tree = ast.parse(doc.source)
        visitor = HtpyVisitor()
        visitor.visit(tree)
        return visitor.diagnostics
    except SyntaxError as e:
        # Convert Python SyntaxError to LSP Diagnostic
        # lineno/offset can be None
        line = (e.lineno - 1) if e.lineno is not None else 0
        char = (e.offset - 1) if e.offset is not None else 0
        
        range = Range(
            start=Position(line=line, character=char),
            end=Position(line=line, character=char + 1)
        )
        return [Diagnostic(
            range=range,
            message=f"Syntax Error: {e.msg}",
            severity=DiagnosticSeverity.Error,
            source="htpy-lsp"
        )]
    except Exception as e:
        return []
