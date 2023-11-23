import gzip
import io
import shutil
import subprocess as sp
from os.path import join
from pathlib import Path
from typing import Iterable, Tuple

import boto3
from mypy_boto3_lambda.type_defs import PublishLayerVersionResponseTypeDef


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

    Sorts the site-packages top-level files and dirs by compressed size, and then puts biggest files into layers first,
    putting files into the same layer until we know all files remaining can't fit, and moving onto next layer to do the same.
    """

    def __init__(self, root_dir: Path | str, output_dir: Path | str, exclude: list | None = None):
        if isinstance(root_dir, str):
            root_dir = Path(root_dir)
        if isinstance(output_dir, str):
            output_dir = Path(output_dir)

        assert root_dir.is_dir()
        assert output_dir.is_dir()
        output_dir.mkdir(exist_ok=True, parents=True)

        self.root_dir = root_dir
        self.output_dir = output_dir
        self.layer_paths: list[Path] = []
        self._max_layer_size = 50_000_000
        self._total_layers = 0
        self._layer_size = 0
        self._paths_in_layer: list[Path] = []
        self._exclude: list[str] = ["boto", "urllib"]
        self._exclude.extend(exclude or [])

    def publish(
        self, layer_name: str, description: str
    ) -> list[PublishLayerVersionResponseTypeDef]:
        client = boto3.client("lambda")

        responses = []
        for (i, p) in enumerate(self.layer_paths):
            with open(p, "rb") as f:
                zip_content = f.read()

            response = client.publish_layer_version(
                LayerName=layer_name.format(i), Description=description, Content={"ZipFile": zip_content}
            )
            responses.append(response)

        return responses

    def make(self) -> None:
        # get a list of sorted paths
        sorted_dir = self._get_size_sorted_dir(self.root_dir)
        while sorted_dir:
            unhandled = []
            for (p, size) in sorted_dir:

                # skip this file if it overflows
                if self._is_layer_overflow(size):
                    unhandled.append((p, size))
                    continue

                # we can add the file to the layer
                print("appending layer with size B: ", p, size)
                self._paths_in_layer.append(p)
                self._layer_size += size

            # we've gone through all the files that could possibly fit in the layer, so we make it
            self._make_layer()
            sorted_dir = unhandled

        # # Make sure valid finished state
        assert self._layer_size == 0
        assert not self._paths_in_layer

    def _make_layer(self) -> None:
        self._layer_size = 0
        self._total_layers += 1
        assert self._total_layers <= 5, "Can't possibly fit these layers on lambda"
        print("creating layer with dirs: ", self._paths_in_layer)
        print("layer size MB: ", self._layer_size / 1_000_000)
        zip_output_dir = self.output_dir.joinpath("layer_%d" % self._total_layers)
        layer_files_dir = zip_output_dir.joinpath("python")
        for p in self._paths_in_layer:
            dest = layer_files_dir.joinpath(p.name)
            dest.parent.mkdir(exist_ok=True, parents=True)
            if p.is_file():
                shutil.copy(p, dest)
            else:
                shutil.copytree(p, dest)

        self._paths_in_layer.clear()

        sp.run(
            f"python -m zipfile -c {zip_output_dir}/layer.zip {layer_files_dir}",
            shell=True,
            check=True,
        )
        self.layer_paths.append(zip_output_dir.joinpath("layer.zip"))

    def _is_layer_overflow(self, additional_size: int) -> bool:
        assert additional_size <= self._max_layer_size, "Can't possibly fit these layers on lambda"
        return (self._layer_size + additional_size) > self._max_layer_size

    def _should_exclude(self, path: Path) -> bool:
        for exclude in self._exclude:
            if exclude in str(path):
                return True
        return False

    def _get_size_sorted_dir(self, path: Path) -> list[Tuple[Path, int]]:
        assert path.is_dir()
        dir = list(path.iterdir())
        assert dir
        dir_with_size = []
        for p in dir:
            if self._should_exclude(p):
                continue
            dir_with_size.append((p, LayerMaker._get_compressed_size(p)))

        return sorted(dir_with_size, key=lambda p: p[1], reverse=True)

    @staticmethod
    def _join_filenames(root_dir: str, filenames: list[str]) -> Iterable[str]:
        return (join(root_dir, name) for name in filenames)

    @staticmethod
    def _get_compressed_size(path: Path) -> int:
        if path.is_file():
            return LayerMaker._get_compressed_file_size(path)
        else:
            return LayerMaker._get_compressed_dir_size(path)

    @staticmethod
    def _get_compressed_dir_size(path: Path) -> int:
        return sum(LayerMaker._get_compressed_size(p) for p in path.iterdir())

    @staticmethod
    def _get_compressed_file_size(path: Path | str) -> int:
        with open(path, "rb") as file:
            file_contents = file.read()

        with io.BytesIO() as bytes_io:
            with gzip.GzipFile(fileobj=bytes_io, mode="wb") as gzip_file:
                gzip_file.write(file_contents)

            return len(bytes_io.getvalue())
