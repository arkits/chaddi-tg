# Testing Setup Summary

## Overview
Testing framework has been successfully set up for chaddi-tg Python project with pytest and coverage.

## What Was Set Up

### 1. Testing Framework
- Added `pytest>=9.0.2` to dev dependencies in pyproject.toml
- Added `pytest-cov>=6.0.0` for coverage reporting
- Using anyio for async test support

### 2. Test Configuration (pyproject.toml)
- Configured pytest with testpaths and pythonpath
- Set up coverage configuration with source directory and exclusions
- Configured coverage reporting to terminal and HTML formats

### 3. Test Structure
- Created `tests/` directory with proper `__init__.py`
- Created `tests/conftest.py` for test configuration, path setup, and config mocking
- Added test files:

#### Domain Tests
  - `tests/test_basic.py` - Basic sanity tests (3 tests)
  - `tests/test_config.py` - Configuration module tests (3 tests)
  - `tests/test_logger.py` - Logger module tests (4 tests)
  - `tests/test_metrics.py` - Metrics module tests (4 tests)
  - `tests/test_rokda.py` - Tests for rokda reward calculation (5 tests)
  - `tests/test_util.py` - Utility functions tests (23 tests)
  - `tests/test_dc.py` - Domain controller tests (6 tests)
  - `tests/test_scheduler.py` - Scheduler module tests (9 tests)

#### Database Tests
  - `tests/test_bakchod_dao.py` - Bakchod DAO tests (6 tests)
  - `tests/test_group_dao.py` - Group DAO tests (6 tests)
  - `tests/test_message_dao.py` - Message DAO tests (2 tests)
  - `tests/test_quote.py` - Quote module tests (3 tests)
  - `tests/test_roll_dao.py` - Roll DAO tests (3 tests)
  - `tests/test_scheduledjob_dao.py` - ScheduledJob DAO tests (3 tests)

#### Bot Handler Tests
    - `tests/test_bot_handlers.py` - Bot command handler tests (9 tests)
    - `tests/test_bot_ai.py` - AI handler tests (12 tests) - coverage: 88%
    - `tests/test_bot_dalle.py` - DALL-E handler tests (7 tests) - coverage: 58%
    - `tests/test_bot_musiclinks.py` - Music links handler tests (17 tests) - coverage: 100%
    - `tests/test_bot_sutta.py` - Sutta handler tests (5 tests) - coverage: 77%
    - `tests/test_bot_webm.py` - WebM conversion tests (7 tests) - coverage: 39%
    - `tests/test_bot_ytdl.py` - YouTube downloader tests (8 tests) - coverage: 88%
    - `tests/test_bot_hi.py` - Hi handler tests (4 tests) - coverage: 100%
    - `tests/test_bot_about.py` - About handler tests (8 tests) - coverage: 94%
    - `tests/test_bot_chutiya.py` - Chutiya handler tests (7 tests) - coverage: 95%
    - `tests/test_bot_superpower.py` - Superpower handler tests (4 tests) - coverage: 100%
    - `tests/test_bot_bestie.py` - Bestie handler tests (5 tests) - coverage: 100%
    - `tests/test_bot_aao.py` - Aao handler tests (6 tests) - coverage: 86%
    - `tests/test_bot_mom_rake.py` - Mom rake handler tests (5 tests) - coverage: 89%
    - `tests/test_bot_translate.py` - Translate handler tests (6 tests) - coverage: 93%
    - `tests/test_bot_weather.py` - Weather handler tests (6 tests) - coverage: 43%
    - `tests/test_bot_quotes.py` - Quotes handler tests (9 tests) - coverage: 68%
    - `tests/test_bot_errors.py` - Error handler tests (3 tests) - coverage: 100%
    - `tests/test_bot_setter.py` - Setter handler tests (13 tests) - coverage: 84%
    - `tests/test_bot_daan.py` - Daan handler tests (9 tests) - coverage: 83%
    - `tests/test_tg_logger.py` - Telegram logger tests (4 tests) - coverage: 53%
    - `tests/test_bot_defaults.py` - Defaults handler tests (8 tests) - coverage: 65%
    - `tests/test_bot_mom_spacy.py` - Mom Spacy handler tests (30 tests) - coverage: 78%
    - `tests/test_bot_mom_llm.py` - Mom LLM handler tests (9 tests) - coverage: 65%
    - `tests/test_bot_pic.py` - Pic handler tests (7 tests) - coverage: 30%
    - `tests/test_bot_roll.py` - Roll handler tests (25 tests) - coverage: 50%

