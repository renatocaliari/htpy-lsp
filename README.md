# htpy-lsp

A Language Server Protocol (LSP) server for validating `htpy` coding usage, including **Datastar** integration patterns.

## Rules Enforced

1. **Attributes in Parentheses**: Use keyword arguments like `div(class_="foo")`. (Note: use `class_`, not `cls`).
2. **Content in Brackets**: `div["Hello"]`
3. **No Positional Arguments in Parentheses**:
   - **Invalid**: `div("Hello")` -> **Warning** (Use `div["Hello"]` instead)
   - **Exception 1**: Class shorthand `div(".my-class")` is allowed.
   - **Exception 2**: Datastar helpers `data.on(...)`, `data.attr(...)` are allowed as positional arguments.
4. **Return Type Consistency**:
   - If a function is annotated to return `HtpyResponse` (or `-> HtpyResponse`), it should return a `HtpyResponse(...)` wrapper, not a raw `htpy` element (`div[...]`).
5. **String Conversion**:
   - Avoid manual casting of `htpy` elements to string. Use `HtpyResponse`.
6. **Prefer HtpyResponse**:
   - Warns when `HTMLResponse` is used with `htpy` content.

## Installation

```bash
pip install .
```

## Usage Examples

### Proper Syntax

```python
from htpy import div, span

# ✅ Correct: Attributes in (), content in []
div(class_="container")[
    span(".text-bold")["Hello World"]
]

# ✅ Correct: Standalone tags or attributes only
my_div = div
attrs_only = div(id="main")

# ❌ Incorrect: Content in ()
div("Hello")  # Use div["Hello"]

# ❌ Incorrect: Syntax not supported by htpy (or invalid Python)
# div[class_="foo"]  # Attributes must be in ()
```

### Datastar & Responses

```python
from datastar_py import attribute_generator as data
from starlette.responses import HTMLResponse

# ✅ Correct: Datastar in ()
button(data.on("click", "increment"))["+"]

# ✅ Correct: HtpyResponse wrapper
def home() -> HtpyResponse:
    return HtpyResponse(div["Hello"])

# ❌ Warning: Manual wrapping
def bad() -> HtpyResponse:
    return HTMLResponse(content=str(div["Oops"])) # Suggests HtpyResponse
```
