#!/usr/bin/env python

import gi
import sys
import argparse
import os

try:
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst, GObject
except ValueError as e:
    print(f"Hata: GStreamer yüklenemedi veya PyGObject bulunamadı. Hata: {e}")
    sys.exit(1)

# Sabitler
UDP_PORT = 5600
# Kendi bilgisayarınızda bir alıcı çalıştırıyorsanız '127.0.0.1' (localhost) doğru.
# Başka bir cihaza gönderecekseniz o cihazın IP'sini girin.
HOST_IP = "127.0.0.1" 

# Global değişkenler (Önceki kodunuzla uyumlu kalmak için)
pipeline = None
loop = None

# --- Hata ve EOS İşleyicileri (Değişmedi) ---

def on_error(bus, msg):
    """Hata mesajlarını işler ve uygulamayı sonlandırır."""
    err, debug_info = msg.parse_error()
    print(f"Hata Kaynağı: {msg.src.get_name()}")
    print(f"Hata: {err.message}")
    print(f"Hata Ayıklama Bilgisi: {debug_info}")
    global pipeline, loop
    if pipeline:
        pipeline.set_state(Gst.State.NULL)
    if loop:
        loop.quit()

def on_eos(bus, msg):
    """Akış Sonu (End of Stream) sinyalini işler."""
    print("Akış Sonu (End of Stream) ulaşıldı.")
    global pipeline, loop
    if pipeline:
        pipeline.set_state(Gst.State.NULL)
    if loop:
        loop.quit()

# ----------------------------------------------------------------

def run_camera_sender():
    """
    Kameradan canlı video akışını alır, H.264 olarak kodlar ve UDP üzerinden gönderir.
    """
    global pipeline, loop
    Gst.init(None)

    print("Kamera akışı hazırlanıyor.")
    print(f"Akış adresi: {HOST_IP}:{UDP_PORT}")
    
    # Pipeline Yapısı:
    # autovideosrc: Sistemdeki varsayılan kamerayı otomatik olarak bulur ve açar.
    # videoconvert: RAW video formatını kodlayıcı için hazırlar.
    # x264enc: H.264 formatına kodlar (zerolatency=düşük gecikme için kritik).
    # rtph264pay: H.264 verisini RTP paketlerine dönüştürür.
    # udpsink: RTP paketlerini alıcının adresine ve portuna gönderir.

    # NOT: Linux'ta V4L2 destekli kameralar için 'v4l2src' daha kesin sonuç verebilir.
    # Eğer bu betik çalışmazsa 'autovideosrc' yerine 'v4l2src ! video/x-raw, framerate=30/1 ! ' deneyin.
    # Yeni pipeline_str denemesi (Windows için dshowvideosrc)

    pipeline_str = (
        f"ksvideosrc ! "         # <-- dshowvideosrc yerine ksvideosrc
        f"videoconvert ! "
        f"x264enc tune=zerolatency bitrate=1000 ! "
        f"rtph264pay config-interval=1 pt=96 ! "
        f"udpsink host={HOST_IP} port={UDP_PORT}"
    )   

    print(f"\nPipeline: {pipeline_str}")
    
    try:
        pipeline = Gst.parse_launch(pipeline_str)
    except Exception as e:
        print(f"Hata: Pipeline oluşturulurken hata. Gerekli elemanların (x264enc, autovideosrc) kurulu olduğundan emin olun. Hata: {e}")
        return

    # Bus ayarları
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message::error", on_error)
    # Kamera akışı (canlı) olduğu için EOS gelmesi beklenmez, bu yüzden EOS bağlantısını kaldırabiliriz
    # bus.connect("message::eos", on_eos) 
    
    print("Kamera akışı başlatılıyor. Pencere açılmayacaktır, akış arka planda gönderiliyor...")
    pipeline.set_state(Gst.State.PLAYING)

    # Ana döngü
    loop = GObject.MainLoop()
    try:
        loop.run()
    except KeyboardInterrupt:
        print("\nKullanıcı tarafından durduruldu (Ctrl+C).")
        pass 

    print("Pipeline sonlandırılıyor...")
    pipeline.set_state(Gst.State.NULL)


if __name__ == "__main__":
    run_camera_sender()
    print("Gönderici sonlandı.")