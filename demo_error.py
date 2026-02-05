from htpy import div, span
from datastar_py import attribute_generator as data

# ❌ Should be flagged: Content in parentheses
div("This should be a warning")

# ❌ Should be flagged: Incorrect Shorthand Order
# Class/ID shorthands should be at the beginning
div(data.on("click", "..."), ".btn")

# ❌ Should be flagged: Incorrect Attribute Names
# htpy uses class_, not cls or class
div(cls="container")

# ✅ Correct Usage
div(".container")[
    span(".text-bold", data.on("hover", "do()"))["Hello"]
]

# ❌ Should be flagged: Mixed positional and keyword
span("Content", id="my-span")

# ❌ Should be flagged: str() conversion
print(str(div["No manual str please"]))
