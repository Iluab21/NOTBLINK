import time
import queue
import threading
from typing import List, Optional
from mcrcon import MCRcon


class MinecraftRCON:
    def __init__(self, host: str, port: int, password: str, player: str, enable_bossbar: bool = True, enable_actionbar: bool = True):
        self.host = host
        self.port = port
        self.password = password
        self.player = player
        self.enable_bossbar = enable_bossbar
        self.enable_actionbar = enable_actionbar

        self.rcon: Optional[MCRcon] = None
        self.cmd_queue = queue.Queue()
        self.is_connected = False
        self.running = True
        self._lock = threading.Lock()

        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def connect(self) -> bool:
        with self._lock:
            if self.rcon is not None:
                try:
                    self.rcon.disconnect()
                except Exception:
                    pass
                self.rcon = None

            try:
                self.rcon = MCRcon(self.host, self.password, port=self.port, timeout=5)
                self.rcon.connect()
                self.is_connected = True
                print(f"[RCON] Successfully connected to {self.host}:{self.port}")
                if self.enable_bossbar:
                    self._init_bossbar()
                else:
                    self._send_raw("bossbar remove minecraft:blink_bar")
                return True
            except Exception as e:
                self.is_connected = False
                print(f"[RCON] Connection failed ({e}). Check host/port/password.")
                return False

    def _init_bossbar(self):
        commands = [
            'bossbar add blink_bar "Моргания"',
            'bossbar set minecraft:blink_bar players @a',
            'bossbar set minecraft:blink_bar color red',
            'bossbar set minecraft:blink_bar style notched_10',
            'bossbar set minecraft:blink_bar visible true'
        ]
        for cmd in commands:
            self._send_raw(cmd)

    def _send_raw(self, command: str) -> Optional[str]:
        if not self.is_connected or self.rcon is None:
            if not self.connect():
                return None

        try:
            resp = self.rcon.command(command)
            return resp
        except Exception as e:
            print(f"[RCON] Command error ({command}): {e}. Attempting reconnect...")
            self.is_connected = False
            if self.connect():
                try:
                    return self.rcon.command(command)
                except Exception:
                    return None
            return None

    def execute_command(self, command: str):
        formatted_cmd = command.replace("<Ник>", self.player).replace("<Player>", self.player)
        self.cmd_queue.put([formatted_cmd])

    def execute_batch(self, commands: List[str]):
        formatted_batch = [cmd.replace("<Ник>", self.player).replace("<Player>", self.player) for cmd in commands]
        self.cmd_queue.put(formatted_batch)

    def update_bossbar(self, current_blink: int, boss_interval: int):
        """Updates the native in-game bossbar."""
        if not self.enable_bossbar:
            return
        remaining = boss_interval - (current_blink % boss_interval)
        if remaining == boss_interval and current_blink > 0:
            remaining = 0
        progress = (current_blink % boss_interval)
        if progress == 0 and current_blink > 0:
            progress = boss_interval

        title_json = f'{{"text":"👀 Моргания: {current_blink} | 💀 До БОССА: {remaining}","color":"gold","bold":true}}'
        self.execute_batch([
            f'bossbar set minecraft:blink_bar max {boss_interval}',
            f'bossbar set minecraft:blink_bar value {progress}',
            f'bossbar set minecraft:blink_bar name {title_json}'
        ])

    def send_actionbar(self, text: str, color: str = "gold"):
        if not self.enable_actionbar:
            return
        clean_text = text.replace('"', '\\"')
        cmd = f'title {self.player} actionbar {{"text":"{clean_text}","color":"{color}","bold":true}}'
        self.execute_command(cmd)


    def _worker_loop(self):
        while self.running:
            try:
                batch = self.cmd_queue.get(timeout=0.1)
                for cmd in batch:
                    self._send_raw(cmd)
                self.cmd_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"[RCON Worker] Error: {e}")

    def close(self):
        self.running = False
        with self._lock:
            if self.rcon:
                try:
                    self.rcon.disconnect()
                except Exception:
                    pass
                self.rcon = None
