import time
import datetime

try:
    from tqdm import tqdm
except ImportError:
    tqdm = list

from csv2json import headers2template, json2csv_headers

# samples (default options)


def test_basic():
    headers = "abc.0,abc.1,status,item1.subitem1".split(",")
    assert headers2template(headers).render_as_dict([1, 2, 3, 0]) == {
        "abc": [1, 2],
        "item1": {"subitem1": 0},
        "status": 3,
    }


def test_basic_list_with_dict():
    headers = "abc.0.def,abc.1,status".split(",")
    assert headers2template(headers).render_as_dict([3, 1, 2]) == {
        "abc": [{"def": 3}, 1],
        "status": 2,
    }


def test_basic_non_uniform_list():
    headers = "abc.10,abc.1,status".split(",")
    assert headers2template(headers).render_as_dict([3, 1, 2]) == {
        "abc": [None, 1, None, None, None, None, None, None, None, None, 3],
        "status": 2,
    }


def test_basic_sub_list_with_dict():
    headers = "abc.5.3.def,abc.1,status".split(",")
    assert headers2template(headers).render_as_dict([3, 1, 2]) == {
        "abc": [None, 1, None, None, None, [None, None, None, {"def": 3}]],
        "status": 2,
    }


def test_basic_types_conservation():
    headers = "abc.5.3.def,abc.1,status,foo.bar".split(",")
    assert headers2template(headers).render_as_dict(
        ["3", "1", datetime.datetime(2019, 11, 1), True]
    ) == {
        "abc": [None, "1", None, None, None, [None, None, None, {"def": "3"}]],
        "status": datetime.datetime(2019, 11, 1),
        "foo": {"bar": True},
    }


def test_basic_perf():
    headers = "abc.5.3.def,abc.1,status,foo.bar".split(",")
    n = 1_000_000
    start = time.time()
    t = headers2template(headers)
    for _ in tqdm(range(n)):
        t.render_as_dict(["3", "1", datetime.datetime(2019, 11, 1), True])
    print(f"completed {n} basic resolution in {time.time() - start}")


# sample with options


def test_with_options_types():
    headers = "abc.3,status".split(",")
    options = {
        "abc.3": {"infer_type": True},  # prio 1
        "status": {"render": datetime.datetime.fromisoformat},  # prio 4
    }
    assert headers2template(headers, options=options).render_as_dict(
        ["1", "2019-02-01T01:01:01"]
    ) == {
        "abc": [None, None, None, 1],
        "status": datetime.datetime(2019, 2, 1, 1, 1, 1),
    }


def test_with_options_on_value():
    headers = "abc.0,abc.3,status,item1.subitem1,foo".split(",")
    options = {
        "abc.3": {"infer_type": True},
        "abc": {"fill_value": 0},
        "status": {"render": datetime.datetime.fromisoformat},
        "foo": {"optional": len},
    }
    assert headers2template(headers, options=options).render_as_dict(
        ["1", "2", "2019-02-01T01:01:01", "0", ""]
    ) == {
        "abc": ["1", 0, 0, 2],
        "item1": {"subitem1": "0"},
        "status": datetime.datetime(2019, 2, 1, 1, 1, 1),
    }


def test_with_options_perf():
    n = 1_000_000
    headers = "abc.0,abc.3,status,item1.subitem1,foo".split(",")
    options = {
        "abc.3": {"infer_type": True},
        "abc": {"fill_value": 0},
        "status": {"render": datetime.datetime.fromisoformat},
        "foo": {"optional": len},
    }
    start = time.time()
    t = headers2template(headers, options=options)
    for _ in tqdm(range(n)):
        t.render_as_dict(["1", "2", "2019-02-01T01:01:01", "0", ""])
    print(f"completed {n} complex resolution in {time.time() - start}")


def test_optional_multi_level():
    headers = "abc.0,foo.0,foo.1".split(",")
    options = {
        "abc.0": {"optional": len},
        "foo": {"optional": len},
        "foo.0": {"optional": len},
        "foo.1": {"optional": len},
    }
    assert headers2template(headers, options=options).render_as_dict(["", "", ""]) == {
        "abc": []
    }


# test json to csv


def test_empty_json_2_csv():
    assert json2csv_headers("{}") == ([], [])
    assert json2csv_headers({}) == ([], [])


def test_json_with_null_2_csv():
    assert json2csv_headers('{"a": "true","b": null}') == (["a", "b"], ["true", None])
    assert json2csv_headers({"a": "true", "b": None}) == (["a", "b"], ["true", None])


def test_json_2_csv():
    assert json2csv_headers('{"a": "true","b": [1, {"f": 2}, 234]}') == (
        ["a", "b.0", "b.1.f", "b.2"],
        ["true", 1, 2, 234],
    )
