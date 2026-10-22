import random
import time
import threading
from typing import Dict, Any, Callable
import pyautogui


JUNK_ITEMS = [
    "minecraft:cake",
    "minecraft:stick",
    "minecraft:pufferfish",
    "minecraft:flower_pot",
    "minecraft:poisonous_potato",
    "minecraft:wooden_hoe",
    "minecraft:dead_bush",
    "minecraft:wet_sponge",
    "minecraft:bowl",
    "minecraft:wheat_seeds",
    "minecraft:carved_pumpkin",
    "minecraft:bone"
]

ROULETTE_BLOCKS = [
    "minecraft:melon",
    "minecraft:sponge",
    "minecraft:slime_block",
    "minecraft:tnt",
    "minecraft:soul_sand",
    "minecraft:bookshelf",
    "minecraft:target",
    "minecraft:pumpkin",
    "minecraft:honey_block",
    "minecraft:hay_block",
    "minecraft:cobweb"
]


class TriggerRegistry:
    def __init__(self, rcon_client, sound_manager, config: dict):
        self.rcon = rcon_client
        self.sound = sound_manager
        self.config = config
        self.player = config["minecraft"]["player_name"]
        self.use_pyautogui = config["gameplay"].get("use_pyautogui_for_drop", True)
        self.gulliver_duration = config["gameplay"].get("gulliver_duration_seconds", 12)
        self.sleepwalker_duration = config["gameplay"].get("sleepwalker_duration_seconds", 25)
        self.prevent_repeats = config["gameplay"].get("prevent_repeats_history", 3)
        self.recent_triggers = []


        self.regular_triggers = [
            ("fake_mlg", "Фейковый MLG (Подмена)", self.trigger_fake_mlg),
            ("jump_future", "Прыжок в будущее", self.trigger_jump_future),
            ("oily_hands", "Масляные руки (Выброс)", self.trigger_oily_hands),
            ("view_inversion", "Инверсия взгляда (180°)", self.trigger_view_inversion),
            ("slippery_floor", "Скользкий пол (Лед)", self.trigger_slippery_floor),
            ("block_roulette", "Квантовая рулетка блоков", self.trigger_block_roulette),
            ("gravity_collapse", "Гравитационный коллапс", self.trigger_gravity_collapse),
            ("water_disco", "Внезапная аквадискотека", self.trigger_water_disco),
            ("wall_summon", "Призыв Стены", self.trigger_wall_summon),
            ("gulliver_effect", "Эффект Гулливера / Лилипута", self.trigger_gulliver_effect),
            ("screamer_decoy", "Скример-приманка", self.trigger_screamer_decoy),
            ("instant_cake", "Мгновенный торт", self.trigger_instant_cake),
            ("body_swap", "Рокировка с мобом", self.trigger_body_swap),
            ("anvil_drop", "Наковальня сверху!", self.trigger_anvil_drop),
            ("speed_roulette", "Скоростной рассинхрон", self.trigger_speed_roulette),
        ]

        self.boss_triggers = [
            ("boss_pursuer", "Охотник-Преследователь", self.trigger_boss_pursuer),
            ("sleepwalker_mode", "Режим Лунатика", self.trigger_sleepwalker_mode)
        ]


    def trigger_fake_mlg(self):
        item = random.choice(JUNK_ITEMS)
        commands = [
            f'item replace entity {self.player} weapon.mainhand with {item} 1',
            f'execute as {self.player} at @s run playsound minecraft:entity.item.break master @s ~ ~ ~ 1.5 1.2'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("⚠️ ФЕЙКОВЫЙ MLG: Предмет подменен!", "gold")
        self.sound.play("warning")

    def trigger_jump_future(self):
        commands = [
            f'execute as {self.player} at @s rotated ~ 0 run tp @s ^ ^0.2 ^4',
            f'execute as {self.player} at @s run playsound minecraft:entity.enderman.teleport master @s ~ ~ ~ 1.5 1.5'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("⚡ СЛЕПОЙ РЫВОК ВПЕРЕД (+4 блока)!", "aqua")
        self.sound.play("warning")

    def trigger_oily_hands(self):
        if self.use_pyautogui:
            try:
                pyautogui.FAILSAFE = False
                pyautogui.press('q')
            except Exception as e:
                print(f"[Trigger] pyautogui press failed: {e}")
        commands = [
            f'execute as {self.player} at @s run playsound minecraft:entity.item.pickup master @s ~ ~ ~ 2.0 0.5'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("🧈 МАСЛЯНЫЕ РУКИ: Предмет выброшен!", "yellow")
        self.sound.play("warning")

    def trigger_view_inversion(self):
        commands = [
            f'execute at {self.player} rotated ~ 0 run tp {self.player} ~ ~ ~ ~180 ~',
            f'execute as {self.player} at @s run playsound minecraft:entity.player.attack.sweep master @s ~ ~ ~ 1.5 0.7'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("🔄 РАЗВОРОТ КАМЕРЫ НА 180°!", "red")
        self.sound.play("warning")

    def trigger_slippery_floor(self):
        commands = [
            f'execute at {self.player} run fill ~-2 ~-1 ~-2 ~2 ~-1 ~2 minecraft:blue_ice',
            f'execute as {self.player} at @s run playsound minecraft:block.glass.place master @s ~ ~ ~ 2 1.2'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("⛸️ СКОЛЬЗКИЙ СИНИЙ ЛЕД ПОД НОГАМИ!", "aqua")
        self.sound.play("warning")


    def trigger_block_roulette(self):
        chosen_block = random.choice(ROULETTE_BLOCKS)
        block_clean = chosen_block.split(":")[-1].replace("_", " ").upper()
        commands = [
            f'execute at {self.player} run fill ~-2 ~-1 ~-2 ~2 ~2 ~2 {chosen_block}',
            f'execute at {self.player} run fill ~ ~ ~ ~ ~1 ~ minecraft:air',
            f'execute as {self.player} at @s run playsound minecraft:block.note_block.bell master @s ~ ~ ~ 2 1.5'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar(f"🎰 КВАНТОВАЯ РУЛЕТКА: {block_clean}!", "light_purple")
        self.sound.play("warning")

    def trigger_gravity_collapse(self):
        material = random.choice(["minecraft:gravel", "minecraft:red_sand", "minecraft:sand"])
        commands = [
            f'execute at {self.player} run fill ~-2 ~3 ~-2 ~2 ~5 ~2 {material}',
            f'execute as {self.player} at @s run playsound minecraft:block.gravel.break master @s ~ ~ ~ 2.0 0.8'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("💥 ГРАВИТАЦИОННЫЙ КОЛЛАПС СВЕРХУ!", "gold")
        self.sound.play("warning")

    def trigger_water_disco(self):
        commands = [
            f'execute at {self.player} run fill ~-1 ~ ~-1 ~1 ~2 ~1 minecraft:water keep',
            f'execute at {self.player} run summon tropical_fish ~ ~1 ~',
            f'execute at {self.player} run summon tropical_fish ~ ~1 ~',
            f'execute at {self.player} run summon glow_squid ~ ~1 ~',
            f'execute as {self.player} at @s run playsound minecraft:entity.player.splash master @s ~ ~ ~ 2 1.0'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("🐠 ВНЕЗАПНАЯ АКВАДИСКОТЕКА!", "aqua")
        self.sound.play("warning")

    def trigger_wall_summon(self):
        wall_mat = random.choice(["minecraft:obsidian", "minecraft:bedrock"])
        commands = [
            f'execute at {self.player} run fill ^-1 ^ ^2 ^1 ^2 ^2 {wall_mat}',
            f'execute as {self.player} at @s run playsound minecraft:block.stone.place master @s ~ ~ ~ 2 0.6'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("🧱 СТЕНА В 2 БЛОКАХ ПЕРЕД ЛИЦОМ!", "dark_purple")
        self.sound.play("warning")


    def trigger_gulliver_effect(self):
        scale = random.choice([0.2, 3.5])
        mode_text = "ЛИЛИПУТ (0.2x)" if scale < 1.0 else "ГИГАНТ (3.5x)"
        commands = [
            f'attribute {self.player} minecraft:scale base set {scale}',
            f'attribute {self.player} minecraft:generic.scale base set {scale}',
            f'execute as {self.player} at @s run playsound minecraft:entity.player.burp master @s ~ ~ ~ 2.0 0.8'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar(f"🔬 ЭФФЕКТ ГУЛЛИВЕРА: {mode_text} ({self.gulliver_duration} сек)!", "green")
        self.sound.play("scale")

        def _revert():
            time.sleep(self.gulliver_duration)
            self.rcon.execute_command(f'attribute {self.player} minecraft:scale base set 1.0')
            self.rcon.execute_command(f'attribute {self.player} minecraft:generic.scale base set 1.0')
            self.rcon.send_actionbar("📏 Размер вернулся в норму!", "green")

        threading.Thread(target=_revert, daemon=True).start()

    def trigger_screamer_decoy(self):
        commands = [
            f'execute as {self.player} at @s run playsound minecraft:entity.elder_guardian.curse master @s ~ ~ ~ 5.0 1.0',
            f'execute as {self.player} at @s run playsound minecraft:entity.creeper.primed master @s ~ ~ ~ 5.0 1.0',
            f'effect give {self.player} minecraft:darkness 3 0 true'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("😱 КТО-ТО ПРЯМО ЗА СПИНОЙ?!", "dark_red")
        self.sound.play("screamer")

    def trigger_instant_cake(self):
        commands = [
            f'execute at {self.player} run fill ~-1 ~ ~-1 ~1 ~1 ~1 minecraft:cake keep',
            f'effect give {self.player} minecraft:hunger 5 255 true',
            f'execute as {self.player} at @s run playsound minecraft:entity.generic.eat master @s ~ ~ ~ 2.0 1.0'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("🎂 ЗАМУРОВАН В ТОРТ! ЕШЬ, ЧТОБЫ ВЫЙТИ!", "light_purple")
        self.sound.play("warning")

    def trigger_body_swap(self):
        commands = [
            f'execute at {self.player} run summon armor_stand ~ ~ ~ {{Invisible:1b,Invulnerable:1b,Tags:["swap_stand"]}}',
            f'execute at {self.player} as @e[type=!player,type=!item,type=!armor_stand,limit=1,sort=random,distance=2..25] at @s run tag @s add swap_target',
            f'execute as @e[tag=swap_target,limit=1] at @s run tp {self.player} ~ ~ ~',
            f'execute as @e[tag=swap_target,limit=1] at @e[tag=swap_stand,limit=1] run tp @s ~ ~ ~',
            f'kill @e[tag=swap_stand]',
            f'tag @e[tag=swap_target] remove swap_target',
            f'execute as {self.player} at @s run playsound minecraft:entity.enderman.teleport master @s ~ ~ ~ 2 1.0'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("🌀 РОКИРОВКА С БЛИЖАЙШИМ МОБОМ!", "dark_aqua")
        self.sound.play("warning")


    def trigger_anvil_drop(self):
        commands = [
            f'execute at {self.player} run summon falling_block ~ ~8 ~ {{BlockState:{{Name:"minecraft:anvil"}}}}',
            f'execute as {self.player} at @s run playsound minecraft:block.anvil.land master @s ~ ~ ~ 2.0 1.5'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("⚠️ НАКОВАЛЬНЯ СВЕРХУ! БЕГИ!", "red")
        self.sound.play("warning")

    def trigger_speed_roulette(self):
        is_sonic = random.choice([True, False])
        speed_val = 0.35 if is_sonic else 0.02
        label = "СВЕРХСКОРОСТЬ" if is_sonic else "УЛИТКА"
        commands = [
            f'attribute {self.player} minecraft:movement_speed base set {speed_val}',
            f'attribute {self.player} minecraft:generic.movement_speed base set {speed_val}',
            f'effect give {self.player} minecraft:speed 5 4 true' if is_sonic else f'effect give {self.player} minecraft:slowness 5 6 true',
            f'execute as {self.player} at @s run playsound minecraft:entity.horse.gallop master @s ~ ~ ~ 2.0 1.5'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar(f"👟 СКОРОСТНОЙ СБОЙ: {label} (5 сек)!", "yellow")
        self.sound.play("warning")

        def _revert_speed():
            time.sleep(5)
            self.rcon.execute_command(f'attribute {self.player} minecraft:movement_speed base set 0.1')
            self.rcon.execute_command(f'attribute {self.player} minecraft:generic.movement_speed base set 0.1')
            self.rcon.send_actionbar("👟 Скорость вернулась в норму!", "green")

        threading.Thread(target=_revert_speed, daemon=True).start()


    def trigger_boss_pursuer(self):
        summon_cmd = (
            f'execute at {self.player} rotated ~ 0 run summon wither_skeleton ^ ^0.2 ^4 '
            f'{{CustomName:\'{{"text":"☠ ПРЕСЛЕДОВАТЕЛЬ","color":"dark_red","bold":true}}\','
            f'CustomNameVisible:1b,Glowing:1b,Tags:["boss_pursuer"],'
            f'Attributes:['
            f'{{Name:"generic.follow_range",Base:64.0d}},'
            f'{{Name:"minecraft:follow_range",Base:64.0d}},'
            f'{{Name:"generic.movement_speed",Base:0.35d}},'
            f'{{Name:"minecraft:movement_speed",Base:0.35d}}'
            f']}}'
        )
        commands = [
            f'execute as {self.player} at @s run playsound minecraft:entity.wither.spawn master @s ~ ~ ~ 2.5 1.0',
            f'execute as {self.player} at @s run playsound minecraft:entity.lightning_bolt.thunder master @s ~ ~ ~ 2.0 0.8',
            summon_cmd,
            f'item replace entity @e[tag=boss_pursuer,sort=nearest,limit=1] weapon.mainhand with minecraft:netherite_sword',
            f'item replace entity @e[tag=boss_pursuer,sort=nearest,limit=1] armor.head with minecraft:netherite_helmet',
            f'item replace entity @e[tag=boss_pursuer,sort=nearest,limit=1] armor.chest with minecraft:netherite_chestplate',
            f'item replace entity @e[tag=boss_pursuer,sort=nearest,limit=1] armor.legs with minecraft:netherite_leggings',
            f'item replace entity @e[tag=boss_pursuer,sort=nearest,limit=1] armor.feet with minecraft:netherite_boots',
            f'effect give @e[tag=boss_pursuer] minecraft:speed 9999 2 false',
            f'effect give @e[tag=boss_pursuer] minecraft:strength 9999 1 false',
            f'effect give @e[tag=boss_pursuer] minecraft:resistance 9999 1 false',
            f'effect give @e[tag=boss_pursuer] minecraft:fire_resistance 9999 0 false',
            f'effect give @e[tag=boss_pursuer] minecraft:regeneration 9999 0 false',
            f'attribute @e[tag=boss_pursuer] minecraft:generic.follow_range base set 64',
            f'attribute @e[tag=boss_pursuer] minecraft:follow_range base set 64',
            f'attribute @e[tag=boss_pursuer] minecraft:generic.movement_speed base set 0.35',
            f'attribute @e[tag=boss_pursuer] minecraft:movement_speed base set 0.35',
            f'execute as @e[tag=boss_pursuer,sort=nearest,limit=1] at @s run damage @s 0.0001 player_attack by {self.player}',
            f'title {self.player} title {{"text":"☠ БОСС: ПРЕСЛЕДОВАТЕЛЬ!","color":"dark_red","bold":true}}',
            f'title {self.player} subtitle {{"text":"В незеритовой броне и жаждет мести!","color":"gold"}}'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar("☠ ПОЯВИЛСЯ БОСС: ПРЕСЛЕДОВАТЕЛЬ В НЕЗЕРИТЕ!", "dark_red")
        self.sound.play("boss")

    def trigger_sleepwalker_mode(self):
        duration = self.sleepwalker_duration
        commands = [
            f'effect give {self.player} minecraft:levitation {duration} 2 false',
            f'effect give {self.player} minecraft:darkness {duration} 0 false',
            f'effect give {self.player} minecraft:blindness {duration} 0 false',
            f'effect give {self.player} minecraft:speed {duration} 1 false',
            f'effect give {self.player} minecraft:glowing {duration} 0 false',
            f'execute at {self.player} run summon firework_rocket ~ ~1 ~ {{LifeTime:0,FireworksItem:{{id:firework_rocket,count:1,tag:{{Fireworks:{{Explosions:[{{Type:1,Colors:[I;16711680,16776960]}}]}}}}}}}}',
            f'title {self.player} title {{"text":"🌀 РЕЖИМ ЛУНАТИКА!","color":"light_purple","bold":true}}',
            f'title {self.player} subtitle {{"text":"Взлет в небо на {duration} сек... а потом падение!","color":"yellow"}}'
        ]
        self.rcon.execute_batch(commands)
        self.rcon.send_actionbar(f"🌀 РЕЖИМ ЛУНАТИКА: Взлет ({duration} сек) перед падением!", "light_purple")
        self.sound.play("boss")

        def _sleepwalker_watcher():
            for rem in range(duration, 0, -5):
                time.sleep(5)
                left = rem - 5
                if left > 0:
                    self.rcon.send_actionbar(f"🌀 ВЗЛЕТ В СТРАТОСФЕРУ: до падения {left} сек...", "light_purple")
            drop_commands = [
                f'effect clear {self.player} minecraft:levitation',
                f'effect clear {self.player} minecraft:blindness',
                f'effect clear {self.player} minecraft:darkness',
                f'title {self.player} title {{"text":"💀 СМЕРТЕЛЬНОЕ ПАДЕНИЕ!","color":"dark_red","bold":true}}',
                f'title {self.player} subtitle {{"text":"Гравитация вернулась! Берегись земли!","color":"red"}}',
                f'execute as {self.player} at @s run playsound minecraft:entity.ghast.scream master @s ~ ~ ~ 3.0 1.0',
                f'execute as {self.player} at @s run playsound minecraft:entity.generic.explode master @s ~ ~ ~ 2.0 1.2'
            ]
            self.rcon.execute_batch(drop_commands)
            self.rcon.send_actionbar("💀 СВОБОДНОЕ ПАДЕНИЕ С ВЫСОТЫ! СПАСАЙСЯ!", "red")

        threading.Thread(target=_sleepwalker_watcher, daemon=True).start()


    def trigger_random_regular(self) -> tuple:
        """Picks a random trigger avoiding immediate repeats."""
        available = [t for t in self.regular_triggers if t[0] not in self.recent_triggers]
        if not available:
            available = self.regular_triggers

        chosen = random.choice(available)
        tid, title, handler = chosen

        self.recent_triggers.append(tid)
        if len(self.recent_triggers) > self.prevent_repeats:
            self.recent_triggers.pop(0)

        handler()
        return tid, title

    def trigger_boss(self) -> tuple:
        chosen = random.choice(self.boss_triggers)
        tid, title, handler = chosen
        handler()
        return tid, f"[БОСС] {title}"
