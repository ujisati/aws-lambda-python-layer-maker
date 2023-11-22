# AWS Lambda Python Layer Maker

This is a little script I wrote to make my job easier. Use it or don't.

It will basically just naively stuff files into layer dirs (up to 5 since that is the limit) and ensure they are all less than 50 MB compressed.
Run the code on the lambda architecture you're targeting in case there are compiled dependencies.


```python
LayerMaker(
    root_dir="/home/.../venv/lib/python3.11/site-packages/",
    output_dir="/home/.../layers/"
).make()
```

The output should look like this:

layers/
  layer_1/
    layer.zip/
    .../
  layer_2/
    layer.zip/
    .../
  .../
  layer_5/
    layer.zip/
    .../
