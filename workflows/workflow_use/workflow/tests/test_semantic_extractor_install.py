"""
Tests for semantic_extractor init-script install behaviour.

Verifies the per-Page install caching: the first ``extract_interactive_elements``
call triggers ``page.add_init_script`` + a one-shot ``page.evaluate`` of the
~5KB extractor body; subsequent calls on the same Page only invoke the
pre-installed ``window.__wfu_extract`` function with a tiny payload.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from workflow_use.workflow.semantic_extractor import SemanticExtractor


def _make_fake_page() -> MagicMock:
	"""A minimal stand-in for browser-use's Page that records add_init_script
	+ evaluate calls and returns a canned extractor result."""
	page = MagicMock()
	page.add_init_script = AsyncMock()
	# Each evaluate call returns the canned shape that the Python side parses.
	page.evaluate = AsyncMock(return_value={'elements': [], 'debugLog': [], 'stats': {'processed': 0, 'errors': 0, 'total': 0}})
	return page


@pytest.mark.asyncio
async def test_install_runs_only_on_first_call_per_page():
	"""``add_init_script`` must fire exactly once per unique Page identity, and
	subsequent ``extract_interactive_elements`` calls just invoke the
	pre-installed function."""
	extractor = SemanticExtractor()
	page = _make_fake_page()

	await extractor.extract_interactive_elements(page)
	first_install_calls = page.add_init_script.call_count
	first_evaluate_calls = page.evaluate.call_count

	await extractor.extract_interactive_elements(page)
	second_install_calls = page.add_init_script.call_count
	second_evaluate_calls = page.evaluate.call_count

	# add_init_script should not be re-called on the second extraction.
	assert first_install_calls == 1, 'add_init_script should run on first extract'
	assert second_install_calls == 1, (
		f'add_init_script should NOT run a second time on the same Page (got {second_install_calls})'
	)
	# evaluate is called for both the install (1) and each extract invocation.
	# First extract: 1 install-evaluate + 1 invoke-evaluate = 2.
	# Second extract: only 1 invoke-evaluate. Total = 3.
	assert first_evaluate_calls == 2
	assert second_evaluate_calls == 3


@pytest.mark.asyncio
async def test_install_runs_per_distinct_page():
	"""A second Page object gets its own install — id(page) is the cache key."""
	extractor = SemanticExtractor()
	page_a = _make_fake_page()
	page_b = _make_fake_page()

	await extractor.extract_interactive_elements(page_a)
	await extractor.extract_interactive_elements(page_b)

	assert page_a.add_init_script.call_count == 1
	assert page_b.add_init_script.call_count == 1


@pytest.mark.asyncio
async def test_install_falls_back_to_evaluate_only_if_init_script_unsupported():
	"""Some Page relays don't implement add_init_script; the extractor must
	still install via evaluate and not crash."""
	extractor = SemanticExtractor()
	page = _make_fake_page()
	page.add_init_script = AsyncMock(side_effect=NotImplementedError('CDP relay does not support init scripts'))

	# Should not raise; should still call evaluate to install + invoke.
	await extractor.extract_interactive_elements(page)
	assert page.evaluate.call_count >= 1
