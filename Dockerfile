FROM public.ecr.aws/lambda/python:3.10

ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_DEFAULT_REGION
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}

RUN yum install git -y
RUN python -m pip install nox
COPY . /home/app
WORKDIR /home/app
RUN python -m venv venv
RUN git clone https://github.com/ujisati/aws-lambda-python-layer-maker 
WORKDIR aws-lambda-python-layer-maker
RUN pip install -r requirements.txt
RUN python layer_maker.py --root /home/app/venv/lambda/lib/python3.10/site-packages/ --output ./layers/ --exclude pycache pytest coverage --publish --name lambda-layer-

ENTRYPOINT ["/bin/bash"]

