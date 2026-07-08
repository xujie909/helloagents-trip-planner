FROM node:20-bookworm-slim

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

RUN mkdir -p /data/output /data/audio /data/images

ENV VIDEO_MEDIA_ROOT=/data \
    VIDEO_OUTPUT_SUBDIR=output \
    VIDEO_AUDIO_SUBDIR=audio \
    VIDEO_IMAGE_SUBDIR=images

CMD ["sh", "-c", "echo 'video-generator runtime ready'; tail -f /dev/null"]
