import csv
import sys
import json
import argparse

from typing import List, Dict, Any, Optional, AnyStr, Union
from dataclasses import dataclass
from collections import defaultdict
from collections.abc import Iterable, Callable


default_options = {}
nested_dict = lambda: defaultdict(nested_dict)
drop_entry = object()


class DictTranscoder:
    def __init__(self, resolve_values=True):
        self.resolve_values = resolve_values

    def on_leaf(self, e, path):
        if isinstance(e, TemplateValue) and self.resolve_values:
            e = e.v
        return e

    def on_collection(self, e, path):
        if type(e) is dict and all(k.isdigit() for k in e.keys()):
            l = [self.get_collection_fill_value(path)] * (
                max(int(k) for k in e.keys()) + 1
            )
            for k, v in e.items():
                if v is not drop_entry:
                    l[int(k)] = v
            return l
        return e

    def get_collection_fill_value(self, path):
        return None


def infer_type(o: str) -> Any:
    if o.isdigit():
        return int(o)
    if o.lower() == "true":
        return True
    if o.lower() == "false":
        return False
    if "," in o:
        return o.split(",")
    return o


class DictOptionsTranscoder(DictTranscoder):
    def __init__(self, options):
        super().__init__()
        self.options = options

    def on_leaf(self, e, path):
        e = super().on_leaf(e, path)

        o = self.options.get(".".join(path), None)
        if not o:
            return e
        if o.get("infer_type") is True:
            e = infer_type(e)
        if "render" in o:
            e = o["render"](e)
        if "optional" in o and not o["optional"](e):
            return drop_entry
        return e

    def on_collection(self, e, path):
        e = super().on_collection(e, path)

        o = self.options.get(".".join(path), None)
        if not o:
            return e
        if "optional" in o and not o["optional"](e):
            return drop_entry
        return e

    def get_collection_fill_value(self, path):
        o = self.options.get(".".join(path), None)
        return o and o.get("fill_value", None)


def dict_transformer(
    indict: Any,
    path: Optional[List[AnyStr]] = None,
    *,
    transcoder: Optional[DictTranscoder] = None,
) -> Any:
    if path is None:
        path = []
    if transcoder is None:
        transcoder = DictTranscoder()
    if not isinstance(indict, Iterable) or isinstance(indict, (str, bytearray, bytes)):
        return transcoder.on_leaf(indict, path)

    if isinstance(indict, dict):
        d = {}
        for key, v in indict.items():
            v = dict_transformer(v, path + [key], transcoder=transcoder)
            if v is not drop_entry:
                d[key] = v
        return transcoder.on_collection(d, path)

    it = []
    for i, e in enumerate(indict):
        v = dict_transformer(e, path + [str(i)], transcoder=transcoder)
        if v is not drop_entry:
            it.append(v)
    return transcoder.on_collection(it, path)  # if on_collection else it


class TemplateTree:
    def __init__(self):
        self._d = nested_dict()
        self._dict_cache = None

    def set_value(self, path: str, value: Any) -> None:
        self._dict_cache = None
        parts = path.split(".")
        branch = self._d
        for part in parts[:-1]:
            branch = branch[part]
        branch[parts[-1]] = value
        return value

    def render_as_dict(self, options: Optional[Dict] = None) -> Dict:
        if not self._dict_cache:
            _tr = DictTranscoder
            if options:

                class _tr(DictTranscoder):
                    def get_collection_fill_value(self, path):
                        o = options.get(".".join(path), None)
                        return o and o.get("fill_value", None)

            self._dict_cache = dict_transformer(self._d, transcoder=_tr(resolve_values=False))
        return dict_transformer(self._dict_cache, transcoder=DictTranscoder())


@dataclass
class TemplateValue:
    v: Optional[Any] = None

    def __eq__(self, o):
        return (self.v == (o.v if isinstance(o, TemplateValue) else o)) or self.v == o

    def __str__(self):
        return str(self.v)


@dataclass
class Template:
    tree: TemplateTree
    placeholders: List
    options: Optional[Dict[AnyStr, Any]] = None

    def render_as_dict(self, values: List) -> dict:
        assert len(values) == len(self.placeholders)
        for i, v in enumerate(values):
            self.placeholders[i].v = v
        base = self.tree.render_as_dict(options=self.options)
        if self.options:
            return dict_transformer(
                base, transcoder=DictOptionsTranscoder(self.options)
            )
        return base

    @classmethod
    def from_headers(cls, headers, options=None) -> "Template":
        tree = TemplateTree()
        values = [
            tree.set_value(header, TemplateValue(i)) for i, header in enumerate(headers)
        ]
        return cls(tree, values, options=options)


headers2template = Template.from_headers


def csv2json(input_stream, *, headers=None, options=None) -> List[Dict]:
    reader = csv.reader(input_stream)
    if not options:
        options = {}
    if not headers:
        headers = next(reader, None)
        if not headers:
            raise ValueError("input doesn't contain headers")

    template = headers2template(headers, options={**default_options, **options})
    for values in reader:
        r = template.render_as_dict(values)
        yield r


class Dict2CsvTranscoder(DictTranscoder):
    def __init__(self):
        super().__init__()
        self.headers = []
        self.values = []

    def on_leaf(self, e, path):
        self.headers.append(".".join(path))
        self.values.append(e)
        return e

    def on_collection(self, e, path):
        if len(e) == 0:
            # todo: should we do something with empty collections?
            # self.headers.append(".".join(path + ["0"]))
            # self.values.append()
            pass
        return e


def json2csv_headers(instr: Union[AnyStr, dict]) -> List[List[Any]]:
    body = json.loads(instr) if isinstance(instr, (str, bytearray, bytes)) else instr
    t = Dict2CsvTranscoder()
    dict_transformer(body, transcoder=t)
    return t.headers, t.values


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=argparse.FileType("r"))
    parser.add_argument("-i", "--indent", action="store_true", default=False)
    parser.add_argument("-r", "--reverse", action="store_true", default=False)
    args = parser.parse_args(argv)

    with args.input_file as f:
        if args.reverse:
            headers, values = json2csv_headers(f.read())
            print(f"headers: {','.join(headers)}")
            print(f"values: {','.join(map(str, values))}")
        else:
            for l in csv2json(f):
                print(json.dumps(l, indent=4 if args.indent else None), end="\n\n")
