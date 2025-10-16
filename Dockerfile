FROM python:3.11-slim-bookworm

WORKDIR /python-docker

COPY requirements.txt requirements.txt
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

# Install FFmpeg and other dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    ca-certificates \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Verify FFmpeg is installed
RUN ffmpeg -version && ffprobe -version

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]