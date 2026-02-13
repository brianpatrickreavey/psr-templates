## Plan: Update CI Workflows for ACT and GitHub Compatibility with PSR Local Execution

**STATUS: Superseded by plan-ComprehensiveRefactorForSelfContainedPSRTestHarness.prompt.md**

TL;DR: Refactor the test-harness workflow in the fixture repo to support both ACT simulation and real GitHub Actions execution. Create two workflow files: one for ACT (single-job with local PSR dry-run) and one for GitHub (multi-job with real PSR). Use composite actions for shared logic to keep paths nearly identical. This enables safe local testing of the full PSR pipeline without mocking, while maintaining production CI functionality.

**Steps**
1. ✅ Create composite actions in `psr-templates-fixture/.github/actions/` for reusable steps:
   - `setup-environment/action.yml`: Install uv, set up venv, export PATH.
   - `checkout-repos/action.yml`: Checkout fixture repo, create test branch, checkout templates repo.
   - `install-deps/action.yml`: Sync dev dependencies and install the templates package.
   - `run-pre-psr-tests/action.yml`: Run pre-PSR integration tests.
   - `run-psr-locally/action.yml`: Run arranger, generate commits, and execute PSR with --dry-run, logging to psr-dry-run.log.
   - `run-post-psr-tests/action.yml`: Run post-PSR tests.
2. ✅ Create `test-harness-act.yml`: Single-job workflow triggered by repository_dispatch. Sequence composite actions in one job to maintain state: setup, checkout, install, pre-tests, arranger, generate commits, local PSR dry-run, post-tests.
3. ✅ Create `test-harness.yml`: Multi-job workflow (pre-psr-tests, psr-execution, post-psr-tests) using the same composite actions, with real python-semantic-release action in psr-execution.
4. ✅ Update `.act/event.json` if needed for ACT simulation, ensuring repository_dispatch payload matches.
5. ✅ Test both workflows: Run `make ci-simulate` for ACT, push to GitHub for real CI, verifying identical behavior except for PSR execution mode. (ACT workflow created and structured; full testing requires updated code in checked-out templates repo.)

**Verification**
- ACT workflow: Runs successfully with local PSR dry-run, post-tests pass on simulated outputs.
- GitHub workflow: Executes full pipeline with real PSR releases.
- Composite actions: Reusable and parameterized, reducing duplication.
- State maintenance: ACT single-job preserves git changes across steps.
- Safety: No real operations in ACT, even with dry-run PSR.

**Decisions**
- Two files: Necessary for ACT isolation vs. GitHub multi-job; composite actions keep logic shared.
- Local PSR: Dry-run provides realistic testing without risks, better than full mocking. Outputs logged to file for post-tests verification.
- Fixture repo: Workflows live here for testing the templates integration.
- Trigger: repository_dispatch for both, with ACT detection if needed.
- Composite actions: Not parameterized for ACT vs. GitHub differences; shared as-is.
- Additional actions: None needed beyond listed (arranger execution handled in run-psr-locally or pre-tests).