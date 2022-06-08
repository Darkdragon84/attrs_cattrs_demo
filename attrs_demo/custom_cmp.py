import collections.abc as abc
from typing import TypeVar, Callable, Sequence, Mapping, get_origin, get_args, List, Optional, Union, Dict
from functools import partial

import attr
import cattrs
import numpy as np
from attr import define, Attribute

T = TypeVar("T")
KT = TypeVar("KT")

EqFunType = Callable[[T, T], bool]

SPECIAL_EQ_TYPES = {
    np.ndarray: partial(np.array_equal, equal_nan=False)
}


def eq(a: T, b: T) -> bool:
    return a == b


def noneable_eq(eq_fun: EqFunType = eq) -> Callable[[Optional[T], Optional[T]], bool]:
    def new_eq_fun(a: Optional[T], b: Optional[T]) -> bool:
        return True if a is None and b is None else eq_fun(a, b)

    return new_eq_fun


def sequence_eq(eq_fun: EqFunType = eq) -> Callable[[Sequence[T], Sequence[T]], bool]:
    def new_eq_fun(c1: Sequence[T], c2: Sequence[T]) -> bool:
        if not isinstance(c1, Sequence):
            raise TypeError(f"c1 ({type(c1)}, '{c1}') is not a Sequence.")
        if not isinstance(c2, Sequence):
            raise TypeError(f"c2 ({type(c2)}, '{c2}') is not a Sequence.")
        return len(c1) == len(c2) and all(eq_fun(v1, v2) for v1, v2 in zip(c1, c2))

    return new_eq_fun


def mapping_eq(eq_fun: EqFunType = eq) -> Callable[[Mapping[KT, T], Mapping[KT, T]], bool]:
    def new_eq_fun(m1: Mapping[KT, T], m2: Mapping[KT, T]) -> bool:
        if not isinstance(m1, Mapping):
            raise TypeError(f"m1 ({type(m1)}, '{m1}') is not a Mapping.")
        if not isinstance(m2, Mapping):
            raise TypeError(f"m2 ({type(m2)}, '{m2}') is not a Mapping.")
        return m1.keys() == m2.keys() and all(eq_fun(v1, m2.get(k1)) for k1, v1 in m1.items())

    return new_eq_fun


def get_sequence_type(c):
    origin = get_origin(c)
    args = get_args(c)
    if origin is not None and issubclass(origin, abc.Sequence):
        assert len(args) == 1, "args of Sequence must be of length 1."
        return args[0]
    return None


def get_mapping_types(c):
    origin = get_origin(c)
    args = get_args(c)
    if origin is not None and issubclass(origin, abc.Mapping) and len(args) == 2:
        assert len(args) == 2, "args of Mapping must be of length 1."
        return args
    return None, None


def get_optional_type(c):
    origin = get_origin(c)
    args = get_args(c)
    if origin is Union and args[1] is type(None):
        return args[0]
    return None


def get_special_eq_fun(tp):
    funs = get_eq_funs(tp, [])
    if not funs:
        return None
    funs = reversed(funs)
    total_fun = next(funs)
    for fun in funs:
        total_fun = fun(total_fun)
    return total_fun


def get_eq_funs(tp, funs: List[Callable[[EqFunType], EqFunType]]) -> List[Callable[[EqFunType], EqFunType]]:
    if tp is None:
        return []

    opt_tp = get_optional_type(tp)
    if opt_tp is not None:
        funs.append(noneable_eq)
        tp = opt_tp

    special_eq_fun = SPECIAL_EQ_TYPES.get(tp)
    if special_eq_fun is not None:
        funs.append(special_eq_fun)
        return funs

    new_tp = get_sequence_type(tp)
    if new_tp is not None:
        funs.append(sequence_eq)
        return get_eq_funs(new_tp, funs)

    _, new_tp = get_mapping_types(tp)
    if new_tp is not None:
        funs.append(mapping_eq)
        return get_eq_funs(new_tp, funs)


def endow_fields_with_special_eq(_: type, fields: List[Attribute]) -> List[Attribute]:
    new_fields = []
    for field in fields:
        special_eq_fun = get_special_eq_fun(field.type)
        if special_eq_fun is not None:
            special_cmp = attr.cmp_using(  # type: ignore
                eq=special_eq_fun, class_name=str(field.type), require_same_type=True
            )
            field = field.evolve(eq=special_cmp, eq_key=special_cmp)
        new_fields.append(field)

    return new_fields


smart_eq = define(field_transformer=endow_fields_with_special_eq)


@smart_eq
class ComplexObject:
    name: str
    score: float
    lst: List[np.ndarray]
    dct: Dict[str, np.ndarray]


def main():
    mats = [np.random.randn(2, 2) for _ in range(3)]
    obj1 = ComplexObject(
        "a",
        2.2,
        mats,
        {str(i): mat for i, mat in enumerate(mats)}
    )
    obj2 = ComplexObject(
        "a",
        2.2,
        mats,
        {str(i): mat for i, mat in enumerate(mats)}
    )
    print(obj1 == obj2)
    obj2.lst = list(reversed(obj2.lst))
    print(obj1 == obj2)


if __name__ == '__main__':
    main()
