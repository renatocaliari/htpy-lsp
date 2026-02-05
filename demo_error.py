from htpy import div, span

# ❌ Should be flagged: Content in parentheses
div("This should be a warning")

# ❌ Should be flagged: Mixed positional and keyword
span("Content", id="my-span")

# ✅ Correct: Attributes in (), content in []

div(id="container")[
    span(".text-bold")["Hello World"]
]

# ❌ Should be flagged: str() conversion
print(str(div["No manual str please"]))
