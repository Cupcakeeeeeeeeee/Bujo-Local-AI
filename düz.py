from foundry_local_sdk import Configuration, FoundryLocalManager
config = Configuration(app_name="kisisel_asistan_service")   # port belirtmiyoruz, dinamik kalsın
FoundryLocalManager.initialize(config)
manager = FoundryLocalManager.instance
models = manager.catalog.list_models()
for m in models:
    print(f"alias={m.alias}  id={m.id}  device={getattr(m, 'device', '?')}  cached={getattr(m, 'is_cached', '?')}")