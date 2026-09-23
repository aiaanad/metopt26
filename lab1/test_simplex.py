import pytest

from simplex import (
    read_file,
    to_canon,
    calc_new_table,
    to_dop_canon,
    main_task,
    chose_re,
    print_solution,
)


def write_input(tmp_path, text: str) -> str:
    p = tmp_path / "input.txt"
    p.write_text(text, encoding="utf8")
    return str(p)


# ----------------------------- read_file -----------------------------

def test_read_file_valid(tmp_path):
    path = write_input(
        tmp_path,
        "max\n"
        "2\n"
        "1 2\n"
        "2\n"
        "1 1 <= 10\n"
        "2 1 >= 4\n"
    )

    n, c, m, data, task_type = read_file(path)

    assert n == 2
    assert c == ["1", "2"]
    assert m == 2
    assert data == ["1 1 <= 10\n", "2 1 >= 4\n"]
    assert task_type == "max"


def test_read_file_bad_c_count(tmp_path):
    path = write_input(
        tmp_path,
        "max\n"
        "3\n"
        "1 2\n"
        "1\n"
        "1 <= 1\n"
    )

    with pytest.raises(ValueError, match="недостаточно коэффициентов c"):
        read_file(path)


def test_read_file_bad_task_type(tmp_path):
    path = write_input(
        tmp_path,
        "maximum\n"
        "1\n"
        "1\n"
        "1\n"
        "1 <= 1\n"
    )

    with pytest.raises(ValueError, match="task_type"):
        read_file(path)


def test_read_file_bad_constraints_count(tmp_path):
    path = write_input(
        tmp_path,
        "max\n"
        "1\n"
        "1\n"
        "2\n"
        "1 <= 1\n"
    )

    with pytest.raises(ValueError, match="недостаточно строк ограничений"):
        read_file(path)


# ----------------------------- to_canon -----------------------------

def test_to_canon_max_le_ge():
    n = 2
    c = ["1", "2"]
    m = 2
    data = ["1 1 <= 10\n", "2 1 >= 4\n"]

    new_n, new_c, m_out, parsed = to_canon(n, c, m, data, "max")

    assert new_n == 4
    assert m_out == 2
    assert new_c == pytest.approx([-1.0, -2.0, 0.0, 0.0, 0.0, 0.0])

    assert parsed[0] == pytest.approx([1.0, 1.0, 1.0, 0.0, 10.0])
    assert parsed[1] == pytest.approx([2.0, 1.0, 0.0, -1.0, 4.0])
    assert parsed[2] == pytest.approx([0.0, 0.0, 0.0, 0.0, 0.0])


def test_to_canon_flips_negative_rhs():
    n = 2
    c = ["1", "2"]
    m = 1
    data = ["1 1 <= -5\n"]

    new_n, new_c, m_out, parsed = to_canon(n, c, m, data, "min")

    assert new_n == 3
    assert parsed[0] == pytest.approx([-1.0, -1.0, -1.0, 5.0])


def test_to_canon_min_keeps_c():
    new_n, new_c, m, parsed = to_canon(
        1, ["5"], 1, ["1 <= 3\n"], "min"
    )

    assert new_c[0] == 5.0


# ----------------------------- calc_new_table -----------------------------

def test_calc_new_table_standard_pivot():
    n = 2
    m = 2
    a = [
        [2.0, 1.0, 10.0],
        [1.0, 3.0, 15.0],
        [-1.0, -2.0, 0.0],
    ]

    new_a = calc_new_table(n, m, a, 0, 0, is_dop=False)

    expected = [
        [0.5, 0.5, 5.0],
        [-0.5, 2.5, 10.0],
        [0.5, -1.5, 5.0],
    ]

    assert len(new_a) == len(expected)
    for row_got, row_exp in zip(new_a, expected):
        assert row_got == pytest.approx(row_exp)


def test_calc_new_table_dop_pivot():
    n = 2
    m = 2
    a = [
        [2.0, 1.0, 10.0],
        [1.0, 3.0, 15.0],
        [-1.0, -2.0, 0.0],
    ]

    new_a = calc_new_table(n, m, a, 0, 0, is_dop=True)

    expected = [
        [0.0, 0.5, 5.0],
        [0.0, 2.5, 10.0],
        [0.0, -1.5, 5.0],
    ]

    assert len(new_a) == len(expected)
    for row_got, row_exp in zip(new_a, expected):
        assert row_got == pytest.approx(row_exp)


# ----------------------------- chose_re -----------------------------

def test_chose_re_optimal():
    a = [
        [1.0, 0.0, 5.0],
        [0.0, 1.0, 3.0],
        [0.0, 0.0, 8.0],
    ]

    assert chose_re(2, 2, a) == (-1, -1)


def test_chose_re_selects_column_and_row():
    a = [
        [1.0, 0.0, 5.0],
        [0.0, 1.0, 3.0],
        [-1.0, -2.0, 0.0],
    ]

    assert chose_re(2, 2, a) == (1, 1)


