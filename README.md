# AWS Lambda Python Layer Maker

![Static Badge](https://img.shields.io/badge/python-3.11-blue?logo=python)

This tool solves the problem of python lambda's that have dependencies that don't easily fit into one layer. It sorts the site-packages top-level files and dirs by compressed size, and then puts biggest files into layers first, putting files into the same layer until we know all files remaining can't fit, and moving onto next layer to do the same.

Run the code on the lambda architecture you're targeting in case there are compiled dependencies.


```python
lm = LayerMaker(
    root_dir="/home/.../venv/lib/python3.11/site-packages/",
    output_dir="/home/.../layers/"
)
lm.make()
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

Publish the layers like so using a format string for the name:

```python
lm.publish(layer_name="layer-number-{}", description="some description")
```

This would publish layer-number-1, layer-number-2, ..., upto layer-number-5. 