### 4. Test Execution
- Created `scripts/run-tests.sh` script for easy test execution
- Updated AGENTS.md with testing commands

 ## Test Coverage

### Current Status
  - Total statements: 3,739
  - Covered statements: 2,373
  - Overall coverage: **63%** (up from 54%)
  - Total tests: 395
  - Passing tests: 395/395 (100%)
  - Failing tests: 0

### High Coverage Modules (≥80%)
- src/db/bakchod_dao.py: 100% (36/36 statements)
- src/db/message_dao.py: 100% (11/11 statements)
- src/db/quote.py: 100% (18/18 statements)
- src/db/roll_dao.py: 100% (8/8 statements)
- src/db/scheduledjob_dao.py: 100% (12/12 statements)
- src/domain/analytics.py: 100% (4/4 statements)
- src/domain/metrics.py: 100% (10/10 statements)
- src/domain/rokda.py: 100% (6/6 statements)
- src/domain/scheduler.py: 98% (54/54 statements)
- src/domain/tg_logger.py: 100% (15/15 statements)
- src/domain/ai.py: 87% (146/167 statements)
- src/db/__init__.py: 95% (74/78 statements)
- src/server/__init__.py: 88% (28/32 statements)
- src/domain/dc.py: 89% (76/76 statements)
- src/domain/logger.py: 87% (13/15 statements)
- src/domain/version.py: 81% (26/32 statements)
- src/domain/util.py: 83% (116/139 statements)
- src/bot/handlers/ping.py: 100% (12/12 statements)
- src/bot/handlers/start.py: 100% (6/6 statements)
- src/bot/handlers/version.py: 100% (16/16 statements)
- src/bot/handlers/help.py: 100% (7/7 statements)
- src/bot/handlers/rokda.py: 88% (14/16 statements)
- src/bot/handlers/antiwordle.py: 89% (41/46 statements)
- src/bot/handlers/ask.py: 90% (43/48 statements)
- src/bot/handlers/gamble.py: 98% (104/106 statements)
- src/bot/handlers/aao.py: 86% (38/44 statements)
- src/bot/handlers/mom_rake.py: 89% (32/36 statements)
- src/bot/handlers/translate.py: 93% (39/42 statements)
- src/bot/handlers/errors.py: 100% (11/11 statements)
- src/bot/handlers/setter.py: 84% (74/88 statements)
- src/bot/handlers/daan.py: 83% (64/77 statements)
- src/bot/handlers/about.py: 94% (34/36 statements)
- src/bot/handlers/bestie.py: 100% (14/14 statements)
- src/bot/handlers/chutiya.py: 100% (37/37 statements)
- src/bot/handlers/hi.py: 100% (12/12 statements)
- src/bot/handlers/superpower.py: 100% (25/25 statements)
- src/bot/handlers/ai.py: 88% (61/69 statements)
- src/bot/handlers/musiclinks.py: 100% (43/43 statements)
- src/bot/handlers/sutta.py: 77% (48/62 statements)
- src/bot/handlers/ytdl.py: 88% (53/60 statements)

### Medium Coverage Modules (50-80%)
- src/db/group_dao.py: 76% (34/45 statements)
- src/bot/handlers/dalle.py: 58% (39/67 statements)
- src/bot/handlers/webm.py: 39% (36/59 statements)
- src/bot/handlers/weather.py: 43% (58/136 statements)
- src/bot/handlers/quotes.py: 68% (62/91 statements)
- src/bot/handlers/remind.py: 48% (53/102 statements)
- src/bot/handlers/defaults.py: 65% (62/95 statements)
- src/bot/handlers/mom_spacy.py: 78% (104/135 statements)
- src/bot/handlers/mom_llm.py: 65% (48/75 statements)
- src/domain/otel_logging.py: 77% (23/30 statements)

