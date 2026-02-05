# htpy-lsp (python)

A Language Server Protocol (LSP) server for validating `htpy` coding usage, including **Datastar** and FastApi integration patterns.

> [!TIP]
> **Why this matters?**
> While `htpy` is powerful and type-safe, its syntax (brackets for content, parentheses for attributes) can be counter-intuitive for developers coming from React/Jinja.
> **LLMs and AI coding assistants frequently fail** to follow these rules, often nesting content in parentheses. This LSP serves as a critical safety net for both humans and AI to ensure correct code generation and execution.

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

### Global Installation (Recommended)

Using `uv` to install the tool globally and isolated:

```bash
uv tool install htpy-lsp
# Or from local source:
uv tool install .
```

This creates a global `htpy-lsp` command.

## Editor Configuration

### 1. OpenCode

OpenCode uses `~/.opencode/config.json` for global LSP settings. Add the following:

```json
{
	"lsp": {
		"htpy-lsp": {
			"command": ["htpy-lsp"],
			"filetypes": ["python"]
		}
	}
}
```

### 2. VS Code

Since `htpy-lsp` is a custom server, you can use the [Generic LSP Client](https://marketplace.visualstudio.com/items?itemName=GoranSljivic.glspc) extension.

In your `settings.json`:

```json
{
	"glspc.server.command": "htpy-lsp",
	"glspc.server.languageId": "python",
	"glspc.server.label": "htpy-lsp"
}
```

_(Alternatively, for more robust multi-LSP support, consider extensions that allow multiple servers per language ID)._

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
from starlette.responses import HtpyResponse
from fastapi.responses import HTMLResponse

# ✅ Correct: Datastar in ()
button(data.on("click", "$count += 1"))["+"]

# ✅ Correct: HtpyResponse wrapper
def home() -> HtpyResponse:
    return HtpyResponse(div["Hello"])

# ❌ Warning: Manual wrapping
def bad() -> HtpyResponse:
    return HTMLResponse(content=str(div["Oops"])) # Suggests HtpyResponse
```
