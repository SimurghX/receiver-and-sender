import gi
import sys

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

class CameraStreamer: 
    # 127.0.0.1 = Current Device
    def __init__(self, ip="127.0.0.1", port=5600):
        self.ip = ip
        self.port = port
        self.pipeline = None
        self.loop = None

        Gst.init(None)

    # Error process
    def on_error(self, bus, msg):
        err, debug_info = msg.parse_error()
        print(f"ERROR: {err.message}")
        print(f"DEBUG: {debug_info}")

        if self.loop:
            self.loop.quit()

    # End of stream process
    def on_eos(self):
        print("INFO: Reach EOS (End of Stream).")
        if self.loop:
            self.loop.quit()

    # Get live feed from camera
    # Encode with H.264 send with UDP
    def run(self):
        # Define Pipeline Structure
        pipeline_str = (
            f"v4l2src ! "
            f"video/x-raw, width=640, height=480, framerate=30/1 ! "
            f"videoconvert ! "
            f"x264enc tune=zerolatency bitrate=2500 speed-preset=ultrafast key-int-max=30 ! "
            f"rtph264pay config-interval=1 pt=96 ! "
            f"udpsink host={self.ip} port={self.port} sync=false"
        )

        print(f"INFO: Sending to {self.ip}:{self.port}")
        print(f"\nPipeline: {pipeline_str}")
        # Create the pipeline
        try:
            self.pipeline = Gst.parse_launch(pipeline_str)
        except Exception as e:
            print("ERROR: Failed to create pipeline")
            print(f"{e}")
            return
        
        # Bus settings
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self.on_error)

        # Since the camera feed is live EOS is not needed
        # bus.connect("message::eos", on_eos) 
        
        print("INFO: Camera feed is starting. Sending the feed on the background.")
        self.pipeline.set_state(Gst.State.PLAYING)

        # Main loop
        self.loop = GLib.MainLoop()
        try:
            self.loop.run()
        except KeyboardInterrupt:
            print("INFO: Program stopped by user.")
            pass 
        finally:
            print("INFO: Cleaning up resources...")
            self.pipeline.set_state(Gst.State.NULL)
            print("INFO: Stream stopped.")

if __name__ == "__main__":
    streamer = CameraStreamer()
    streamer.run()