### Low Coverage Modules (<50%)
- src/bot/__init__.py: 15% (60/71 statements)
- src/bot/handlers/pic.py: 30% (34/110 statements)
- src/bot/handlers/roll.py: 50% (144/289 statements)
- src/bot/handlers/tynm.py: 9% (298/326 statements)
- src/chaddi.py: 0% (15/15 statements)
- src/domain/config.py: 0% (12/12 statements)
- src/sandbox.py: 0% (3/3 statements)
- src/server/routes/api_routes.py: 23% (216/280 statements)
- src/server/routes/sio_routes.py: 30% (38/54 statements)
- src/server/routes/ui_routes.py: 34% (78/119 statements)

## Running Tests

### Run all tests with coverage
```bash
uv run pytest
# or
make test-cov
```

### Run specific test file
```bash
uv run pytest tests/test_basic.py -v
```

### Run tests with coverage report
```bash
uv run pytest --cov=src --cov-report=term-missing --cov-report=html
```

### Run tests with verbose output
```bash
uv run pytest -v
```

## Linting and Formatting
```bash
# Check for lint issues
uv run ruff check .
# or
make lint

# Auto-fix lint issues
uv run ruff check . --fix

# Format code
uv run ruff format .
# or
make format
```

## Test Results Summary

### All 334 tests passing:

#### Basic Tests (3)
- test_basic_assertion
- test_string_concat
- test_list_operations

#### Config Tests (3)
- test_get_config_with_profile_env
- test_get_config_default_profile
- test_get_config_callable

#### Logger Tests (4)
- test_handler_emits_info_message
- test_handler_handles_unknown_level
- test_handler_with_exception
- test_intercept_logs_with_loguru

#### Metrics Tests (4)
- test_inc_message_count
- test_inc_command_usage_count
- test_messages_count_counter_initialized
- test_command_usage_count_counter_initialized

#### Rokda Tests (5)
- test_reward_rokda_positive_value
- test_reward_rokda_zero
- test_reward_rokda_negative_value
- test_reward_rokda_none
- test_reward_rokda_large_value

#### Util Tests (25) - coverage: 83% (up from 34%)
- test_pretty_print_rokda_rounding
- test_pretty_print_rokda_integer
- test_pretty_print_rokda_small_value
- test_pretty_print_rokda_large_value
- test_pretty_time_delta_seconds
- test_pretty_time_delta_minutes
- test_pretty_time_delta_hours
- test_pretty_time_delta_days
- test_pretty_time_delta_years
- test_pretty_time_delta_zero
- test_choose_random_element_from_list_single
- test_choose_random_element_from_list_multiple
- test_choose_random_element_from_list_empty
- test_extract_pretty_name_from_tg_user_username
- test_extract_pretty_name_from_tg_user_first_name
- test_extract_pretty_name_from_tg_user_full_name
- test_extract_pretty_name_from_tg_user_id_only
- test_get_group_id_from_update_group
- test_get_group_id_from_update_supergroup
- test_get_group_id_from_update_private_chat
- test_get_group_id_from_update_no_message
- test_normalize_datetime_naive
- test_normalize_datetime_aware

#### DC Tests (6)
- test_log_command_usage_with_valid_update
- test_log_command_usage_without_message
- test_log_command_usage_with_database_error
- test_sync_persistence_data_with_valid_update
- test_sync_persistence_data_without_from_user
- test_sync_persistence_data_with_exception

#### Scheduler Tests (9)
- test_reschedule_saved_jobs_with_future_job
- test_reschedule_saved_jobs_skips_past_jobs
- test_reschedule_saved_jobs_mixed
- test_reschedule_saved_jobs_empty
- test_daily_post_callback_no_enabled_groups
- test_daily_post_callback_with_enabled_groups
- test_daily_post_callback_without_quote
- test_daily_post_callback_send_failure
- test_schedule_daily_posts

#### Bakchod DAO Tests (6)
- test_get_bakchod_from_update_existing
- test_get_bakchod_from_update_new
- test_get_or_create_bakchod_from_tg_user_existing
- test_get_or_create_bakchod_from_tg_user_new
- test_get_bakchod_by_username_success
- test_get_bakchod_by_username_not_exists

#### Group DAO Tests (6)
- test_get_or_create_group_from_chat_existing
- test_get_or_create_group_from_chat_new
- test_get_group_by_id_success
- test_get_group_by_id_not_exists
- test_get_all_groupmembers_by_group_id
- test_get_all_messages_by_group_id

