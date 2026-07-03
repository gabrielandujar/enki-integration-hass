"""Guard against deprecated Home Assistant const imports (removed in HA 2026+)."""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPONENT = REPO_ROOT / "custom_components" / "enki"

# Removed from homeassistant.const — use UnitOf* StrEnum members instead.
BANNED_CONST_SYMBOLS = frozenset(
    {
        "ENERGY_KILO_WATT_HOUR",
        "ENERGY_WATT_HOUR",
        "ENERGY_MEGAJOULE",
        "POWER_WATT",
        "POWER_KILO_WATT",
        "TEMP_CELSIUS",
        "TEMP_FAHRENHEIT",
        "TEMP_KELVIN",
    }
)

# Still present as aliases today but prefer UnitOf* in new code.
LEGACY_UNIT_ALIASES = frozenset({"PERCENTAGE"})


def _const_imports_from_ast(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        if node.module != "homeassistant.const":
            continue
        for alias in node.names:
            names.add(alias.name)
    return names


def test_no_removed_home_assistant_const_symbols() -> None:
    violations: list[str] = []
    for path in sorted(COMPONENT.rglob("*.py")):
        banned = _const_imports_from_ast(path) & BANNED_CONST_SYMBOLS
        if banned:
            rel = path.relative_to(REPO_ROOT)
            violations.append(f"{rel}: {sorted(banned)}")
    assert not violations, "Removed HA const imports found:\n" + "\n".join(violations)


def test_sensor_uses_modern_unit_enums() -> None:
    source = (COMPONENT / "sensor.py").read_text(encoding="utf-8")
    assert "UnitOfEnergy" in source
    assert "UnitOfRatio" in source
    assert "ENERGY_KILO_WATT_HOUR" not in source
    assert "PERCENTAGE" not in re.findall(
        r"from homeassistant\.const import \((.*?)\)",
        source,
        flags=re.DOTALL,
    )


def test_no_legacy_percentage_import_in_component() -> None:
    violations: list[str] = []
    for path in sorted(COMPONENT.rglob("*.py")):
        if "PERCENTAGE" in _const_imports_from_ast(path):
            violations.append(str(path.relative_to(REPO_ROOT)))
    assert not violations, "Use UnitOfRatio.PERCENTAGE instead of PERCENTAGE in:\n" + "\n".join(
        violations
    )
