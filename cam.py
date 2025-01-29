import gi
import platform
gi.require_version('Gst', '1.0')
gi. require_version( 'GstRtspServer', '1.0')
from gi.repository import Gst, GLib, GstRtspServer

HOST = "0.0.0.0"
PORT = "8559"

device = platform.platform()

if (device.lower().find("linux") != -1):
    PIPELINE = 'v4l2src device=/dev/video0 ! videorate ! video/x-raw, framerate=30/1 ! videoconvert ! x264enc ! rtph264pay name=pay0'
elif (device.lower().find("macos") != -1):
    PIPELINE = 'avfvideosrc ! videorate ! video/x-raw, framerate=30/1 ! videoconvert ! x264enc ! rtph264pay name=pay0'

print (f"hosting RTSP on {HOST}: {PORT}")
print(f"pipeline: {PIPELINE}")

Gst.init(None)

server = GstRtspServer.RTSPServer()
server.props.service = PORT

mounts = server.get_mount_points()

factory = GstRtspServer.RTSPMediaFactory()
factory. set_launch(PIPELINE)

mounts.add_factory("/test", factory)
server. attach (None)

# Create a GLib Main Loop and run it
loop = GLib.MainLoop()
try:
    loop.run ( )
except KeyboardInterrupt:
    pass