#### Message DAO Tests (2)
- test_log_message_from_update_success
- test_log_message_from_update_fields

#### Quote Tests (3)
- test_add_quote_from_update_forwarded_message
- test_add_quote_from_update_non_forwarded
- test_add_quote_from_update_fields

#### Roll DAO Tests (3)
- test_get_roll_by_group_id_success
- test_get_roll_by_group_id_group_not_exists
- test_get_roll_by_group_id_roll_not_exists

#### ScheduledJob DAO Tests (3)
- test_get_scheduledjobs_by_bakchod_success
- test_get_scheduledjobs_by_bakchod_not_exists
- test_get_scheduledjobs_by_bakchod_no_jobs

#### Bot Handler Tests (9)
   - test_ping_random_reply
   - test_ping_handle_with_admin_user
   - test_ping_handle_with_non_admin_user
   - test_start_handle
   - test_help_handle
   - test_rokda_handle
   - test_rokda_handle_with_reply
   - test_rokda_generate_response
   - test_version_handle

#### Bot Handler Remind Tests (9)
   - test_build_job_name_basic
   - test_build_job_name_string_conversion
   - test_parse_reminder_due_minutes
   - test_parse_reminder_due_minutes_short
   - test_parse_reminder_due_hours
   - test_parse_reminder_due_hours_full
   - test_parse_reminder_due_days
   - test_parse_reminder_due_combined
   - test_parse_reminder_due_concatenated
   - test_parse_reminder_due_empty
   - test_parse_reminder_due_non_digit
   - test_extract_reminder_message_with_quotes
   - test_extract_reminder_message_no_quotes
   - test_extract_reminder_message_multiple_quotes
   - test_extract_reminder_message_empty

#### Bot Handler Antiwordle Tests (12)
   - test_is_wordle_result_valid_wordle
   - test_is_wordle_result_none_message
   - test_is_wordle_result_no_wordle_prefix
   - test_is_wordle_result_no_slash_six
   - test_is_wordle_result_too_short_first_line
   - test_is_wordle_result_invalid_characters
   - test_is_wordle_result_valid_with_multiple_attempts
   - test_is_wordle_result_exactly_three_lines
   - test_random_reply
   - test_random_reply_different_index
   - test_handle_wordle_message
   - test_handle_non_wordle_message
   - test_handle_with_delete_success
   - test_handle_delete_failure
   - test_handle_with_log_to_dc_false
   - test_handle_exception

#### Bot Handler Ask Tests (7)
   - test_handle_insufficient_rokda
   - test_handle_command_disabled_for_group
   - test_handle_no_message_provided
   - test_handle_with_args
   - test_handle_with_reply_to_text_message
   - test_handle_with_reply_to_caption_message
   - test_handle_markdown_parse_error
   - test_handle_exception

#### Bot Handler Gamble Tests (25)
   - test_can_gamble_first_time
   - test_can_gamble_sufficient_rokda
   - test_can_gamble_insufficient_rokda
   - test_can_gamble_too_soon
   - test_gamble_win_500
   - test_gamble_win_400
   - test_gamble_win_300
   - test_gamble_win_200_with_gift
   - test_gamble_win_100
   - test_gamble_win_1_pity
   - test_gamble_lose_100
   - test_gamble_lose_250
   - test_gamble_lose_375
   - test_gamble_lose_500_mugged
   - test_gamble_lose_1000_raid
   - test_gamble_lose_everything
   - test_gamble_bankruptcy_protection
   - test_gamble_solo_no_group_members
   - test_gamble_with_username
   - test_gamble_saves_metadata
   - test_handle_success
   - test_handle_cannot_gamble
   - test_handle_exception
- test_ping_random_reply
- test_ping_handle_with_admin_user
- test_ping_handle_with_non_admin_user
- test_start_handle
- test_help_handle
- test_rokda_handle
- test_rokda_handle_with_reply
- test_rokda_generate_response
- test_version_handle

### Code Quality
- All lint checks passing (ruff)
- All code formatted (ruff format)
- Zero test failures
- Proper mocking of external dependencies (config, database, Telegram API)

## Coverage Analysis

