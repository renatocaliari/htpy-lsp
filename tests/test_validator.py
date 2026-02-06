import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dataclasses import dataclass
from unittest.mock import MagicMock
import types

# ---------------------------------------------------------
# USE REAL LSP PROTOCOL
# ---------------------------------------------------------
from lsprotocol.types import Diagnostic, Range, Position

from htpy_lsp.validator import validate_document

@dataclass
class MockDocument:
    source: str

def test_validator():
    # TEST CASE SCHEMA: (source_code, expected_error_count)
    # 0 = PASS (Correct syntax and logic)
    # 1+ = FAIL (Either SyntaxError or logic violation)
    
    cases = [
        # --- BASIC SYNTAX & ATTRIBUTES ---
        ("div(id='foo')", 0),                        # PASS: Valid attributes
        ("div(id='foo')['content']", 0),             # PASS: Attributes then content
        ("div['content']", 0),                       # PASS: Content only
        ("div(class_='teste')[div['test']]", 0),     # PASS: Nested standard usage
        ("div", 0),                                   # PASS: Standalone tag
        ("div(class_='teste')", 0),                   # PASS: Attributes only
        
        # --- SYNTAX ERRORS (Python doesn't allow these) ---
        ("div[class_='teste', div['test']]", 1),     # FAIL: Keywords in [] (Syntax Error)
        ("div[class_='teste'][div['test']]", 1),      # FAIL: Keywords in [] (Syntax Error)
        ("div[class_='teste'](div['test'])", 1),     # FAIL: Keywords in [] (Syntax Error)
        ("div[]", 1),                                 # FAIL: Empty brackets (Syntax Error)
        ("div(class_='teste')[]", 1),                 # FAIL: Empty brackets (Syntax Error)
        
        # --- LOGIC ERRORS (Valid Python, Invalid htpy usage) ---
        ("div('content')", 1),                        # FAIL: Content in ()
        ("span('content')", 1),                      # FAIL: Content in ()
        ("span('content', id='bar')", 1),            # FAIL: Mixed content/attrs in ()
        ("htpy.div('content')", 1),                   # FAIL: htpy prefix + content in ()
        ("div(data.on('click'), 'content')", 1),     # FAIL: Mixed valid helper + invalid content
        ("str(div['hello'])", 1),                     # FAIL: Manual string conversion
        
        # --- DATASTAR_PY & SPECIAL HELPERS ---
        ("div(data.on('click', 'action'))", 0),      # PASS: data.* helper in ()
        ("div(data.on('click', 'action'), id='foo', class_='bar')", 0),      # PASS: data.* helper in ()
        ("div(id='foo', class_='bar', **props)", 0), # PASS: Multiple attributes
        ("div('.my-class', data.on('click', '...'))", 0), # PASS: Shorthand first
        ("div(data.on('click', '...'), '.my-class')", 1), # FAIL: Shorthand after other helper
        
        # --- ATTR NAMES (class vs class_) ---
        ("div(class_='foo')", 0),                     # PASS: class_ is correct
        ("div(cls='foo')", 1),                        # FAIL: cls is incorrect
        ("div(class='foo')", 1),                      # FAIL: Syntax Error (reserved word)
        
        # --- COMPLEX NESTED EXAMPLES ---
        ("""
div(
    h2(class_="text-3xl font-bold")["My Clients"],
    div(
        input(
             type_="text",
             placeholder="Search clients...",
             class_="input input-bordered w-full max-w-xs",
             data_bind="searchQuery", 
        ),
        button(
            class_="btn btn-primary",
            onclick="window.location.href='/clients/new'",
        )("New Client"),
        class_="flex gap-4",
    ),
    class_="flex justify-between items-center mb-6",
)
        """, 5), # Expected 5: h2 in div, nested div in div, input in inner div, button call in inner div, string in button
        
        # --- RESPONSE & RETURN TYPES ---
        ("HTMLResponse(div['hello'])", 1),           # FAIL: Suggest HtpyResponse
        ("HTMLResponse(str(div['hello']))", 2),      # FAIL: Suggest HtpyResponse + no str()
        
        # Complex return type logic
        ("""
def view() -> HtpyResponse:
    return HtpyResponse(div['hello'])
""", 0),                                             # PASS: Correct wrapped return
        ("""
def view() -> HtpyResponse:
    return div['hello']
""", 1),                                             # FAIL: Raw element returned as HtpyResponse
        ("""
def view():
    return div['hello']
""", 0),                                             # PASS: No annotation, no enforcement
    ]

    print("\nRunning merged test suite...")
    print("-" * 60)
    failed_any = False
    
    for i, (source, expected) in enumerate(cases):
        doc = MockDocument(source=source)
        diagnostics = validate_document(doc)
        actual = len(diagnostics)
        
        status = "✅" if actual == expected else "❌"
        if actual != expected: failed_any = True
        
        # Clean up source for printing
        display_source = source.strip().replace("\n", " \\ ")
        print(f"[{i:02}] {status} {display_source[:40]:<40} | Exp: {expected} | Got: {actual}")
        
        if actual != expected:
            for d in diagnostics:
                print(f"      > {d.message}")

    print("-" * 60)
    if not failed_any:
        print("ALL TESTS PASSED!")
    else:
        print("SOME TESTS FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    test_validator()
