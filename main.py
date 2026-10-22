import os
import sys
import json
import time
import cv2

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from sound_manager import SoundManager
from minecraft_rcon import MinecraftRCON
from triggers import TriggerRegistry
from vision import BlinkDetector
from overlay_server import start_overlay_server, overlay_state

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Config file not found at {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    print("=" * 60)
    print("🚀 NOTBLINK - Minecraft Eye-Tracking Chaos Trigger System")
    print("=" * 60)

    config = load_config()

    audio_cfg = config.get("audio", {})
    sound = SoundManager(
        enabled=audio_cfg.get("enabled", True),
        volume=audio_cfg.get("volume", 0.8)
    )
    mc_cfg = config.get("minecraft", {})
    rcon = MinecraftRCON(
        host=mc_cfg.get("rcon_host", "127.0.0.1"),
        port=mc_cfg.get("rcon_port", 25575),
        password=mc_cfg.get("rcon_password", ""),
        player=mc_cfg.get("player_name", "Steve"),
        enable_bossbar=mc_cfg.get("enable_bossbar", True),
        enable_actionbar=mc_cfg.get("enable_actionbar_titles", True)
    )
    print("[RCON] Connecting to Minecraft server in background...")
    rcon.connect()

    triggers = TriggerRegistry(rcon, sound, config)

    overlay_cfg = config.get("overlay", {})
    if overlay_cfg.get("enabled", True):
        port = overlay_cfg.get("port", 8765)
        start_overlay_server(port)

    detector = BlinkDetector(config)
    if not detector.start_camera():
        print("[Vision] Camera failed to start. Running in manual hotkey mode.")
        use_camera = False
    else:
        use_camera = True
        print("[Vision] Camera successfully started!")

    blink_count = 0
    is_paused = False
    boss_interval = config["gameplay"].get("boss_trigger_interval", 25)
    last_action_title = "СИСТЕМА ГОТОВА"

    VK_F8 = 0x77
    f8_prev_state = False

    def toggle_pause():
        nonlocal is_paused, last_action_title
        is_paused = not is_paused
        if is_paused:
            sound.play("pause")
            last_action_title = "ТРЕКИНГ НА ПАУЗЕ"
            rcon.send_actionbar("⏸️ ТРЕКИНГ НА ПАУЗЕ (F8 / P)", "gold")
            print("\n[⏸️ ПАУЗА] Отслеживание морганий ПРИОСТАНОВЛЕНО! (Нажмите F8 или P для продолжения)")
        else:
            sound.play("resume")
            last_action_title = "ТРЕКИНГ АКТИВЕН"
            rcon.send_actionbar("▶️ ТРЕКИНГ ВОЗОБНОВЛЕН", "green")
            print("\n[▶️ СТАРТ] Отслеживание морганий ВОЗОБНОВЛЕНО!")

        overlay_state.broadcast(
            blink_count=blink_count,
            boss_interval=boss_interval,
            last_action=last_action_title,
            is_blink=False,
            is_paused=is_paused
        )

    def handle_blink(forced_boss: bool = False):
        nonlocal blink_count, last_action_title
        blink_count += 1
        sound.play("blink")

        is_boss = forced_boss or (blink_count % boss_interval == 0)

        if is_boss:
            _, title = triggers.trigger_boss()
            last_action_title = title
            print(f"\n[💥 БОСС-МОРГАНИЕ #{blink_count}] Сработало: {title}")
        else:
            _, title = triggers.trigger_random_regular()
            last_action_title = title
            print(f"\n[👀 Моргание #{blink_count}] Сработало: {title}")

        rcon.update_bossbar(blink_count, boss_interval)

        overlay_state.broadcast(
            blink_count=blink_count,
            boss_interval=boss_interval,
            last_action=last_action_title,
            is_blink=True,
            is_boss=is_boss,
            is_paused=is_paused
        )

    print("\n🎮 Управление:")
    print(" [F8]      - ГЛОБАЛЬНАЯ ПАУЗА / СТАРТ (работает прямо из игры!)")
    print(" [P]       - Пауза / Старт (в окне камеры)")
    print(" [ПРОБЕЛ]  - Симулировать моргание (тест)")
    print(" [T]       - Случайный обычный триггер")
    print(" [B]       - Принудительный БОСС-триггер")
    print(" [R]       - Сброс счетчика морганий")
    print(" [ESC / X] - Выход\n")

    overlay_state.broadcast(blink_count, boss_interval, last_action_title, is_blink=False, is_paused=False)

    try:
        while True:
            if sys.platform == "win32":
                try:
                    import ctypes
                    f8_current = (ctypes.windll.user32.GetAsyncKeyState(VK_F8) & 0x8000) != 0
                    if f8_current and not f8_prev_state:
                        toggle_pause()
                    f8_prev_state = f8_current
                except Exception:
                    pass

            avg_ear = 0.0
            head_down = False

            if use_camera:
                success, frame, blink_detected, avg_ear, head_down = detector.process_frame()
                if success and frame is not None:
                    if blink_detected and not is_paused:
                        handle_blink()

                    detector.draw_hud(frame, blink_count, boss_interval, last_action_title, avg_ear, head_down, is_paused)
                    cv2.imshow("NOTBLINK - Camera Tracking (Active)", frame)
            else:
                time.sleep(0.03)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('x'), ord('X')):  # ESC or X
                break
            elif key in (ord('p'), ord('P'), 239, 207):  # P / З (Пауза)
                toggle_pause()
            elif key in (ord('h'), ord('H'), 240, 208):  # H / Р (Скрыть/Показать HUD)
                detector.show_hud = not detector.show_hud
                print(f"[HUD] Интерфейс на веб-камере: {'ВКЛЮЧЕН' if detector.show_hud else 'ОТКЛЮЧЕН (100% чистая камера)'}")
            elif key == ord(' '):  # Space
                handle_blink()
            elif key in (ord('t'), ord('T'), 229, 197):  # T / Е
                _, title = triggers.trigger_random_regular()
                last_action_title = title
                overlay_state.broadcast(blink_count, boss_interval, last_action_title, is_blink=True, is_boss=False, is_paused=is_paused)
            elif key in (ord('b'), ord('B'), 232, 200):  # B / И
                handle_blink(forced_boss=True)
            elif key in (ord('r'), ord('R'), 234, 202):  # R / К
                blink_count = 0
                last_action_title = "СЧЕТЧИК СБРОШЕН"
                rcon.update_bossbar(blink_count, boss_interval)
                overlay_state.broadcast(blink_count, boss_interval, last_action_title, is_blink=False, is_paused=is_paused)
                print("[Reset] Счетчик морганий сброшен в 0.")

    except KeyboardInterrupt:
        print("\n[Exit] Остановка пользователем...")
    finally:
        if use_camera:
            detector.release()
        rcon.close()
        print("[Exit] Все компоненты остановлены.")


if __name__ == "__main__":
    main()
