"""Unit tests for the markdown formatting module - Task 5b."""

import pytest

from app.services.markdown import (
    convert_to_markdown,
    format_bullet,
    format_heading,
    is_bullet,
    is_heading,
    is_numbered_heading,
    is_short_line,
    is_uppercase_heading,
    to_markdown,
)


def test_is_short_line():
    assert is_short_line("CORTA") is True
    assert is_short_line("Una línea con pocas palabras") is True
    assert is_short_line("") is False
    assert is_short_line("   ") is False
    long_line = " ".join(["palabra"] * 25)
    assert is_short_line(long_line) is False


def test_is_uppercase_heading():
    assert is_uppercase_heading("INTRODUCCIÓN") is True
    assert is_uppercase_heading("RESUMEN EJECUTIVO") is True
    assert is_uppercase_heading("12345") is False
    assert is_uppercase_heading("Introducción") is False
    assert is_uppercase_heading("PARTE DE UN TEXTO MUY LARGO QUE SUPERA EL LIMITE DE PALABRAS PERMITIDO PARA SER UN TITULO") is False


def test_is_numbered_heading():
    assert is_numbered_heading("1. Introducción") is True
    assert is_numbered_heading("1.1 Marco Teórico") is True
    assert is_numbered_heading("2) Objetivos") is True
    assert is_numbered_heading("No numerado") is False
    assert is_numbered_heading("12345") is False


def test_is_bullet_and_format():
    assert is_bullet("* Elemento") is True
    assert is_bullet("+ Elemento") is True
    assert is_bullet("- Elemento") is True
    assert is_bullet("• Elemento") is True
    assert is_bullet("Normal text") is False

    assert format_bullet("* Item") == "- Item"
    assert format_bullet("+ Item") == "- Item"
    assert format_bullet("• Item") == "- Item"
    assert format_bullet("- Item") == "- Item"


def test_format_heading():
    assert format_heading("TITULO") == "# TITULO"
    assert format_heading("# YA ES TITULO") == "# YA ES TITULO"


def test_to_markdown_empty_and_whitespace():
    assert to_markdown("") == ""
    assert to_markdown("   \n\n  ") == ""
    assert convert_to_markdown("") == ""


def test_to_markdown_full_example():
    sample_text = """TITULO PRINCIPAL

Este es el primer párrafo con información importante
sobre el proyecto en desarrollo.

1. OBJETIVOS ESPECÍFICOS
* Primer objetivo a cumplir
+ Segundo objetivo a cumplir
- Tercer objetivo a cumplir
• Cuarto objetivo a cumplir

CONCLUSIÓN
Párrafo final que concluye el documento."""

    result = to_markdown(sample_text)

    # Verifica encabezados marcados con #
    assert "# TITULO PRINCIPAL" in result
    assert "# 1. OBJETIVOS ESPECÍFICOS" in result
    assert "# CONCLUSIÓN" in result

    # Verifica que las viñetas se hayan normalizado a "- "
    assert "- Primer objetivo a cumplir" in result
    assert "- Segundo objetivo a cumplir" in result
    assert "- Tercer objetivo a cumplir" in result
    assert "- Cuarto objetivo a cumplir" in result
    assert "* Primer objetivo" not in result
    assert "+ Segundo objetivo" not in result
    assert "• Cuarto objetivo" not in result

    # Verifica separación de párrafos
    assert "\n\n" in result
    assert "Párrafo final que concluye el documento." in result
