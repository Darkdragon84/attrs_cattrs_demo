from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import cattrs


@dataclass
class A:
    name: str
    value: float
    valid: bool


@dataclass
class B:
    idx: int
    data: List[float]


@dataclass
class C:
    alist: List[A]
    bdict: Dict[str, B]

    @classmethod
    def from_dict(cls, cdict: Dict[str, Any]):
        """
        This is unhandy and inflexible
        """
        return cls(
            alist=[A(**adict) for adict in cdict["alist"]],
            bdict={key: B(**bdict) for key, bdict in cdict["bdict"].items()}
        )


def main():
    c1 = C(
        [A("a", 2.2, True),
         A("b", 6.9, False),
         A("c", 4.2, True)],
        {"a": B(1, [1.1, 2.2, 3.3]),
         "b": B(2, [4.5, 6.7])}
    )
    print(c1)

    # only with dataclass
    cdict1 = asdict(c1)
    c2 = C.from_dict(cdict1)
    print(c1 == c2)

    # with cattrs <3
    cdict2 = cattrs.unstructure(c1)
    c3 = cattrs.structure(cdict2, C)
    print(c1 == c3)

    # cattrs will complain about missing "valid" in alist[0]
    cdict2["alist"][0].pop("valid")
    cattrs.structure(cdict2, C)


if __name__ == '__main__':
    main()
