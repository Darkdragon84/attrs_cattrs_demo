from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any, TypeVar

import cattrs

ScalarType = TypeVar("ScalarType", int, float)


# THIS IS NOT A DATACLASS
class CoordinateBox:
    def __init__(self, xmin, ymin, xmax, ymax):
        self.xmin = xmin
        self.ymin = ymin
        self.xmax = xmax
        self.ymax = ymax

    @property
    def coordinates(self):
        return self.xmin, self.ymin, self.xmax, self.ymax

    def __repr__(self):
        return f"{self.__class__.__name__}{self.coordinates}"

    def __eq__(self, other: "CoordinateBox"):
        return self.__class__ == other.__class__ and self.coordinates == other.coordinates


@dataclass
class TableDetection:
    location: CoordinateBox
    confidence_score: float

    # NOW WE NEED THIS TOO BC CoordinateBox IS NOT A DATACLASS
    def to_dict(self) -> Dict[str, Any]:
        data_dict = asdict(self)
        data_dict["location"] = list(self.location.coordinates)
        return data_dict

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]):
        data_dict = data_dict.copy()
        data_dict["location"] = CoordinateBox(*data_dict["location"])
        return cls(**data_dict)


@dataclass
class TableInfo:
    coordinates: CoordinateBox
    caption: Optional[str]
    caption_extraction_confidence: Optional[float]
    extra_caption: Optional[List[str]]
    header: Optional[Dict[str, str]]
    footer: Optional[List[str]]
    label: Optional[Dict[str, str]]
    data: List[List[str]]
    table_extraction_confidence: Optional[float]

    # it trickles down, anything containing a CoordinateBox now needs a to_dict
    def to_dict(self) -> Dict[str, Any]:
        data_dict = asdict(self)
        data_dict["coordinates"] = list(self.coordinates.coordinates)
        return data_dict

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]):
        data_dict = data_dict.copy()
        data_dict["coordinates"] = CoordinateBox(*data_dict["coordinates"])
        return cls(**data_dict)


@dataclass
class PageInfo:
    table_locations: List[TableDetection]
    table_data: List[TableInfo]

    # and further up the hierarchy, boilerplate galore!
    def to_dict(self) -> Dict[str, Any]:
        return {
            "table_locations": [td.to_dict() for td in self.table_locations],
            "table_data": [ti.to_dict() for ti in self.table_data]
        }

    @classmethod
    def from_dict(cls, data_dict: Dict[str, Any]):
        return cls(
            table_locations=[TableDetection.from_dict(d) for d in data_dict["table_locations"]],
            table_data=[TableInfo.from_dict(d) for d in data_dict["table_data"]]
        )


def unstructure_coordinates(coord_box: CoordinateBox) -> List[ScalarType]:
    return list(coord_box.coordinates)


def structure_coordinates(coordinates: List[ScalarType], _) -> CoordinateBox:
    return CoordinateBox(*coordinates)


converter = cattrs.Converter()
converter.register_unstructure_hook(CoordinateBox, unstructure_coordinates)
converter.register_structure_hook(CoordinateBox, structure_coordinates)


def main():
    coords1 = CoordinateBox(1, 2, 3, 4)
    coords2 = CoordinateBox(5.1, 6.2, 7.44, 8.989)
    page_info = PageInfo(
        table_locations=[TableDetection(coords1, 0.9), TableDetection(coords2, 0.85)],
        table_data=[
            TableInfo(
                coordinates=coords1, caption="table 1", caption_extraction_confidence=1., extra_caption=None,
                header={"0": "A", "1": "B"}, footer=None, label={"0": "IE 1", "1": "IE 2"},
                data=[["1", "2"], ["2", "3"]], table_extraction_confidence=0.7
            ),
            TableInfo(
                coordinates=coords2, caption="table 2", caption_extraction_confidence=0.5, extra_caption=["table 3"],
                header={"0": "A"}, footer=["data without warranty"], label={"0": "CS 1"},
                data=[["1", "2"]], table_extraction_confidence=0.9
            )
        ]
    )
    print(page_info)

    # using only dataclass
    pi_dict1 = page_info.to_dict()
    page_info2 = PageInfo.from_dict(pi_dict1)
    print(page_info == page_info2)

    # using cattrs: no to/from_dict needed, but we needed to register two small hooks
    pi_dict2 = converter.unstructure(page_info)
    page_info3 = converter.structure(pi_dict2, PageInfo)
    print(page_info == page_info3)


if __name__ == '__main__':
    main()
