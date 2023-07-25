for i in 1 2 3 4 5 6
do
    cat video.mp4 > /tmp/media
done
echo 'cat over'
mplayer /tmp/media -cache 30
