"""
PyMineflayer - A condensed, single-file, comprehensive Python wrapper for the Mineflayer bot API.
This file provides a unified Bot class that covers the entire Mineflayer API surface.

Usage:
    from pymineflayer import create_bot, Vec3
    
    bot = create_bot({
        'host': 'localhost',
        'port': 25565,
        'username': 'PyBot'
    })

    @bot.on_login
    def handle_login():
        bot.chat("Hello, world! I'm a Python bot.")

    @bot.on_chat
    def handle_chat(username, message, *args):
        if username == bot.username: return
        if 'pos' in message:
            bot.chat(f"I am at {bot.entity.position}")

Full API Documentation: https://github.com/PrismarineJS/mineflayer/blob/master/docs/api.md
"""

from typing import Optional, Dict, Any, List, Union, Callable
from javascript import require, On

# Expose commonly used JS classes
Vec3 = require('vec3').Vec3
# Location = require('prismarine-viewer').mineflayer.Location
from collections import defaultdict

class Bot:
    """A unified, flattened interface for all Mineflayer bot functionality."""

    def __init__(self, options: Dict[str, Any]):
        """Creates a new Mineflayer bot instance."""
        self.bot = require('mineflayer').createBot(options)
        self.mc_data = require('minecraft-data')(self.bot.version)
        blocksByName = self.bot.registry.blocksByName
        # blocksByName = iter(blocksByName)
        # print(dir(blocksByName))
        keys = iter(blocksByName)
        bbn = {k: self.bot.registry.blocksByName[k] for k in keys}
        displayname_to_id = defaultdict(list)
        for k,v in bbn.items():
            displayname_to_id[v.displayName].append(v.id)
        self.displayname_to_id = displayname_to_id
        # self.displayname_to_id = {v.displayName: v.id }
        # self.items = {v.displayName:v for k,v in self.bot.registry.itemsByName.items()}

    # ========================================
    # CORE & API ACCESS
    # ========================================
    @property
    def js_bot(self):
        """Direct access to the underlying JavaScript bot instance."""
        return self.bot

    @property
    def registry(self):
        """Instance of minecraft-data used by the bot."""
        return self.bot.registry

    # ========================================
    # PROPERTIES
    # ========================================
    @property
    def world(self):
        return self.bot.world

    @property
    def entity(self):
        return self.bot.entity

    @property
    def entities(self) -> Dict[int, Any]:
        return self.bot.entities

    @property
    def username(self) -> str:
        return self.bot.username

    @property
    def spawn_point(self):
        return self.bot.spawnPoint

    @property
    def held_item(self):
        return self.bot.heldItem

    @property
    def using_held_item(self) -> bool:
        return self.bot.usingHeldItem

    @property
    def game(self):
        return self.bot.game

    @property
    def physics_enabled(self) -> bool:
        return getattr(self.bot, "physicsEnabled", True)

    @physics_enabled.setter
    def physics_enabled(self, value: bool):
        self.bot.physicsEnabled = value

    @property
    def player(self):
        return self.bot.player

    @property
    def players(self) -> Dict[str, Any]:
        return self.bot.players

    @property
    def tablist(self):
        return self.bot.tablist

    @property
    def is_raining(self) -> bool:
        return self.bot.isRaining

    @property
    def rain_state(self) -> float:
        return self.bot.rainState

    @property
    def thunder_state(self) -> float:
        return self.bot.thunderState

    @property
    def chat_patterns(self) -> List[Dict]:
        return self.bot.chatPatterns

    @property
    def settings(self):
        return self.bot.settings

    @property
    def experience(self):
        return self.bot.experience

    @property
    def health(self) -> float:
        return self.bot.health

    @property
    def food(self) -> float:
        return self.bot.food

    @property
    def food_saturation(self) -> float:
        return self.bot.foodSaturation

    @property
    def oxygen_level(self) -> int:
        return self.bot.oxygenLevel

    @property
    def physics(self):
        return self.bot.physics

    @property
    def firework_rocket_duration(self) -> int:
        return self.bot.fireworkRocketDuration

    @property
    def time(self):
        return self.bot.time

    @property
    def quick_bar_slot(self) -> int:
        return self.bot.quickBarSlot

    @property
    def inventory(self):
        return self.bot.inventory

    @property
    def target_dig_block(self):
        return self.bot.targetDigBlock

    @property
    def is_sleeping(self) -> bool:
        return self.bot.isSleeping

    @property
    def scoreboards(self) -> Dict:
        return self.bot.scoreboards

    @property
    def scoreboard(self) -> Dict:
        return self.bot.scoreboard

    @property
    def teams(self) -> Dict:
        return self.bot.teams

    @property
    def team_map(self) -> Dict:
        return self.bot.teamMap

    @property
    def control_state(self) -> Dict[str, bool]:
        return self.bot.controlState

    # ========================================
    # EVENT HANDLING
    # ========================================
    def on(self, event: str, callback: Callable):
        """Generic event handler registration. Can be used as a decorator."""
        @On(self.bot, event)
        def handler(this, *args):
            callback(*args)
        return handler

    def once(self, event: str, callback: Callable):
        """Generic event handler that fires only once. Can be used as a decorator."""
        @On(self.bot, event, once=True)
        def handler(this, *args):
            callback(*args)
        return handler

    # --- Specific Event Handlers (for decorator usage and clarity) ---
    def on_chat(self, cb): return self.on('chat', cb)
    def on_whisper(self, cb): return self.on('whisper', cb)
    def on_action_bar(self, cb): return self.on('actionBar', cb)
    def on_message(self, cb): return self.on('message', cb)
    def on_messagestr(self, cb): return self.on('messagestr', cb)
    def on_inject_allowed(self, cb): return self.on('inject_allowed', lambda: cb())
    def on_login(self, cb): return self.on('login', lambda: cb())
    def on_spawn(self, cb): return self.on('spawn', lambda: cb())
    def on_respawn(self, cb): return self.on('respawn', lambda: cb())
    def on_game(self, cb): return self.on('game', lambda: cb())
    def on_resource_pack(self, cb): return self.on('resourcePack', cb)
    def on_title(self, cb): return self.on('title', cb)
    def on_title_times(self, cb): return self.on('title_times', cb)
    def on_title_clear(self, cb): return self.on('title_clear', lambda: cb())
    def on_rain(self, cb): return self.on('rain', lambda: cb())
    def on_weather_update(self, cb): return self.on('weatherUpdate', lambda: cb())
    def on_time(self, cb): return self.on('time', lambda: cb())
    def on_kicked(self, cb): return self.on('kicked', cb)
    def on_end(self, cb): return self.on('end', cb)
    def on_error(self, cb): return self.on('error', cb)
    def on_spawn_reset(self, cb): return self.on('spawnReset', lambda: cb())
    def on_death(self, cb): return self.on('death', lambda: cb())
    def on_health(self, cb): return self.on('health', lambda: cb())
    def on_breath(self, cb): return self.on('breath', lambda: cb())
    def on_entity_attributes(self, cb): return self.on('entityAttributes', cb)
    def on_entity_swing_arm(self, cb): return self.on('entitySwingArm', cb)
    def on_entity_hurt(self, cb): return self.on('entityHurt', cb)
    def on_entity_dead(self, cb): return self.on('entityDead', cb)
    def on_entity_taming(self, cb): return self.on('entityTaming', cb)
    def on_entity_tamed(self, cb): return self.on('entityTamed', cb)
    def on_entity_shaking_off_water(self, cb): return self.on('entityShakingOffWater', cb)
    def on_entity_eating_grass(self, cb): return self.on('entityEatingGrass', cb)
    def on_entity_hand_swap(self, cb): return self.on('entityHandSwap', cb)
    def on_entity_wake(self, cb): return self.on('entityWake', cb)
    def on_entity_eat(self, cb): return self.on('entityEat', cb)
    def on_entity_critical_effect(self, cb): return self.on('entityCriticalEffect', cb)
    def on_entity_magic_critical_effect(self, cb): return self.on('entityMagicCriticalEffect', cb)
    def on_entity_crouch(self, cb): return self.on('entityCrouch', cb)
    def on_entity_uncrouch(self, cb): return self.on('entityUncrouch', cb)
    def on_entity_equip(self, cb): return self.on('entityEquip', cb)
    def on_entity_sleep(self, cb): return self.on('entitySleep', cb)
    def on_entity_spawn(self, cb): return self.on('entitySpawn', cb)
    def on_entity_elytra_flew(self, cb): return self.on('entityElytraFlew', cb)
    def on_item_drop(self, cb): return self.on('itemDrop', cb)
    def on_player_collect(self, cb): return self.on('playerCollect', cb)
    def on_entity_gone(self, cb): return self.on('entityGone', cb)
    def on_entity_moved(self, cb): return self.on('entityMoved', cb)
    def on_entity_detach(self, cb): return self.on('entityDetach', cb)
    def on_entity_attach(self, cb): return self.on('entityAttach', cb)
    def on_entity_update(self, cb): return self.on('entityUpdate', cb)
    def on_entity_effect(self, cb): return self.on('entityEffect', cb)
    def on_entity_effect_end(self, cb): return self.on('entityEffectEnd', cb)
    def on_player_joined(self, cb): return self.on('playerJoined', cb)
    def on_player_updated(self, cb): return self.on('playerUpdated', cb)
    def on_player_left(self, cb): return self.on('playerLeft', cb)
    def on_block_update(self, cb, at_pos=None): return self.on(f'blockUpdate{f":{at_pos}" if at_pos else ""}', cb)
    def on_block_placed(self, cb): return self.on('blockPlaced', cb)
    def on_chunk_column_load(self, cb): return self.on('chunkColumnLoad', cb)
    def on_chunk_column_unload(self, cb): return self.on('chunkColumnUnload', cb)
    def on_sound_effect_heard(self, cb): return self.on('soundEffectHeard', cb)
    def on_hardcoded_sound_effect_heard(self, cb): return self.on('hardcodedSoundEffectHeard', cb)
    def on_note_heard(self, cb): return self.on('noteHeard', cb)
    def on_piston_move(self, cb): return self.on('pistonMove', cb)
    def on_chest_lid_move(self, cb): return self.on('chestLidMove', cb)
    def on_block_break_progress_observed(self, cb): return self.on('blockBreakProgressObserved', cb)
    def on_block_break_progress_end(self, cb): return self.on('blockBreakProgressEnd', cb)
    def on_digging_completed(self, cb): return self.on('diggingCompleted', cb)
    def on_digging_aborted(self, cb): return self.on('diggingAborted', cb)
    def on_used_firework(self, cb): return self.on('usedFirework', cb)
    def on_move(self, cb): return self.on('move', lambda: cb())
    def on_forced_move(self, cb): return self.on('forcedMove', lambda: cb())
    def on_mount(self, cb): return self.on('mount', lambda: cb())
    def on_dismount(self, cb): return self.on('dismount', cb)
    def on_window_open(self, cb): return self.on('windowOpen', cb)
    def on_window_close(self, cb): return self.on('windowClose', cb)
    def on_sleep(self, cb): return self.on('sleep', lambda: cb())
    def on_wake(self, cb): return self.on('wake', lambda: cb())
    def on_experience(self, cb): return self.on('experience', lambda: cb())
    def on_scoreboard_created(self, cb): return self.on('scoreboardCreated', cb)
    def on_scoreboard_deleted(self, cb): return self.on('scoreboardDeleted', cb)
    def on_scoreboard_title_changed(self, cb): return self.on('scoreboardTitleChanged', cb)
    def on_score_updated(self, cb): return self.on('scoreUpdated', cb)
    def on_score_removed(self, cb): return self.on('scoreRemoved', cb)
    def on_scoreboard_position(self, cb): return self.on('scoreboardPosition', cb)
    def on_team_created(self, cb): return self.on('teamCreated', cb)
    def on_team_removed(self, cb): return self.on('teamRemoved', cb)
    def on_team_updated(self, cb): return self.on('teamUpdated', cb)
    def on_team_member_added(self, cb): return self.on('teamMemberAdded', cb)
    def on_team_member_removed(self, cb): return self.on('teamMemberRemoved', cb)
    def on_boss_bar_created(self, cb): return self.on('bossBarCreated', cb)
    def on_boss_bar_deleted(self, cb): return self.on('bossBarDeleted', cb)
    def on_boss_bar_updated(self, cb): return self.on('bossBarUpdated', cb)
    def on_held_item_changed(self, cb): return self.on('heldItemChanged', cb)
    def on_physics_tick(self, cb): return self.on('physicsTick', lambda: cb())
    def on_chat_pattern(self, name, cb): return self.on(f'chat:{name}', cb)
    def on_particle(self, cb): return self.on('particle', cb)

    # ========================================
    # FUNCTIONS (World Query)
    # ========================================
    def block_at(self, point, extra_infos=True): return self.bot.blockAt(point, extra_infos)
    async def wait_for_chunks_to_load(self): return await self.bot.waitForChunksToLoad()
    def block_in_sight(self, max_steps=256, vec_len=5/16): return self.bot.blockInSight(max_steps, vec_len)
    def block_at_cursor(self, max_dist=256): return self.bot.blockAtCursor(max_dist)
    def entity_at_cursor(self, max_dist=3.5): return self.bot.entityAtCursor(max_dist)
    def block_at_entity_cursor(self, entity=None, max_dist=256): return self.bot.blockAtEntityCursor(entity or self.entity, max_dist)
    def can_see_block(self, block) -> bool: return self.bot.canSeeBlock(block)
    def find_blocks(self, options: Dict): return self.bot.findBlocks(options)
    def find_block(self, options: Dict): return self.bot.findBlock(options)
    def can_dig_block(self, block) -> bool: return self.bot.canDigBlock(block)
    def recipes_for(self, *args) -> List: return self.bot.recipesFor(*args)
    def recipes_all(self, *args) -> List: return self.bot.recipesAll(*args)
    def nearest_entity(self, match: Optional[Callable] = None): return self.bot.nearestEntity(match if match is not None else lambda e: True)

    # ========================================
    # METHODS (Bot Actions)
    # ========================================
    def end(self, reason: Optional[str] = None): return self.bot.end(reason) if reason else self.bot.end()
    def quit(self, reason: str = 'disconnect.quitting'): return self.bot.quit(reason)
    async def tab_complete(self, s, *args): return await self.bot.tabComplete(s, *args)
    def chat(self, msg: str): self.bot.chat(msg)
    def whisper(self, user: str, msg: str): self.bot.whisper(user, msg)
    def chat_add_pattern(self, pattern, chat_type, desc=''): self.bot.chatAddPattern(pattern, chat_type, desc)
    def add_chat_pattern(self, name, pattern, opts=None): return self.bot.addChatPattern(name, pattern, opts or {})
    def add_chat_pattern_set(self, name, patterns, opts=None): return self.bot.addChatPatternSet(name, patterns, opts or {})
    def remove_chat_pattern(self, name: Union[str, int]): self.bot.removeChatPattern(name)
    async def await_message(self, *args): return await self.bot.awaitMessage(*args)
    def set_settings(self, options: Dict): self.bot.setSettings(options)
    def load_plugin(self, plugin: Callable): self.bot.loadPlugin(plugin)
    def load_plugins(self, plugins: List[Callable]): self.bot.loadPlugins(plugins)
    def has_plugin(self, plugin: Callable) -> bool: return self.bot.hasPlugin(plugin)
    async def sleep(self, bed_block): return await self.bot.sleep(bed_block)
    def is_a_bed(self, block) -> bool: return self.bot.isABed(block)
    async def wake(self): return await self.bot.wake()
    def set_control_state(self, control, state): self.bot.setControlState(control, state)
    def get_control_state(self, control) -> bool: return self.bot.getControlState(control)
    def clear_control_states(self): self.bot.clearControlStates()
    def get_explosion_damages(self, entity, pos, radius, raw=False): return self.bot.getExplosionDamages(entity, pos, radius, raw)
    async def look_at(self, point, force=False): return await self.bot.lookAt(point, force)
    async def look(self, yaw, pitch, force=False): return await self.bot.look(yaw, pitch, force)
    async def update_sign(self, block, text, back=False): return await self.bot.updateSign(block, text, back)
    async def equip(self, item, dest): 
        try:
            self.bot.equip(item, dest)
            return 1
        except:
            return 0
    async def unequip(self, dest): return await self.bot.unequip(dest)
    async def toss_stack(self, item): return await self.bot.tossStack(item)
    async def toss(self, item_type, meta=None, count=None): return await self.bot.toss(item_type, meta, count)
    async def elytra_fly(self): return await self.bot.elytraFly()
    async def dig(self, block, force_look=True, dig_face='auto'): 
        try:
            self.bot.dig(block, force_look, dig_face)
            return 1
        except:
            return 0
    def stop_digging(self): self.bot.stopDigging()
    def dig_time(self, block) -> int: return self.bot.digTime(block)
    def accept_resource_pack(self): self.bot.acceptResourcePack()
    def deny_resource_pack(self): self.bot.denyResourcePack()
    async def place_block(self, ref_block, face_vec): return await self.bot.placeBlock(ref_block, face_vec)
    async def place_entity(self, ref_block, face_vec): return await self.bot.placeEntity(ref_block, face_vec)
    async def activate_block(self, block, direction=None, c_pos=None): return await self.bot.activateBlock(block, direction, c_pos)
    async def activate_entity(self, entity): return await self.bot.activateEntity(entity)
    async def activate_entity_at(self, entity, pos): return await self.bot.activateEntityAt(entity, pos)
    async def consume(self): return await self.bot.consume()
    async def fish(self): return await self.bot.fish()
    def activate_item(self, off_hand=False): self.bot.activateItem(off_hand)
    def deactivate_item(self): self.bot.deactivateItem()
    def use_on(self, target_entity): self.bot.useOn(target_entity)
    def attack(self, entity, swing=True): self.bot.attack(entity, swing)
    def swing_arm(self, hand='right', show_hand=True): self.bot.swingArm(hand, show_hand)
    def mount(self, entity): self.bot.mount(entity)
    def dismount(self): self.bot.dismount()
    def move_vehicle(self, left, forward): self.bot.moveVehicle(left, forward)
    def set_quick_bar_slot(self, slot: int): self.bot.setQuickBarSlot(slot)
    async def craft(self, recipe, count=1, table=None): return await self.bot.craft(recipe, count, table)
    async def write_book(self, slot: int, pages: List[str]): return await self.bot.writeBook(slot, pages)
    async def open_container(self, container, *args): return await self.bot.openContainer(container, *args)
    async def open_chest(self, chest, *args): return await self.bot.openChest(chest, *args)
    async def open_furnace(self, furnace_block): return await self.bot.openFurnace(furnace_block)
    async def open_dispenser(self, dispenser_block): return await self.bot.openDispenser(dispenser_block)
    async def open_enchantment_table(self, table_block): return await self.bot.openEnchantmentTable(table_block)
    async def open_anvil(self, anvil_block): return await self.bot.openAnvil(anvil_block)
    async def open_villager(self, villager): return await self.bot.openVillager(villager)
    async def trade(self, villager, trade_idx, times=1): return await self.bot.trade(villager, trade_idx, times)
    def set_command_block(self, pos, command, opts=None): self.bot.setCommandBlock(pos, command, opts or {})
    def support_feature(self, name: str) -> bool: return self.bot.supportFeature(name)
    async def wait_for_ticks(self, ticks: int): return await self.bot.waitForTicks(ticks)
    def respawn(self): self.bot.respawn()

    # ========================================
    # LOWER LEVEL INVENTORY METHODS
    # ========================================
    def simple_click_left(self, slot: int): self.bot.simpleClick.leftMouse(slot)
    def simple_click_right(self, slot: int): self.bot.simpleClick.rightMouse(slot)
    async def click_window(self, slot, mouse_button, mode): return await self.bot.clickWindow(slot, mouse_button, mode)
    async def put_selected_item_range(self, start, end, window, slot): return await self.bot.putSelectedItemRange(start, end, window, slot)
    async def put_away(self, slot: int): return await self.bot.putAway(slot)
    def close_window(self, window): self.bot.closeWindow(window)
    async def transfer(self, options: Dict): return await self.bot.transfer(options)
    async def open_block(self, block, *args): return await self.bot.openBlock(block, *args)
    async def open_entity(self, entity): return await self.bot.openEntity(entity)
    async def move_slot_item(self, source_slot, dest_slot): return await self.bot.moveSlotItem(source_slot, dest_slot)
    def update_held_item(self): self.bot.updateHeldItem()
    def get_equipment_dest_slot(self, dest: str) -> int: return self.bot.getEquipmentDestSlot(dest)

    # ========================================
    # CREATIVE MODE
    # ========================================
    @property
    def creative(self):
        """Provides access to the `bot.creative` object for creative-only actions."""
        return self.bot.creative

    async def set_inventory_slot(self, slot: int, item): return await self.creative.setInventorySlot(slot, item)
    async def clear_slot(self, slot: int): return await self.creative.clearSlot(slot)
    async def clear_inventory(self): return await self.creative.clearInventory()
    async def fly_to(self, dest): return await self.creative.flyTo(dest)
    def start_flying(self): self.creative.startFlying()
    def stop_flying(self): self.creative.stopFlying()


def create_bot(options: Dict[str, Any]) -> Bot:
    """
    Creates and returns a new Bot instance. Main entry point for PyMineflayer.
    Args:
        options: Dictionary with bot configuration like host, port, username.
    Returns: An instance of the unified Bot class with all Mineflayer functionality.
    """
    return Bot(options)
