import ast
from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

# Common htpy tags to monitor
HTPY_TAGS = {
    "div", "span", "a", "p", "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "li", "ol", "form", "input", "button", "label", "img",
    "section", "header", "footer", "nav", "main", "article", "aside"
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
            # Rule: Protect against 'class' or 'cls' instead of 'class_'
            for kw in node.keywords:
                if kw.arg in {"class", "cls"}:
                    self.add_diagnostic(
                        kw,
                        f"Use 'class_' instead of '{kw.arg}' for htpy attributes. 'class' is a Python reserved keyword and 'cls' is not the expected name for htpy."
                    )
                
                # Rule: Detect manual data_... keyword arguments
                if kw.arg and kw.arg.startswith("data_"):
                    helper_name = kw.arg[5:].replace("_", ".")
                    self.add_diagnostic(
                        kw,
                        f"Avoid manual keyword argument '{kw.arg}'. Use the 'data.' helper at the beginning of the parentheses. "
                        f"Example: data.{helper_name}(...)"
                    )
                
                # Rule: Detect **{"data-...": ...} unpacking
                if kw.arg is None and isinstance(kw.value, ast.Dict):
                    for i, key_node in enumerate(kw.value.keys):
                        if key_node and isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
                            if key_node.value.startswith("data-"):
                                self.add_diagnostic(
                                    kw,
                                    f"Do not use unpacking '**' or 'data-' format for '{key_node.value}'. "
                                    f"Use the 'data.' helper as the first arguments in the parentheses."
                                )

            # Rule 1: Content in () is invalid (except .class or data.*)
            # Rule: Class shorthand order - must be at the beginning of positional args
            non_shorthand_seen = False
            for arg in node.args:
                is_valid_positional = False
                
                # 1. Shorthand: ".class", "#id"
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.startswith((".", "#")):
                    is_valid_positional = True
                    if non_shorthand_seen:
                         self.add_diagnostic(
                            arg,
                            f"Class/ID shorthand '{arg.value}' should be positioned at the beginning of parentheses, before other positional helpers like data.*."
                        )
                
                # 2. Datastar/Helpers: data.on(), data.signals, etc.
                elif isinstance(arg, ast.Call) and isinstance(arg.func, ast.Attribute):
                    if isinstance(arg.func.value, ast.Name) and arg.func.value.id == "data":
                        is_valid_positional = True
                        non_shorthand_seen = True
                
                # 3. Variables/Signals/Attributes: approval_signals, user.attrs, *items
                # We allow these to avoid false positives with helpers/signals stored in variables.
                elif isinstance(arg, (ast.Name, ast.Attribute, ast.Starred)):
                    is_valid_positional = True
                    non_shorthand_seen = True

                if not is_valid_positional:
                     msg = f"Content '{self.get_arg_text(arg)}' should be in brackets [], not parentheses ()."
                     if self._is_htpy_element(arg):
                         msg = f"Nested htpy element '{self.get_arg_text(arg)}' should be in brackets [], not parentheses ()."
                     
                     self.add_diagnostic(
                        arg, 
                        f"{msg} Parentheses are exclusively for attributes (keyword arguments) or specialized helpers like data.*."
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
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Call):
             return f"{self.get_arg_text(node.func)}(...)"
        if isinstance(node, ast.Subscript):
            return f"{self.get_arg_text(node.value)}[...]"
        if isinstance(node, ast.Attribute):
             return f"{self.get_arg_text(node.value)}.{node.attr}"
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
        # Sort diagnostics by line then character
        visitor.diagnostics.sort(key=lambda d: (d.range.start.line, d.range.start.character))
        return visitor.diagnostics
    except SyntaxError as e:
        # Convert Python SyntaxError to LSP Diagnostic
        # This error blocks the AST visitor, so we provide an explicit message.
        range = Range(
            start=Position(line=e.lineno - 1, character=e.offset - 1),
            end=Position(line=e.lineno - 1, character=e.offset)
        )
        return [Diagnostic(
            range=range,
            message=f"Python Syntax Error: {str(e)}. (This error is blocking full htpy logic validation)",
            severity=DiagnosticSeverity.Error,
            source="htpy-lsp"
        )]
    except Exception as e:
        return []
