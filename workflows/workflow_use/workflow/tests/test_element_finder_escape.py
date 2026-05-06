"""
Tests for element_finder XPath quote escape hardening.

Verifies that ``_xpath_string_literal`` produces valid XPath 1.0 string
literals for any input value, including values that contain both single
and double quotes (the case the previous ``str.replace`` form mangled),
and an injection-attempt fixture that the XPath engine must treat as
data, never as syntax.
"""

import pytest

from workflow_use.workflow.element_finder import _js_string_literal, _xpath_string_literal


class TestXpathStringLiteral:
	def test_plain_string_uses_single_quotes(self):
		assert _xpath_string_literal('hello') == "'hello'"

	def test_string_with_single_quote_uses_double_quotes(self):
		# When only ' is present, double-quoting is the simpler/cleaner form.
		assert _xpath_string_literal("it's") == '"it\'s"'

	def test_string_with_double_quote_uses_single_quotes(self):
		assert _xpath_string_literal('say "hi"') == '\'say "hi"\''

	def test_string_with_both_quotes_uses_concat(self):
		# Must split on the single-quote character and emit a concat() form.
		result = _xpath_string_literal("it's a \"test\"")
		assert result == 'concat(\'it\', "\'", \'s a "test"\')'

	def test_empty_string_uses_single_quotes(self):
		assert _xpath_string_literal('') == "''"

	def test_only_single_quote(self):
		# A bare ' is a single-quote-only value, so the double-quote branch
		# wraps it as "'".
		assert _xpath_string_literal("'") == '"\'"'

	def test_injection_attempt_with_double_quotes_only(self):
		# Attacker-controlled value that tries to escape an attribute selector
		# context like //*[@id='<value>'] and pivot to a password input. With
		# only " characters, the literal is wrapped in single quotes — the
		# entire payload is preserved as XPath string data, not syntax.
		payload = '"]/preceding::input[@type="password"]["'
		result = _xpath_string_literal(payload)
		# No ' in payload, so single-quote-wrapping is correct.
		assert result == f"'{payload}'"
		# Re-embedded XPath remains syntactically valid: the payload is
		# entirely inside a string literal and cannot escape it.
		full_xpath = f'//*[@id={result}]'
		assert full_xpath.count('[') == full_xpath.count(']')

	def test_injection_attempt_with_both_quotes(self):
		# Adversarial payload that contains BOTH ' and " — this is the case
		# the previous single-character escape mangled. concat() form is the
		# only correct XPath 1.0 representation.
		payload = "it's \"]/preceding::input[@type='password'][\""
		result = _xpath_string_literal(payload)
		assert result.startswith('concat(')
		# Every adversarial token is preserved as string data.
		assert 'preceding::input' in result
		# Re-embedding produces balanced syntax.
		full_xpath = f'//*[@id={result}]'
		assert full_xpath.count('(') == full_xpath.count(')')


class TestJsStringLiteral:
	def test_plain_string_round_trip(self):
		# json.dumps wraps in double quotes by default.
		assert _js_string_literal('hello') == '"hello"'

	def test_string_with_quotes_is_safe(self):
		# Both ' and " are handled correctly; previous str.replace form would
		# leave the " unescaped and break the surrounding JS string.
		result = _js_string_literal('it\'s "test"')
		assert result == '"it\'s \\"test\\""'

	def test_backslash_is_escaped(self):
		assert _js_string_literal('a\\b') == '"a\\\\b"'

	def test_newline_is_escaped(self):
		assert _js_string_literal('a\nb') == '"a\\nb"'


if __name__ == '__main__':
	pytest.main([__file__, '-v'])
