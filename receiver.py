import gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# Default variables
UDP_PORT = 5600
HOST_IP = "0.0.0.0"  # Listen for all packages

# Error process
def on_error(self, bus, msg):
    err, debug_info = msg.parse_error()
    print(f"ERROR: {err.message}")
    print(f"DEBUG: {debug_info}")
    global loop

    if loop:
        loop.quit()

# End of stream process
def on_eos(self):
    print("INFO: Reach EOS (End of Stream).")
    global loop
    if loop:
        loop.quit()

def run_gcs_receiver():
    # Start GStreamer
    Gst.init(None)

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
        pipeline = Gst.parse_launch(pipeline_str)
    except Exception as e:
        print("ERROR: Failed to create pipeline")
        print(f"{e}")
        return

    # Bus settings
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message::error", on_error)
    bus.connect("message::eos", on_eos)

    # Start the pipeline
    print("INFO: Waiting for video stream...")
    pipeline.set_state(Gst.State.PLAYING)

    # Main loop
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("INFO: Program stopped by user.")
        pass
    finally:
        print("INFO: Cleaning up resources...")
        pipeline.set_state(Gst.State.NULL)
        print("INFO: Stream stopped.")

if __name__ == "__main__":
    run_gcs_receiver()