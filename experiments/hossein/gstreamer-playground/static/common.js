if (window.location.search == '?third-party') {
    window.video_url = 'https://bitdash-a.akamaihd.net/content/MI201109210084_1/m3u8s-fmp4/f08e80da-bf1d-4e3d-8899-f0f6155f6efa.m3u8'
} else if (window.location.search == '?local') {
    window.video_url = window.location.origin + "/live/playlist.m3u8"
} else {
    window.video_url = window.location.search.slice(1); // remove "?" mark
}
