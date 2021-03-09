#!/bin/bash
config="$1"

# check if video file exists, if not download it
line=$(cat $config | grep VideoPath)
videoPath="$(cut -d'=' -f2 <<<"$line" | xargs)"
if [ ! -f "$videoPath" ] && [ "$videoPath" = "/repo/data/softbio_vid.mp4" ]; then
    echo "video file at $videoPath not exists, downloading..."
    sh '/repo/download_sample_video.sh'
fi

# start process video
echo "running curl 0.0.0.0:8000/start-process-video "
while true
do  
    if sslEnabled=$(cat $config | grep -i "SSLEnabled = " | grep -i "true\|yes\|1"); then
        url=https://0.0.0.0:8000/start-process-video
    else
        url=0.0.0.0:8000/start-process-video
    fi
    # TODO: Remove the -k flag using the certificate already created
    response=$(curl -X PUT -k $url)
    if [ "$response" != true ] ; then
        echo "curl failed, trying again in 5 seconds!"
        sleep 5
    elif [ "$response" = true ] ; then
     	echo "ok video is going to be processed"
        break
    fi  
done
