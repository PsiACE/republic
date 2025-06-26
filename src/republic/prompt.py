import importlib

try:
    importlib.util.find_spec("republic_prompt")
    from republic_prompt import *  # noqa: F403, F401
except ImportError:
    print(
        "`republic-prompt` is not installed. Please add it or add `republic[prompt]` to your project dependencies."
    )
    exit(1)
