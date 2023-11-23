# AWS Lambda Python Layer Maker

![Static Badge](https://img.shields.io/badge/python-3.11-blue?logo=python)

This is a little script I wrote to make my job easier.

It sorts the site-packages top-level files and dirs by compressed size, and then puts biggest files into layers first, putting files into the same layer until we know all files remaining can't fit, and moving onto next layer to do the same.

Run the code on the lambda architecture you're targeting in case there are compiled dependencies.


```python
LayerMaker(
    root_dir="/home/.../venv/lib/python3.11/site-packages/",
    output_dir="/home/.../layers/"
).make()
```

The output should look like this:

```
layers/
  layer_1/
    layer.zip
    python/
  layer_2/
    layer.zip
    python/
  .../
  layer_5/
    layer.zip
    python/
```
