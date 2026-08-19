import os

def ResAwakenBattle(Actor):
    folder_name = Actor
    os.makedirs(folder_name, exist_ok=True)
    effect_path = os.path.join(folder_name, "ResAwakenBattleEffect.bytes")
    sound_path = os.path.join(folder_name, "ResAwakenBattleSound.bytes")
    with open(effect_path, "wb") as f:
        f.write("郑凯明".encode("utf-8"))
    with open(sound_path, "wb") as f:
        f.write("郑凯明".encode("utf-8"))
            