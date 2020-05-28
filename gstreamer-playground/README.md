`cd gstreamer-playground` and run the following commands:

```bash
export PUBLIC_HOST=http://localhost
export PUBLIC_PORT=8080
docker run --rm --name nginx-static -v $PWD/nginx.conf:/etc/nginx/conf.d/default.conf:ro -v $PWD/static:/srv:ro -p $PUBLIC_PORT:80 -d nginx
echo "Open $PUBLIC_HOST:$PUBLIC_PORT in browser"
find "static/live" | grep -v .keep | rm -f && gst-launch-1.0 videotestsrc ! videoconvert ! x264enc speed-preset=ultrafast ! hlssink max-files=5 playlist-root=$PUBLIC_HOST:$PUBLIC_PORT/live/ location=$PWD/static/live/video_%05d.ts playlist-location=$PWD/static/live/playlist.m3u8
```
