#!/usr/bin/env python

# GStreamer'ı Python'da kullanmak için gerekli kütüphaneler
import gi
import sys

# GStreamer sürümünü belirtin
try:
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst, GLib
except ValueError as e:
    print(f"Hata: GStreamer yüklenemedi. Gerekli kütüphanelerin kurulu olduğundan emin olun. Hata: {e}")
    sys.exit(1)

# Sabitler
UDP_PORT = 5600
HOST_IP = "0.0.0.0"  # Tüm arayüzlerden gelen paketleri dinle

def on_error(bus, msg):
    """Hata mesajlarını işler ve uygulamayı sonlandırır."""
    err, debug_info = msg.parse_error()
    print(f"Hata Kaynağı: {msg.src.get_name()}")
    print(f"Hata: {err.message}")
    print(f"Hata Ayıklama Bilgisi: {debug_info}")
    # Pipeline'ı durdur ve döngüyü sonlandır
    global pipeline
    if pipeline:
        pipeline.set_state(Gst.State.NULL)
    GLib.MainLoop().quit()

def on_eos(bus, msg):
    """Akış Sonu (End of Stream) sinyalini işler."""
    print("Akış Sonu (End of Stream) ulaşıldı.")
    # Pipeline'ı durdur ve döngüyü sonlandır
    global pipeline
    if pipeline:
        pipeline.set_state(Gst.State.NULL)
    GLib.MainLoop().quit()

def run_gcs_receiver():
    """GCS alıcısını başlatır ve GStreamer pipeline'ı oluşturur."""
    global pipeline

    # 1. GStreamer'ı başlat
    Gst.init(None)

    # 2. Pipeline dizgisini (string) oluştur
    # Drone'dan gelen tipik bir H.264 RTP akışını çözmek için gerekli adımlar:
    # 1. udpsrc: 5600 portundan UDP paketlerini alır.
    # 2. caps: Gelen verinin RTP H.264 video olduğunu belirtir.
    # 3. rtph264depay: RTP paketlerinden H.264 veri birimlerini (NAL'leri) ayırır.
    # 4. h264parse: H.264 akışını ayrıştırır ve kod çözücü için hazırlar.
    # 5. avdec_h264: H.264 verisini çözerek RAW video formatına dönüştürür.
    #    (Sisteminizde donanım hızlandırma varsa 'vaapih264dec' veya 'nvdec' gibi bir element kullanabilirsiniz.)
    # 6. videoconvert: Çözülmüş videoyu ekrana uygun bir formata dönüştürür.
    # 7. autovideosink: Video akışını sistemdeki en uygun pencere/görüntüleme elemanına gönderir.

    pipeline_str = (
        f"udpsrc port={UDP_PORT} address={HOST_IP} ! "
        f"application/x-rtp, media=(string)video, clock-rate=(int)90000, encoding-name=(string)H264, payload=(int)96 ! "
        f"rtph264depay ! "
        f"h264parse ! "
        f"avdec_h264 ! "
        f"videoconvert ! "
        f"autovideosink"
    )

    print(f"Pipeline: {pipeline_str}")
    
    # 3. Pipeline'ı oluştur
    try:
        pipeline = Gst.parse_launch(pipeline_str)
    except Exception as e:
        print(f"Pipeline oluşturulurken hata: {e}")
        return

    # 4. Bus (Otobüs) ayarlarını yap
    # Bus, GStreamer elemanlarından gelen mesajları (Hata, Akış Sonu, vb.) almak için kullanılır.
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message::error", on_error)
    bus.connect("message::eos", on_eos)

    # 5. Pipeline'ı başlat
    print("Video akışı bekleniyor. Pipeline başlatılıyor...")
    pipeline.set_state(Gst.State.PLAYING)

    # 6. Ana döngüyü başlat
    # Bu, GStreamer'ın olayları (frameler, hatalar vb.) işlemesini sağlar.
    loop = GLib.MainLoop()
    try:
        loop.run()  # <-- Bu satır eksikti, programı hayatta tutan budur.
    except KeyboardInterrupt:
        print("\nKullanıcı tarafından durduruldu.")
        on_eos(None, None) # Temiz kapanış
    except Exception as e:
        print(f"Döngü hatası: {e}")

if __name__ == "__main__":
    run_gcs_receiver()
