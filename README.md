[![PyPI version](https://badge.fury.io/py/nx-csv2json.svg)](https://badge.fury.io/py/nx-csv2json)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# CSV 2 JSON

Library to convert an CSV into python dict.
The CSV headers are used as path to location in the target dict.

## Path expression

The path is separated with dots (.) to express list indexes and dict keys.
If all the sub keys of a collections are made of digits, the collections is assumed to be a list.
Otherwise it's a dict.

Note: List indices don't have to be contiguous or ordered.

Sample:

``` csv
"a.0,a.5,a.3"
```

will translate into:

``` json
{
    "a": [None, None, None, None, None]
}
```

But,

``` csv
"a.0,a.5,a.3,a.b"
```

will translate into:

``` json
{
    "a": {
        "0": None,
        "5": None,
        "3": None,
        "b": None,
    }
}
```

Note: list may contain sub-lists and sub-dicts at any level

## Options

By default the input type is preserved. (meaning there is no type conversion by default)
Several options, may be used to alter the output:

### fill_value

Indicate which value can be used to populate empty indices in the list.

Sample:

``` python
options = {
    "abc": {"fill_value": "?"}
}
headers = "abc.3,abc.1"
```

will produce the minimal output:

```json
{
    "abc": ["?", "?", "?", "?"]
}
```

### infer_type

Indicates the transcoder to try to figure out the type of the data and to cast it.

Sample:

``` python
options = {
    "abc": {"infer_type": True},
    "ghi": {"infer_type": True},
}
headers = "abc,def,ghi"
data = ["1", "2", "g,h,i"]
```

will produce the output:

```json
{
    "abc": 1,
    "def": "2",
    "ghi": ["g", "h", "i"]
}
```

#### Supported types:

* int
* bool
* array

### render

A callable which return the output used instead of the original input value.

Sample:

``` python
options = {
    "abc": {"render": lambda _, _: "?"}
}
headers = "abc,def"
data = ["1", "2"]
```

will produce the output:

```json
{
    "abc": "?",
    "def": "2"
}
```

### optional

Refer a callable to figure out if the entry should be removed from the output or not.

Sample:

``` python
options = {
    "abc": {"optional": len}
}
headers = "abc,def"
data = ["", ""]
```

will produce the output:

```json
{
    "def": ""
}
```

#### multi-level

This may affect the output structure on several levels.

Sample:
``` python
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
# "foo" does not appear in the output because of 3 factors:
# - all its sub-items are optional
# - all its sub-items are dropped
# - it is also optional
```

## JSON to headers

The function `json2csv_headers` may be used to evaluate what *could* be the headers of a CSV input based on a JSON.
This function only get a JSON string and returns a list of headers and a list of values extracted from the JSON string.

Sample

``` python
json2csv_headers('{"a": "true","b": null}') == (["a", "b"], ["true", None])
```

## CLI

### csv2json

The package provide an handy CLI command to turn CSV inputs to JSON outputs, just type `csv2json -h`

### json2csv

Use the flag '-r' for the command `csv2json` to extrapolate from a JSON, what the headers might be.

Sample

``` bash
echo '{"a": 1, "b": ["toto", {"test": "bar"}, 1, 3]}' | csv2json -r -
headers: a,b.0,b.1.test,b.2,b.3
values: 1,toto,bar,1,3
```
