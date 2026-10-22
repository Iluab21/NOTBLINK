import json
import os
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from minecraft_rcon import MinecraftRCON
from triggers import TriggerRegistry
from sound_manager import SoundManager

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("🛠️  NOTBLINK - RCON & Trigger Test Utility")
    print("=" * 60)

    cfg = load_config()
    mc_cfg = cfg.get("minecraft", {})
    host = mc_cfg.get("rcon_host", "127.0.0.1")
    port = mc_cfg.get("rcon_port", 25575)
    pwd = mc_cfg.get("rcon_password", "")
    player = mc_cfg.get("player_name", "Steve")

    print(f"Connecting to: {host}:{port} as player '{player}'...")
    rcon = MinecraftRCON(host, port, pwd, player)
    sound = SoundManager()
    registry = TriggerRegistry(rcon, sound, cfg)

    if not rcon.connect():
        print("❌ Не удалось подключиться к серверу по RCON.")
        print("Проверьте:")
        print(" 1. Запущен ли Minecraft-сервер?")
        print(" 2. Включен ли RCON в server.properties (enable-rcon=true)?")
        print(" 3. Совпадают ли порт и rcon.password в config.json и server.properties?")
        return

    print("✅ Успешное подключение к RCON!")

    while True:
        print("\nВыберите действие:")
        print(" 0. Тестовое приветствие в игре (say Hello)")
        print(" 1. Фейковый MLG (Подмена предмета)")
        print(" 2. Прыжок в будущее (tp ^ ^ ^4)")
        print(" 3. Масляные руки (Выброс предмета Q)")
        print(" 4. Инверсия взгляда (180 градусов)")
        print(" 5. Скользкий пол (Синий лед)")
        print(" 6. Квантовая рулетка блоков")
        print(" 7. Гравитационный коллапс (Падение гравия/песка)")
        print(" 8. Внезапная аквадискотека (Вода + рыбы)")
        print(" 9. Призыв Стены перед лицом")
        print(" 10. Эффект Гулливера (0.2x или 4x)")
        print(" 11. Скример-приманка (Шипение крипера / Варден)")
        print(" 12. Мгновенный торт (Замуровывание + Голод)")
        print(" 13. Рокировка с мобом")
        print(" 14. [БОСС] Охотник-Преследователь")
        print(" 15. [БОСС] Режим Лунатика")
        print(" 16. Скоростной рассинхрон (Спринт / Улитка)")
        print(" 99. Выход (или напишите 'exit')")

        choice = input("\nВведите номер: ").strip()
        if choice.lower() in ('99', 'exit', 'close', 'выход'):
            break

        handlers = {
            "0": lambda: rcon.execute_command(f'say Привет, {player}! RCON работает отлично!'),
            "1": registry.trigger_fake_mlg,
            "2": registry.trigger_jump_future,
            "3": registry.trigger_oily_hands,
            "4": registry.trigger_view_inversion,
            "5": registry.trigger_slippery_floor,
            "6": registry.trigger_block_roulette,
            "7": registry.trigger_gravity_collapse,
            "8": registry.trigger_water_disco,
            "9": registry.trigger_wall_summon,
            "10": registry.trigger_gulliver_effect,
            "11": registry.trigger_screamer_decoy,
            "12": registry.trigger_instant_cake,
            "13": registry.trigger_body_swap,
            "14": registry.trigger_boss_pursuer,
            "15": registry.trigger_sleepwalker_mode,
            "16": registry.trigger_speed_roulette,
        }

        func = handlers.get(choice)
        if func:
            print(f"Выполняю триггер #{choice}...")
            func()
            print("Готово!")
        else:
            print("Неверный номер, попробуйте снова.")

    rcon.close()


if __name__ == "__main__":
    main()