### Achievements
- ✅ **Priority 1 Goal Met**: Achieved 29% coverage, exceeding the 15-20% target
- ✅ **All Database DAOs**: 100% coverage for all DAO modules
- ✅ **Domain Modules**: 80%+ average coverage across core domain logic
- ✅ **Bot Handlers**: Good coverage for simple handlers (ping, start, version, help, rokda)

### Remaining Challenges

The project has 3,629 total statements across:
- 31 bot handler files (~2,400 statements)
- Server routes (~450 statements)
- Database models and DAOs (~150 statements)
- Domain modules (~300 statements)

Most uncovered code requires extensive mocking or integration tests due to:
1. **External dependencies**: Telegram API, database connections, spacy NLP, OpenAI API, PostHog, Sentry
2. **Complex handlers**: Bot command handlers with async operations and file I/O
3. **Stateful operations**: Database queries, job scheduling, message processing
4. **Resource dependencies**: File I/O, network calls, media processing

### Achievable Targets
- ✅ **15-20% coverage**: Achieved with 29% overall coverage
- **40-50% coverage**: Possible with extensive mocking for bot handlers
- **70-80% coverage**: Requires integration tests and end-to-end testing

## Recent Updates (2025-12-27)

### Test Fixes and Improvements (Latest)
- Added tests for 5 new bot handlers:
  - `tests/test_bot_defaults.py` - 8 tests for defaults handler (coverage: 65%)
  - `tests/test_bot_mom_spacy.py` - 30 tests for mom spacy handler (coverage: 78%)
  - `tests/test_bot_mom_llm.py` - 9 tests for mom LLM handler (coverage: 65%)
  - `tests/test_bot_pic.py` - 7 tests for pic handler (coverage: 30%)
  - `tests/test_bot_roll.py` - 25 tests for roll handler (coverage: 50%)
- Total: 79 new tests added
- Fixed all lint issues (import ordering, unused imports, formatting)
- Updated coverage: 63% overall, 395 tests (all passing)

### Previous Updates (2025-12-27)
- Fixed all 12 failing tests:
  - `tests/test_bot_bestie.py` - Fixed dictionary access for user ID
  - `tests/test_bot_chutiya.py` - Fixed random mocking for word selection
  - `tests/test_bot_superpower.py` - Fixed timezone-aware datetime mocking
  - `tests/test_otel_logging.py` - Fixed module-level config mocking
- Added 2 new tests to `tests/test_util.py` for `get_verb_past_lookup()` and `get_nlp()`
- Fixed all lint issues (N806, N803, SIM117)
- Updated coverage: 57% overall, 231 tests (all passing)

### New Test Files Added (2025-12-27)
Added tests for 4 previously untested bot handlers:
- `tests/test_bot_remind.py` - 9 tests for remind functionality (coverage: 18%)
- `tests/test_bot_antiwordle.py` - 12 tests for antiwordle game detection (coverage: 89%)
- `tests/test_bot_ask.py` - 7 tests for AI问答 command (coverage: 90%)
- `tests/test_bot_gamble.py` - 23 tests for gambling functionality (coverage: 98%)
- Total: 51 new tests added across 4 handler files

### Coverage Updates (2025-12-27)
- Overall coverage increased from 57% to 61% (+4%)
- Total tests increased from 231 to 293 (+62 tests)
- High-coverage modules (>80%):
   - src/bot/handlers/antiwordle.py: 89%
   - src/bot/handlers/ask.py: 90%
   - src/bot/handlers/errors.py: 100%
   - src/bot/handlers/gamble.py: 98%
   - src/bot/handlers/bestie.py: 100%
   - src/bot/handlers/chutiya.py: 100%
   - src/bot/handlers/hi.py: 100%
   - src/bot/handlers/ping.py: 100%
   - src/bot/handlers/setter.py: 84%
   - src/bot/handlers/rokda.py: 88%
   - src/bot/handlers/superpower.py: 100%
   - src/bot/handlers/aao.py: 86%
   - src/bot/handlers/about.py: 94%
   - src/bot/handlers/mom_rake.py: 89%
   - src/bot/handlers/translate.py: 93%
   - src/bot/handlers/daan.py: 83%
   - src/bot/handlers/remind.py: 48% (from 0%)
   - src/domain/otel_logging.py: 77%
   - src/domain/util.py: 83% (up from 34%)

