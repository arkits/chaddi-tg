class TestBasic:
    def test_basic_assertion(self):
        assert 1 + 1 == 2

    def test_string_concat(self):
        assert "hello" + " world" == "hello world"

    def test_list_operations(self):
        lst = [1, 2, 3]
        assert 2 in lst
        assert len(lst) == 3
