FROM ubuntu:latest

# avoid stuck build due to user prompt
ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install --no-install-recommends -y python3.12 python3.12-venv python3-pip && \
	apt-get clean && rm -rf /var/lib/apt/lists/*

# create and activate virtual environment using final folder name to avoid path issues with packages
RUN python3.12 -m venv /home/heartbeat/venv
ENV PATH="/home/heartbeat/venv/bin:$PATH"

# install requirements
COPY ./requirements.txt .
# RUN pip3 install --no-cache-dir wheel
RUN pip3 install --no-cache-dir -r requirements.txt

RUN useradd --create-home heartbeat
USER heartbeat
# RUN mkdir /home/heartbeat/code
WORKDIR /home/heartbeat
COPY . .

EXPOSE 8080

# make sure all messages always reach console
ENV PYTHONUNBUFFERED=1

# activate virtual environment
ENV VIRTUAL_ENV=/home/heartbeat/venv
ENV PATH="/home/heartbeat/venv/bin:$PATH"

CMD ["python", "src/app.py"]
