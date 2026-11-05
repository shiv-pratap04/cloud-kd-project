import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "service"), str(ROOT / "worker")]
from validation import validate, extract_json_line
from clean import clean
from worker import shard_lines

GOOD = '{"intent": "weather_query", "date": null, "time": null, "place": "london"}'

def rec(i, text, raw): return {"id": i, "text": text, "teacher_raw": raw}

def test_validate_accepts_good_and_rejects_bad():
    assert validate(GOOD)["place"] == "london"
    assert validate("not json") is None
    assert validate('{"intent": "nope", "date": null, "time": null, "place": null}') is None
    assert validate('{"intent": "alarm_set", "date": 5, "time": null, "place": null}') is None
    assert validate('{"intent": "alarm_set"}') is None

def test_extract_first_line():
    assert extract_json_line("\n " + GOOD + "\nCommand: x") == GOOD

def test_clean_reasons_and_accounting():
    cmd = "what is the weather in london"
    rows = [
        rec("C1", cmd, GOOD),
        rec("C2", "x", "garbage"),                                       # a
        rec("C3", "x", '{"intent": "alarm_set"}'),                       # b
        rec("C4", "x", '{"intent": "zzz", "date": null, "time": null, "place": null}'),  # c
        rec("C5", "set alarm", '{"intent": "alarm_set", "date": "monday", "time": null, "place": null}'),  # d
        rec("C0", cmd, GOOD),                                            # duplicate of C1, smaller id wins
    ]
    kept, c = clean(rows)
    assert [r["id"] for r in kept] == ["C0"]
    assert (c["a"], c["b"], c["c"], c["d"], c["duplicates"], c["kept"]) == (1, 1, 1, 1, 1, 1)

def test_sharding_partitions_exactly():
    lines = [str(i) for i in range(10)]
    parts = [shard_lines(lines, i, 3) for i in range(3)]
    ids = sorted(n for p in parts for n, _ in p)
    assert ids == list(range(10))
    assert [n for n, _ in parts[1]] == [1, 4, 7]