def test_chose_re_no_positive_row():
    a = [
        [-1.0, 0.0, 5.0],
        [0.0, 1.0, 3.0],
        [-1.0, 0.0, 0.0],
    ]

    assert chose_re(2, 2, a) == (-1, -1)


# ----------------------------- to_dop_canon -----------------------------

def test_to_dop_canon_simple(capsys):
    n = 1
    m = 1
    a = [
        [1.0, 4.0],
        [0.0, 0.0],
    ]

    n2, m2, a2, basis, free = to_dop_canon(n, m, a)

    assert n2 == 1
    assert m2 == 1

    expected = [
        [0.0, 4.0],
        [0.0, 0.0],
    ]
    assert len(a2) == len(expected)
    for row_got, row_exp in zip(a2, expected):
        assert row_got == pytest.approx(row_exp)

    assert basis == [0]
    assert free == [1]

    out = capsys.readouterr().out
    assert "dop task solved" in out


# ----------------------------- main_task -----------------------------

def test_main_task_already_optimal():
    n = 2
    m = 2
    c = [1.0, 1.0, 0.0, 0.0]
    a = [
        [1.0, 0.0, 5.0],
        [0.0, 1.0, 3.0],
        [0.0, 0.0, 0.0],
    ]
    basis = [2, 3]
    free = [0, 1]

    n2, m2, a2, basis2, free2 = main_task(n, c, m, a, basis, free)

    assert n2 == 2
    assert m2 == 2
    assert a2[-1] == pytest.approx([1.0, 1.0, 0.0])
    assert basis2 == [2, 3]
    assert free2 == [0, 1]


def test_main_task_one_pivot(capsys):
    n = 1
    m = 1
    c = [-1.0, 0.0]
    a = [
        [1.0, 4.0],
        [0.0, 0.0],
    ]
    basis = [1]
    free = [0]

    n2, m2, a2, basis2, free2 = main_task(n, c, m, a, basis, free)

    expected = [
        [1.0, 4.0],
        [1.0, 4.0],
    ]
    assert len(a2) == len(expected)
    for row_got, row_exp in zip(a2, expected):
        assert row_got == pytest.approx(row_exp)

    assert basis2 == [0]
    assert free2 == [1]

    out = capsys.readouterr().out
    assert "simplex is end" in out


# ----------------------------- print_solution -----------------------------

def test_print_solution_max(capsys):
    n_orig = 2
    c_orig = [1, 2]
    a = [
        [1.0, 0.0, 5.0],
        [0.0, 1.0, 3.0],
        [0.0, 0.0, 7.0],
    ]
    basis = [0, 1]

    print_solution(n_orig, c_orig, a, basis, "max")

    out = capsys.readouterr().out
    assert "Вектор x: [5.0, 3.0]" in out
    assert "Оптимальное значение F: 7.0" in out


def test_print_solution_min(capsys):
    n_orig = 1
    c_orig = [1]
    a = [
        [1.0, 2.0],
        [0.0, -2.0],
    ]
    basis = [0]

    print_solution(n_orig, c_orig, a, basis, "min")

    out = capsys.readouterr().out
    assert "Вектор x: [2.0]" in out
    assert "Оптимальное значение F: 2.0" in out


# ----------------------------- интеграционные тесты -----------------------------

def test_full_pipeline_max(tmp_path, capsys):
    path = write_input(
        tmp_path,
        "max\n"
        "2\n"
        "1 1\n"
        "2\n"
        "1 0 <= 4\n"
        "0 1 <= 5\n"
    )

    n, c, m, data, task_type = read_file(path)
    n_canon, c_canon, m, a = to_canon(n, c, m, data, task_type)
    n_canon, m, a, basis, free = to_dop_canon(n_canon, m, a)
    n_canon, m, a, basis, free = main_task(n_canon, c_canon, m, a, basis, free)

    print_solution(n, c, a, basis, task_type)

    out = capsys.readouterr().out
    assert "Вектор x: [4.0, 5.0]" in out
    assert "Оптимальное значение F: 9.0" in out


def test_full_pipeline_min(tmp_path, capsys):
    path = write_input(
        tmp_path,
        "min\n"
        "1\n"
        "1\n"
        "1\n"
        "1 >= 2\n"
    )

    n, c, m, data, task_type = read_file(path)
    n_canon, c_canon, m, a = to_canon(n, c, m, data, task_type)
    n_canon, m, a, basis, free = to_dop_canon(n_canon, m, a)
    n_canon, m, a, basis, free = main_task(n_canon, c_canon, m, a, basis, free)

    print_solution(n, c, a, basis, task_type)

    out = capsys.readouterr().out
    assert "Вектор x: [2.0]" in out
    assert "Оптимальное значение F: 2.0" in out