"""Tests for simple template formatting functionality."""

import pytest

from republic_prompt import format, format_with_functions


class TestSimpleFormat:
    """Test the simple format function."""

    def test_basic_variable_substitution(self):
        """Test basic variable substitution."""
        result = format("Hello {{ name }}!", name="Alice")
        assert result == "Hello Alice!"

    def test_multiple_variables(self):
        """Test multiple variable substitution."""
        result = format(
            "Hello {{ name }} from {{ city }}!", name="Bob", city="New York"
        )
        assert result == "Hello Bob from New York!"

    def test_with_custom_functions(self):
        """Test custom function integration."""

        def upper(text):
            return text.upper()

        def add_exclamation(text):
            return text + "!"

        result = format(
            "{{ upper(name) }} {{ add_exclamation(greeting) }}",
            custom_functions={"upper": upper, "add_exclamation": add_exclamation},
            name="alice",
            greeting="hello",
        )
        assert result == "ALICE hello!"

    def test_conditional_logic(self):
        """Test conditional logic in templates."""
        result = format(
            "{% if count > 1 %}{{ count }} items{% else %}1 item{% endif %}", count=3
        )
        assert result == "3 items"

        result = format(
            "{% if count > 1 %}{{ count }} items{% else %}1 item{% endif %}", count=1
        )
        assert result == "1 item"

    def test_loops(self):
        """Test loop functionality."""
        result = format(
            "{% for item in items %}{{ item }}{% if not loop.last %}, {% endif %}{% endfor %}",
            items=["apple", "banana", "cherry"],
        )
        assert result == "apple, banana, cherry"

    def test_format_with_functions_alias(self):
        """Test the format_with_functions alias."""

        def upper(text):
            return text.upper()

        result = format_with_functions(
            "Hello {{ upper(name) }}!", functions={"upper": upper}, name="alice"
        )
        assert result == "Hello ALICE!"

    def test_auto_escape(self):
        """Test auto-escape functionality."""
        result = format(
            "{{ content }}", auto_escape=True, content="<script>alert('xss')</script>"
        )
        # Should escape HTML
        assert "&lt;" in result and "&gt;" in result

    def test_no_auto_escape(self):
        """Test without auto-escape."""
        result = format(
            "{{ content }}", auto_escape=False, content="<script>alert('xss')</script>"
        )
        # Should not escape HTML
        assert result == "<script>alert('xss')</script>"

    def test_complex_template(self):
        """Test a complex template with multiple features."""

        def calculate_total(items):
            return sum(item.get("price", 0) for item in items)

        result = format(
            """Order for {{ customer }}:
{% for item in items %}
- {{ item.name }}: ${{ "%.2f"|format(item.price) }}
{% endfor %}
Total: ${{ "%.2f"|format(calculate_total(items)) }}""",
            custom_functions={"calculate_total": calculate_total},
            customer="John",
            items=[
                {"name": "Laptop", "price": 999.99},
                {"name": "Mouse", "price": 29.99},
            ],
        )

        assert "Order for John:" in result
        assert "Laptop: $999.99" in result
        assert "Mouse: $29.99" in result
        assert "Total: $1029.98" in result

    def test_error_handling(self):
        """Test error handling for invalid templates."""
        # Test undefined variable - Jinja2 will render empty string by default
        result = format("{{ undefined_variable }}")
        assert result == ""

        # Test calling undefined function - this should raise an exception
        with pytest.raises(Exception):
            format("{{ undefined_function() }}")

    def test_empty_template(self):
        """Test empty template."""
        result = format("")
        assert result == ""

    def test_template_with_no_variables(self):
        """Test template with no variables."""
        result = format("Hello, world!")
        assert result == "Hello, world!"
