"""Tests for OptionsBase serialization mixin."""
from pyvis.types.base import OptionsBase
from dataclasses import dataclass
from typing import Optional, Union, List


@dataclass
class Inner(OptionsBase):
    x: Optional[int] = None
    y: Optional[int] = None


@dataclass
class Outer(OptionsBase):
    name: Optional[str] = None
    inner: Optional[Inner] = None
    flag: Optional[bool] = None


def test_to_dict_strips_none():
    obj = Outer(name="hello")
    result = obj.to_dict()
    assert result == {"name": "hello"}
    assert "inner" not in result
    assert "flag" not in result


def test_to_dict_nested():
    obj = Outer(name="hello", inner=Inner(x=10))
    result = obj.to_dict()
    assert result == {"name": "hello", "inner": {"x": 10}}


def test_to_dict_all_none():
    obj = Outer()
    result = obj.to_dict()
    assert result == {}


def test_to_dict_preserves_false():
    obj = Outer(flag=False)
    result = obj.to_dict()
    assert result == {"flag": False}


def test_to_dict_preserves_zero():
    @dataclass
    class Nums(OptionsBase):
        val: Optional[int] = None

    obj = Nums(val=0)
    assert obj.to_dict() == {"val": 0}


def test_to_dict_list_of_options():
    @dataclass
    class Container(OptionsBase):
        items: Optional[list] = None

    obj = Container(items=[Inner(x=1), Inner(y=2)])
    result = obj.to_dict()
    assert result == {"items": [{"x": 1}, {"y": 2}]}


def test_to_dict_union_str():
    """Union[str, Inner] — when str is provided, pass through."""
    @dataclass
    class Mixed(OptionsBase):
        color: Optional[Union[str, Inner]] = None

    assert Mixed(color="red").to_dict() == {"color": "red"}
    assert Mixed(color=Inner(x=5)).to_dict() == {"color": {"x": 5}}


def test_to_dict_dict_values():
    @dataclass
    class Groups(OptionsBase):
        data: Optional[dict] = None

    obj = Groups(data={"a": Inner(x=1), "b": "plain"})
    result = obj.to_dict()
    assert result == {"data": {"a": {"x": 1}, "b": "plain"}}
