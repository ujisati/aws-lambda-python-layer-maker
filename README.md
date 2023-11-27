# AWS Lambda Python Layer Maker

![Static Badge](https://img.shields.io/badge/python-3.11-blue?logo=python)

This tool solves the problem of python lambda functions that have dependencies that don't easily fit into one layer. It sorts the site-packages top-level files and dirs by compressed size, and then puts biggest files into layers first, putting files into the same layer until we know all files remaining can't fit, and moving onto next layer to do the same.

Run the code on the lambda architecture you're targeting in case there are compiled dependencies. There is an example Dockerfile for how you might do this: 

```shell
docker build -t lambda -f Dockerfile \
  --build-arg AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key) \
  --build-arg AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id) \
  --build-arg AWS_DEFAULT_REGION=us-west-2 .
```

Run like so:

```shell
python3.11 layer_maker.py --root /home/.../lib/python3.10/site-packages/ --output ./layers/ --exclude pycache pytest --publish --name some-layer-
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

The layer name will have the layer number appended to it, so "layer-number-" will publish as

layer-number-1, layer-number-2, ..., upto layer-number-5. 
