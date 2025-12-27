from src.bot.handlers import remind


class TestBuildJobName:
    def test_build_job_name_basic(self):
        result = remind.build_job_name("123456", "789", 1)
        assert "123456" in result and "789" in result and "1" in result

    def test_build_job_name_string_conversion(self):
        result = remind.build_job_name(123456, 789, 1)
        assert "123456" in result and "789" in result and "1" in result


class TestParseReminderDue:
    def test_parse_reminder_due_minutes(self):
        result = remind.parse_reminder_due(["5", "m"])
        assert result == 300

    def test_parse_reminder_due_minutes_short(self):
        result = remind.parse_reminder_due(["5", "min"])
        assert result == 300

    def test_parse_reminder_due_hours(self):
        result = remind.parse_reminder_due(["2", "h"])
        assert result == 7200

    def test_parse_reminder_due_hours_full(self):
        result = remind.parse_reminder_due(["2", "hours"])
        assert result == 7200

    def test_parse_reminder_due_days(self):
        result = remind.parse_reminder_due(["1", "d"])
        assert result == 216000

    def test_parse_reminder_due_combined(self):
        result = remind.parse_reminder_due(["1", "h", "30", "m"])
        assert result == 5400

    def test_parse_reminder_due_concatenated(self):
        result = remind.parse_reminder_due(["5m"])
        assert result == 300

    def test_parse_reminder_due_empty(self):
        result = remind.parse_reminder_due([])
        assert result == 0

    def test_parse_reminder_due_non_digit(self):
        result = remind.parse_reminder_due(["test"])
        assert result == 0


class TestExtractReminderMessage:
    def test_extract_reminder_message_with_quotes(self):
        message = '/remind 5m "test message"'
        result = remind.extract_reminder_message(message)
        assert result == "test message"

    def test_extract_reminder_message_no_quotes(self):
        message = "/remind 5m test"
        result = remind.extract_reminder_message(message)
        assert result == ""

    def test_extract_reminder_message_multiple_quotes(self):
        message = '/remind 5m "first" "second"'
        result = remind.extract_reminder_message(message)
        assert result == "first second"

    def test_extract_reminder_message_empty(self):
        message = ""
        result = remind.extract_reminder_message(message)
        assert result == ""
