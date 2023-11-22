import gzip
import io
import os
import shutil
import subprocess as sp
from os.path import join
from pathlib import Path
from typing import Iterable


class LayerMaker:
    """
    Gets all modules in supplied site-packages-esque dir and output to new dir with layers each less than 50 MB
    E.g.,

    ```python
    LayerMaker(
        root_dir="/home/.../venv/lib/python3.11/site-packages/",
        output_dir="/home/.../layers/"
    ).make()
    ```

    This doesn't use a smart algorithm to find the optimal layer sizes.
    It just stuffs 'em in as its goes. If it doesn't fit, make sure to remove clutter from the
    venv or add files to exclude. If we need an optimal algorithm, we can write it.
    """

    def __init__(self, root_dir: str, output_dir: str, exclude: list | None = None):
        self.root_dir = root_dir.rstrip("/")
        self.output_dir = output_dir.rstrip("/")
        self._max_layer_size = 50_000_000
        self._total_layers = 0
        self._layer_size = 0
        self._dirs_in_layer: list[str] = []
        self._individual_modules: list[str] = []
        self._exclude: list[str] = ["boto", "urllib"]
        self._exclude.extend(exclude or [])

    def make(self) -> None:
        walker = os.walk(self.root_dir)
        site_packages = self.root_dir.split("/")[-1]
        for curr_root, _, files in walker:
            curr_root_parent = curr_root.split("/")[-1]
            if self._should_exclude(curr_root):
                continue
            if curr_root_parent == site_packages:
                # handle where this is a site-package level module file by squeezing in make_layer
                self._individual_modules.extend(
                    name for name in self._join_filenames(curr_root, files)
                )
                continue
            if self.root_dir.split("/")[-1] != curr_root.split("/")[-2]:
                # curr root is not a direct child of site-packages, will be handled by parent dir
                continue

            print(curr_root)
            dir_size = self._get_compressed_dir_size(curr_root)
            if self._is_layer_overflow(dir_size):
                self._make_layer()

            self._dirs_in_layer.append(curr_root)
            self._layer_size += dir_size
            print("curr layer size MB: ", self._layer_size / 1_000_000)

        # Make remaining layer
        self._make_layer()

        # Make sure valid finished state
        assert self._layer_size == 0
        assert not self._individual_modules
        assert not self._dirs_in_layer

    def _make_layer(self) -> None:
        can_squeeze = self._get_squeeze()
        self._layer_size = 0
        self._total_layers += 1
        assert self._total_layers <= 5, "Can't possibly fit these layers on lambda"
        print("creating layer with dirs: ", self._dirs_in_layer)
        zip_output_dir = self.output_dir + "/layer_%d/" % self._total_layers
        layer_files_dir = zip_output_dir + "python/"
        for dir in self._dirs_in_layer:
            shutil.copytree(dir, layer_files_dir + dir.split("/")[-1])
        for file in can_squeeze:
            shutil.copy(file, layer_files_dir + file.split("/")[-1])
        self._dirs_in_layer.clear()

        sp.run(
            f"python -m zipfile -c {zip_output_dir}layer.zip {layer_files_dir}",
            shell=True,
            check=True,
        )

    def _is_layer_overflow(self, additional_size: int) -> bool:
        assert additional_size <= self._max_layer_size, "Can't possibly fit these layers on lambda"
        return (self._layer_size + additional_size) >= self._max_layer_size

    def _get_squeeze(self) -> list[str]:
        can_squeeze = []
        cant_squeeze = []
        for file in self._individual_modules:
            file_size = self._get_compressed_file_size(file)
            if self._is_layer_overflow(file_size):
                cant_squeeze.append(file)
                continue
            can_squeeze.append(file)
            self._layer_size += file_size

        self._individual_modules = cant_squeeze
        return can_squeeze

    def _should_exclude(self, path: str) -> bool:
        for exclude in self._exclude:
            if exclude in path:
                return True
        return False

    def _get_compressed_dir_size(self, path: str) -> int:
        root_directory = Path(path)
        return sum(
            self._get_compressed_file_size(path)
            for path in root_directory.glob("**/*")
            if path.is_file()
        )

    @staticmethod
    def _join_filenames(root_dir: str, filenames: list[str]) -> Iterable[str]:
        return (join(root_dir, name) for name in filenames)

    @staticmethod
    def _get_compressed_file_size(path: Path | str):
        with open(path, "rb") as file:
            file_contents = file.read()

        with io.BytesIO() as bytes_io:
            with gzip.GzipFile(fileobj=bytes_io, mode="wb") as gzip_file:
                gzip_file.write(file_contents)

            compressed_data = bytes_io.getvalue()
            compressed_size = len(compressed_data)

        return compressed_size

