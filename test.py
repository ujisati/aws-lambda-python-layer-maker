import random
import os
import shutil
from pathlib import Path
from typing import Iterable
from layer_maker import LayerMaker

import pytest

def write_file(root: Path, filename: str | int, size: int):
    path = root.joinpath(str(filename))
    path.parent.mkdir(exist_ok=True)

    with open(path, "wb") as f:
        f.write(os.urandom(size))

@pytest.fixture
def layer_maker() -> Iterable[LayerMaker]:
    root = Path("test/site-packages/")
    output = Path("test/layers/")
    root.mkdir(exist_ok=True, parents=True)
    output.mkdir(exist_ok=True)
    lm = LayerMaker(root, output)
    lm._max_layer_size = 1023
    yield lm
    if root.parent.exists():
        shutil.rmtree(root.parent)


@pytest.fixture
def directory() -> Iterable[Path]:
    root = Path("./test/site-packages")


    dir_1 = root.joinpath("dir_biggest")
    write_file(dir_1, f"file_biggest", 1000)

    dir_2 = root.joinpath("dir_2")
    write_file(dir_2, 1, 800)

    write_file(root, 5, 700)

    dir_3 = root.joinpath("dir_3")
    write_file(dir_3, 2, 600)

    dir_4 = root.joinpath("dir_4")
    write_file(dir_4, 3, 400)

    write_file(root, 4, 400)
    write_file(root, f"file_smallest", 200)

    yield root
    if root.parent.exists():
        shutil.rmtree(root.parent)


def test_layer_maker(layer_maker: LayerMaker, directory: Path):
    layer_maker.make()
    assert Path("test/layers/layer_1/python/dir_biggest/file_biggest").exists()
    assert Path("test/layers/layer_2/python/dir_2/1").exists()
    assert Path("test/layers/layer_3/python/5").exists()
    assert Path("test/layers/layer_3/python/file_smallest").exists()
    assert Path("test/layers/layer_4/python/dir_3/2").exists()
    assert Path("test/layers/layer_5/python/dir_4/3").exists()
    assert Path("test/layers/layer_5/python/4").exists()
    assert Path("test/layers/layer_1/layer.zip").exists()
    assert Path("test/layers/layer_2/layer.zip").exists()
    assert Path("test/layers/layer_3/layer.zip").exists()
    assert Path("test/layers/layer_4/layer.zip").exists()
    assert Path("test/layers/layer_5/layer.zip").exists()

    
def test_get_size_sorted_dir(layer_maker: LayerMaker, directory: Path):
    sorted_dir = layer_maker._get_size_sorted_dir(directory)
    assert "dir_biggest" in sorted_dir[0][0].name
    assert "file_smallest" in sorted_dir[-1][0].name


