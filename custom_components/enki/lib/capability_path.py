"""Enki API capability name helpers."""


def capability_to_path_segment(name: str) -> str:
    """Referentiel snake_case to URL kebab-case."""
    return name.replace("_", "-")
