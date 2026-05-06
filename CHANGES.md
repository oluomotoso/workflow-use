# CHANGES — cache-replay branch

This is a fork of [browser-use/workflow-use](https://github.com/browser-use/workflow-use) maintained by [@oluomotoso](https://github.com/oluomotoso). The `cache-replay` branch carries 6 generic adaptations that make workflow-use suitable as a deterministic-replay engine for any consumer (the original use case is browser-task caching, but the changes are generic).

## Pinned upstream

Branched from upstream `main` at commit `59ec570` (Bump faiss-cpu).

## Adaptations

| Commit | Type | Status |
|---|---|---|
| `pydantic-v2: migrate validators to field_validator across all views` | upstreamable | (PR pending) |
| `element_finder: harden xpath quote escaping via concat()` | upstreamable (security fix) | (PR pending) |
| `semantic_extractor: install JS via addInitScript instead of per-call evaluate` | upstreamable (perf) | (PR pending) |
| `step_verifier: disable AI mode by default; LLM=None` | cache-replay-only | — |
| `service: disable run_as_tool LLM input parsing` | cache-replay-only | — |
| `service: drop browser_use Agent fallback in _execute_step` | cache-replay-only | — |

## Re-syncing with upstream

```bash
git fetch upstream
git checkout cache-replay
git rebase upstream/main cache-replay
# Resolve conflicts as they arise (most are isolated to the 5-6 patched files)
git push --force-with-lease origin cache-replay
git tag cache-replay-vN  # bump version
git push origin cache-replay-vN
```

## License

MIT (matches upstream). The 6 adaptations are MIT-licensed contributions to the workflow-use ecosystem.
