"""Text that comes from an API or a chain is data, never instructions."""
import re

CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f‪-‮⁦-⁩]")


def clean_text(value, limit=400):
    """Strip control and bidirectional-override characters and bound the length."""
    text = CONTROL.sub("", str(value))
    return text if len(text) <= limit else text[:limit] + "…"