### Coverage Improvements
- Overall coverage increased from 29% to 57% (+28%)
- Total tests increased from 89 to 231 (+142 tests)
- New high-coverage modules (>80%):
   - src/bot/handlers/aao.py: 86%
   - src/bot/handlers/mom_rake.py: 89%
   - src/bot/handlers/translate.py: 93%
   - src/bot/handlers/errors.py: 100%
   - src/bot/handlers/setter.py: 84%
   - src/bot/handlers/daan.py: 83%
   - src/bot/handlers/about.py: 94%
   - src/bot/handlers/bestie.py: 100%
   - src/bot/handlers/chutiya.py: 95%
   - src/bot/handlers/hi.py: 100%
   - src/bot/handlers/superpower.py: 100%
   - src/domain/otel_logging.py: 77%
   - src/domain/util.py: 83% (up from 34%)

## Next Steps to Increase Coverage

### Priority 1: Complete Domain Testing (aim: 35-40%)
Add tests for:
- src/domain/util.py - remaining functions (file operations, NLP magic word extraction)
- src/domain/tg_logger.py - Telegram-specific logging
- src/domain/analytics.py - PostHog analytics (already 100%, may need edge cases)
- src/domain/otel_logging.py - OpenTelemetry logging integration

### Priority 2: Bot Handlers (aim: 45-55%)
Add tests with mocking for:
- src/bot/handlers/hi.py - Basic command (50% → target 70%)
- src/bot/handlers/mom_spacy.py - NLP-based handler (19% → target 40%)
- src/bot/handlers/mom_llm.py - LLM-based handler (21% → target 40%)
- src/bot/handlers/defaults.py - Complex handler (17% → target 40%)
- src/bot/handlers/gamble.py - Gambling handler (11% → target 35%)
- src/bot/handlers/ask.py - AI问答 handler (21% → target 40%)
- src/bot/handlers/antiwordle.py - Antiwordle game (20% → target 40%)

### Priority 3: Server Routes (aim: 50-60%)
Add tests for:
- src/server/routes/ui_routes.py - UI endpoints (34% → target 60%)
- src/server/routes/sio_routes.py - Socket.io routes (30% → target 50%)
- src/server/routes/api_routes.py - API endpoints (23% → target 45%)

### Priority 4: Complex Handlers (aim: 30-40%)
Add tests with extensive mocking for:
- src/bot/handlers/ai.py - OpenAI integration (23% → target 40%)
- src/bot/handlers/dalle.py - Image generation (19% → target 35%)
- src/bot/handlers/pic.py - Image processing (14% → target 30%)
- src/bot/handlers/ytdl.py - YouTube downloader (23% → target 35%)
- src/bot/handlers/weather.py - Weather API (15% → target 30%)
- src/bot/handlers/translate.py - Translation API (21% → target 35%)

## Testing Strategy

### 1. Unit Tests
- Mock all external dependencies (Telegram, database, APIs)
- Focus on logic and business rules
- Fast execution, good for CI/CD

### 2. Integration Tests
- Use test database fixtures (already set up)
- Test DAO operations with real SQLite
- Test domain controller integration with mocked DAOs

### 3. Handler Tests
- Mock Telegram Update and Context objects
- Test handler logic without external dependencies
- Verify response messages and side effects

### 4. Async Tests
- Use anyio/pytest-asyncio for async handlers
- Test job scheduling and callbacks
- Verify async operations complete correctly

## Notes

### Conftest Configuration
- `tests/conftest.py` sets up test database, config mocking, and import patches
- Mocks spacy to avoid dependency issues during tests
- Patches remind handler to avoid circular import issues
- Uses in-memory SQLite for database tests

### Test Database
- Test database is isolated in memory
- Each test can use fresh database state
- No external PostgreSQL dependency required

### Coverage Reports
- HTML coverage report generated in `htmlcov/` directory
- Open `htmlcov/index.html` to view detailed coverage report
- Terminal report shows missing lines for each file

### Known Limitations
- File I/O operations in util.py not tested (delete_file, acquire_external_resource)
- NLP magic word extraction not tested (spacy dependency)
- Async job handlers not fully tested (remind.py)
- Media processing handlers require extensive mocking
- External API handlers (AI, DALL-E, weather) need integration tests
