"""
Openvino includes a set of plugins for gstreamer, including https://github.com/opencv/gst-video-analytics/wiki/Install-Guide#2-install-gstreamer-video-analytics-plugin.
the script in {OPENVINO_SETUP_VARS_PATH} sets environment variables like PATH, LD_LIBRARY_PATH, and PYTHONPATH so that Openvino libraries,
including gstreamer plugins, are available for other binaries. However, these environment variables prevent access to the globally-installed
libgstreamer1.0 apt-get package. Thus, this script filters those values relating to gstreamer out of the environemnt variables
and output the rest in stdout.

Original usage without this script:
`source /<PATH_TO_OPENVINO>/bin/setupvars.sh && <command>`
Alternative usage with this script:
`env openvino_setupvars <command>`
"""
import subprocess

OPENVINO_SETUP_VARS_PATH='/opt/intel/openvino/bin/setupvars.sh'

if __name__ == '__main__':
    proc = subprocess.Popen([f'/bin/bash -c "source {OPENVINO_SETUP_VARS_PATH} >/dev/null && env"'],
                            stdout=subprocess.PIPE, shell=True)
    for line in proc.communicate()[0].decode().split('\n'):
        line = line.strip()
        if not line:
            continue
        key, value = line.split('=', 1)
        if 'GST_' in key:
            continue
        value = ':'.join([item for item in value.split(':') if 'gstreamer' not in item])
        print(f'{key}={value}')
