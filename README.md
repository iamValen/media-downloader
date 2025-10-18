# Media Downloader 🎵
A lightweight, web-based application for downloading and organizing media files.
Includes a modern frontend, Flask backend, and optional Docker support for easy deployment.

![img](assets/demo.png)

## Run Locally (without Docker)

```bash
git clone https://github.com/yourusername/media-downloader.git
cd media-
```

```bash
python3 -m venv venv
source venv/bin/activate     # on Linux / macOS
venv\Scripts\activate        # on Windows
```

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Configure download paths

By default, downloads are saved to:

Default Path: ~/Downloads/media_downloader
Alternative Path: ~/.cache/media_downloader

To customize these paths, you can set environment variables before running:

```bash
export DEFAULT_DOWNLOAD_PATH=/desired/path
export ALT_DOWNLOAD_PATH=/desired/path
```

(Windows PowerShell equivalent):
```shell
$env:DEFAULT_DOWNLOAD_PATH = "D:\desired\path"
$env:ALT_DOWNLOAD_PATH = "C:\desired\path"
```
python app.py

The server will start at http://localhost:5000

## Docker Deployment

### Quick Start
```bash
# Build the image
docker build -t media-downloader .

# Run the container
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/downloads:/app/downloads \
  -v $(pwd)/temp:/app/temp \
  --name media-downloader \
  media-downloader
```

### Using Docker Compose
```yaml
version: '3.8'

services:
  media-downloader:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./downloads:/app/downloads
      - ./temp:/app/temp
    restart: unless-stopped
```

Then run:
```bash
docker-compose up -d
```

### Environment Variables

- `NETWORK_DOWNLOAD_PATH`: Default download location (default: `/app/downloads`)
- `TEMP_DOWNLOAD_PATH`: Temporary files location (default: `/app/temp`)


# To-do
- [X] Handle better errors
- [ ] Remove the 2 save files options
- [ ] Frontend Warning to use only public/unlisted and explain that it creates folders: artist/album
- [ ] Login
- [ ] Log file
- [ ] Ditch links and make it search
- [ ] Recommend music based on input/profile