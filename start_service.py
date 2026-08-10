from foundry_local_sdk import Configuration, FoundryLocalManager
import time
import json
import sys

MODEL_ALIAS = "phi-4-mini"
INFO_FILE = "foundry_service_info.json"   # app.py ile aynı klasörde olsun

config = Configuration(app_name="kisisel_asistan_service")   # port belirtmiyoruz, dinamik kalsın
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance

print("⚙️ Execution provider'lar hazırlanıyor...")
try:
    manager.download_and_register_eps(progress_callback=lambda ep, pct: print(f" {ep}: %{pct:.0f}"))
except Exception as ep_err:
    print(f"⚠️ EP yükleme uyarısı: {ep_err}")

model = manager.catalog.get_model(MODEL_ALIAS)

def load_best_model_variant(model):
    """
    Kullanıcının donanımında varsayılan EP (örneğin OpenVINO) yüklü veya uyumlu değilse,
    CUDA, Generic GPU veya CPU varyantlarına otomatik geçiş yaparak çökmesini engeller.
    """
    print(f"📦 Model yükleniyor (Varsayılan: {model.id})...")
    try:
        model.download(lambda pct: print(f" İndirme: %{pct:.0f}"))
        model.load()
        print(f"✅ Varsayılan model varyantı başarıyla yüklendi: {model.id}")
        return True
    except Exception as err:
        print(f"⚠️ Varsayılan model varyantı ({model.id}) yüklenemedi: {err}")
        print("🔄 Donanımınızla uyumlu alternatif varyantlar taranıyor...")

    # Varyantları sırala: CUDA / GPU varyantları önce, Generic CPU en son çare (her bilgisayarda çalışır)
    variants = list(model.variants)
    
    def variant_priority(v):
        v_id = v.id.lower()
        if "cuda" in v_id:
            return 1
        elif "gpu" in v_id and "openvino" not in v_id:
            return 2
        elif "cpu" in v_id:
            return 3
        return 4

    sorted_variants = sorted(variants, key=variant_priority)

    for variant in sorted_variants:
        if variant.id == model.id:
            continue
        try:
            print(f"👉 Deneniyor: {variant.id}")
            model.select_variant(variant)
            model.download(lambda pct: print(f" İndirme: %{pct:.0f}"))
            model.load()
            print(f"✅ Uyumlu model varyantı yüklendi: {variant.id}")
            return True
        except Exception as v_err:
            print(f" ❌ {variant.id} yüklenemedi: {v_err}")

    return False

if not load_best_model_variant(model):
    print("❌ HATA: Hiçbir model varyantı donanımınızda yüklenemedi!")
    sys.exit(1)

manager.start_web_service()
base_url = f"{manager.urls[0]}/v1"

# Gerçek port ve model id'yi dosyaya yaz
with open(INFO_FILE, "w") as f:
    json.dump({"base_url": base_url, "model_id": model.id}, f)

print(f"✅ Servis hazır: {base_url}")
print(f"Bilgiler '{INFO_FILE}' dosyasına yazıldı.")

while True:
    time.sleep(3600)