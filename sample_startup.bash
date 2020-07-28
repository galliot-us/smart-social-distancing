#!/bin/bash
config="$1"

# check if video file exists, if not download it
line=$(cat $config | grep VideoPath)
videoPath="$(cut -d'=' -f2 <<<"$line")"
if [ ! -f "$videoPath" ]; then
    echo "video file at $videoPath not exists, downloading..."
    sh '/repo/download_sample_video.sh'
fi

# start process video
echo "running curl 0.0.0.0:8000/process-video-cfg "
while true
do
    response=$(curl 0.0.0.0:8000/process-video-cfg)
    if [ "$response" != true ] ; then
        echo "curl failed, trying again in 5 seconds!"
        sleep 5
    elif [ "$response" = true ] ; then
     	echo "ok video is going to be processed"
        break
    fi  
done
