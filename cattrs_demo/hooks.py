from dataclasses import dataclass
from typing import Any, Dict, TypeVar, List, Tuple

import cattrs
import numpy as np

DT = TypeVar("DT")

converter = cattrs.Converter()


@dataclass
class NumpyArray:
    dims: Tuple[int, ...]
    data: List
    dtype: str

    @classmethod
    def from_ndarray(cls, arr: np.ndarray):
        return cls(arr.shape, arr.flatten().tolist(), str(arr.dtype))

    @property
    def to_ndarray(self) -> np.ndarray:
        return np.asarray(self.data).astype(self.dtype).reshape(self.dims)


def unstructure_numpy(arr: np.ndarray) -> Dict[str, Any]:
    return cattrs.unstructure(NumpyArray.from_ndarray(arr))


def structure_numpy(numpy_dict: Dict[str, Any], _) -> np.ndarray:
    return cattrs.structure(numpy_dict, NumpyArray).to_ndarray


converter.register_structure_hook(np.ndarray, structure_numpy)
converter.register_unstructure_hook(np.ndarray, unstructure_numpy)


def main():
    M = np.random.randn(10, 10).astype(np.float32)
    mu = cattrs.unstructure(M)
    M2 = cattrs.structure(mu, np.ndarray)
    print(np.array_equal(M, M2))


if __name__ == '__main__':
    main()
