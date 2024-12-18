import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstRtspServer", "1.0")
from gi.repository import Gst
from gi.repository import GstRtspServer
from gi.repository import GLib


class GstUdpMediaFactory(GstRtspServer.RTSPMediaFactory):

    def __init__(self, address="127.0.0.1", port="5700"):
        GstRtspServer.RTSPMediaFactory.__init__(self)

        # udpsrc options
        self.address = address
        self.port = port

    def do_create_element(self, url):
        source = f"udpsrc address={self.address} port={self.port}"

        codec = "application/x-rtp, payload=96 ! rtph264depay ! h264parse ! avdec_h264"

        s_h264 = "x264enc tune=zerolatency"
        pipeline_str = f"( {source} ! {codec} ! queue max-size-buffers=1 name=q_enc ! {s_h264} ! rtph264pay name=pay0 pt=96 )"
        print(pipeline_str)
        return Gst.parse_launch(pipeline_str)


class GstServer:
    """
    A GStreamer RTSP server streaming a udpsrc to:

    rtsp://127.0.0.1:8554/camera
    """

    def __init__(self):
        self.server = GstRtspServer.RTSPServer()
        self.server.set_address("127.0.0.1")
        self.server.set_service("8557")

        media_factory = GstUdpMediaFactory(address="127.0.0.1", port="5700")
        media_factory.set_shared(True)

        mount_points = self.server.get_mount_points()
        mount_points.add_factory("/camera", media_factory)

        self.server.attach(None)


def main():
    Gst.init(None)
    server = GstServer()
    loop = GLib.MainLoop()
    loop.run()


if __name__ == "__main__":
    main()