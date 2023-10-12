def test_step1(helper):
    for i in range(1,5):
        table = helper.show_table("db1", "sc1", f"cu001_tb{i}")
        assert table is not None


def test_step2(helper):
    for i in range(1,5):
        table = helper.show_table("db1", "sc1", f"cu001_tb{i}")
        view = helper.show_view("db1", "sc1", f"cu001_vw{i}")

        if i <= 3:
            assert table is not None
            assert view is not None
        else:
            assert table is None
            assert view is None


def test_step3(helper):
    for i in range(1,5):
        table = helper.show_table("db1", "sc1", f"cu001_tb{i}")
        view = helper.show_view("db1", "sc1", f"cu001_vw{i}")

        assert table is None
        assert view is None
