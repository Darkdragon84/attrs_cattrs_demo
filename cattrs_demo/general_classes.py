from typing import Any, Dict

import numpy as np

from numpy_hooks import converter

ANNOTATIONS = "__annotations__"


class CoordinateBoxV2:
    def __init__(self, xmin: float, ymin: float, xmax: float, ymax: float):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax
        self.coords = np.asarray([xmin, ymin, xmax, ymax])
        self.repres = repr(self)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(xmin={self.xmin}, ymin={self.ymin}, xmax={self.xmax}, ymax={self.ymax})"

    def __eq__(self, other: "CoordinateBoxV2"):
        if self.__class__ != other.__class__:
            return False
        self_vars = vars(self)
        other_vars = vars(other)
        if not np.array_equal(self_vars.pop("coords"), other_vars.pop("coords")):
            return False
        return self_vars == other_vars


def unstructure_coordinate_box_v2(my_class: CoordinateBoxV2) -> Dict[str, Any]:
    # We need to generate the type annotations from a live object.
    # This is very crude and could be done much more thorough but this is not the point here
    data_dict = {
        ANNOTATIONS: {name: type(value) for name, value in vars(my_class).items()},
        **converter.unstructure(vars(my_class))
    }
    return data_dict


def structure_coordinate_box_v2(data_dict: Dict[str, Any], _) -> CoordinateBoxV2:
    # fetch annotations
    annotations = data_dict.pop(ANNOTATIONS)
    # structure each variable separately based on exported annotations
    obj_vars = {name: converter.structure(value, annotations[name]) for name, value in data_dict.items()}
    obj = CoordinateBoxV2.__new__(CoordinateBoxV2)
    obj.__dict__.update(obj_vars)
    return obj


converter.register_unstructure_hook(CoordinateBoxV2, unstructure_coordinate_box_v2)
converter.register_structure_hook(CoordinateBoxV2, structure_coordinate_box_v2)


def main():
    coord_box1 = CoordinateBoxV2(2.2, 10.4, 5.3, 12.1)
    data_dict = converter.unstructure(coord_box1)
    print(data_dict)
    coord_box2 = converter.structure(data_dict, CoordinateBoxV2)
    print(coord_box1)
    print(coord_box2)
    print(coord_box1 == coord_box2)


if __name__ == '__main__':
    main()
