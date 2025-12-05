import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Default variables
UDP_PORT = 5600
HOST_IP = "0.0.0.0"  # Listen for all packages

class CameraReceiver:
    # 0.0.0.0 Listen for all packages
    def __init__(self, ip="0.0.0.0", port=5600):
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

    # Receive live camera feed
    def run(self):
        pipeline_str = (
            f"udpsrc port={UDP_PORT} address={HOST_IP} ! "
            "application/x-rtp, payload=96 ! "
            "rtph264depay ! "
            "h264parse ! "
            "decodebin ! "
            "videoconvert ! "
            "autovideosink sync=false"
        )

        print(f"Pipeline: {pipeline_str}")

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
        bus.connect("message::eos", self.on_eos)

        # Start the pipeline
        print("INFO: Waiting for video stream...")
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
    receiver = CameraReceiver()
    receiver.run()