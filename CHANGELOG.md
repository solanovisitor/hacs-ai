## v0.3.1 (monorepo logical)

- Facades: Removed references to synthetic fallback facades; all facades are now explicit per model. Updated `test_comprehensive_facades_llm.py` and docs.
- Docs: Clarified explicit facades and clarified `to_facade("extractable")` as a view, not a facade.
- Cleanup: Pruned debug scripts and legacy examples related to extraction debugging.
- Utils: Centralized helpers remain in `hacs_utils.core_utils` to avoid duplication.
- Version: Bumped `VersionManager` constants to reflect minor cleanup changes.


