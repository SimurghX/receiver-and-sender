import gi
import sys

try:
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst, GLib
except ValueError as e:
    print("ERROR: GStreamer dependencies missing.")
    print(f"ERROR_MSG: {e}")
    sys.exit(1)


UDP_PORT = 5600
# If this device 127.0.0.1
# If another device change to that devices IP
HOST_IP = "127.0.0.1"

# Error process
def on_error(msg):
    err, debug_info = msg.parse_error()
    print(f"ERROR: {err.message}")
    print(f"DEBUG_INFO: {debug_info}")
    global pipeline, loop
    if loop:
        loop.quit()

# End of stream process
def on_eos():
    print("INFO: Reach EOS (End of Stream).")
    global pipeline, loop
    if loop:
        loop.quit()

# Get live feed from camera
# Encode with H.264 send with UDP
def run_camera_sender():
    global pipeline, loop
    Gst.init(None)

    print("INFO: Camera feed getting ready.")
    print(f"Feed address: {HOST_IP}:{UDP_PORT}")
    
    # Pipeline Structure
    pipeline_str = (
        f"autovideosrc ! "
        f"videoconvert ! "
        f"x264enc tune=zerolatency bitrate=1000 speed-preset=ultrafast ! "
        f"rtph264pay config-interval=1 pt=96 ! "
        f"udpsink host={HOST_IP} port={UDP_PORT}"
    )   

    print(f"\nPipeline: {pipeline_str}")
    # Create the pipeline
    try:
        pipeline = Gst.parse_launch(pipeline_str)
    except Exception as e:
        print("ERROR: Pipeline could not be created.")
        print(f"ERROR_MSG: {e}")
        return
    
    # Bus settings
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message::error", on_error)

    # Sınce the camera feed is live EOS is not needed
    # bus.connect("message::eos", on_eos) 
    
    print("INFO: Camera feed is starting. Sending the feed on the background.")
    pipeline.set_state(Gst.State.PLAYING)

    # Main loop
    loop = GLib.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("INFO: Program stopped by user.")
        pass 
    finally:
        print("INFO: Cleaning up resources")
        pipeline.set_state(Gst.State.NULL)
        print("INFO: Stream stopped.")

if __name__ == "__main__":
    run_camera_sender()