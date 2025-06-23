#
#
#

# import tkinter as tk
# import tkinter.scrolledtext
# from tkinter import ttk, PhotoImage
import pygame
import sys
import time
import datetime
from functools import partial
from javascript import require, once, off
import threading
Vec3     = require('vec3').Vec3

from lib.pybot import PyBot
from lib.mine import MineBot
import lib.botlib as botlib


# Pygame UI Color and Font constants
COLOR_BLACK = (0, 0, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_BG = (212, 208, 200) # Classic UI background
COLOR_FRAME = (180, 180, 180)
COLOR_FRAME_BORDER = (120, 120, 120)
COLOR_TEXT = (0, 0, 0)
COLOR_BUTTON = (225, 225, 225)
COLOR_BUTTON_HOVER = (235, 235, 235)
COLOR_BUTTON_BORDER = (100, 100, 100)
COLOR_INPUT_BG = (255, 255, 255)
COLOR_INPUT_BORDER = (50, 50, 50)
COLOR_SEPARATOR = (150, 150, 150)

# Map tkinter color names to RGB tuples
TK_COLORS = {
    "brown": (139, 69, 19),
    "dark green": (0, 100, 0),
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
    "grey": (128, 128, 128),
    "light grey": (211, 211, 211),
    "dark blue": (0, 0, 139),
    "black": (0,0,0),
    "white": (255,255,255)
}

def get_color(name, default=COLOR_BLACK):
    if name is None:
        return None
    return TK_COLORS.get(name.lower(), default)

#            10             20
# 0  Status  |   MicroMap   |    Inventory
# 
#10 --------------------------------------
#
#    Commands
#
#20 --------------------------------------
#
#    Log
#

class LogWidget:
    """ A Pygame replacement for tk.scrolledtext.ScrolledText """
    max_log_lines = 200

    def __init__(self, rect, font):
        self.rect = rect
        self.font = font
        self.lines = []
        self.log_surface = pygame.Surface(self.rect.size)

    def log(self, txt):
        # Add new lines, handling multiline text
        for line in str(txt).split('\n'):
            self.lines.append(line)
        
        # Trim old lines
        if len(self.lines) > self.max_log_lines:
            self.lines = self.lines[-self.max_log_lines:]
        
        self.redraw_log()

    def redraw_log(self):
        self.log_surface.fill(COLOR_INPUT_BG)
        y = self.rect.height - self.font.get_height()
        # Draw lines from the bottom up
        for line in reversed(self.lines):
            if y < -self.font.get_height():
                break
            try:
                text_surf = self.font.render(line, True, COLOR_TEXT)
                self.log_surface.blit(text_surf, (5, y))
            except pygame.error as e:
                # Often happens with unsupported characters
                text_surf = self.font.render(f"Render Error: {e}", True, (255,0,0))
                self.log_surface.blit(text_surf, (5, y))
            y -= self.font.get_height()

    def draw(self, screen):
        screen.blit(self.log_surface, self.rect.topleft)
        pygame.draw.rect(screen, COLOR_INPUT_BORDER, self.rect, 1)

class InputBox:
    """ A Pygame replacement for ttk.Entry """
    def __init__(self, rect, font):
        self.rect = rect
        self.font = font
        self.text = ""
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                # Can be used to submit form, but here we just deactivate
                return "submit" # Signal to the main loop
            else:
                self.text += event.unicode
        return None

    def get_text(self):
        return self.text
    
    def set_text(self, text):
        self.text = text

    def draw(self, screen):
        pygame.draw.rect(screen, COLOR_INPUT_BG, self.rect)
        pygame.draw.rect(screen, COLOR_INPUT_BORDER, self.rect, 1)
        
        text_surface = self.font.render(self.text, True, COLOR_TEXT)
        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))
        
        if self.active:
            if time.time() - self.cursor_timer > 0.5:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = time.time()
            if self.cursor_visible:
                cursor_x = self.rect.x + 5 + text_surface.get_width()
                pygame.draw.line(screen, COLOR_TEXT, (cursor_x, self.rect.y + 5), (cursor_x, self.rect.y + self.rect.height - 5))

class PyBotWithUI(PyBot):

    # List means first is color (or None) second is icon

    block_icons = {
        "Air"           : None,
        "Cave Air"      : None,
        "Void Air"      : None,
        "Torch"         : None,
        "Wall Torch"    : None,
        "Redstone Torch": None,
        "Rail"          : [None,"#"],
        "Chest"         : ["brown","📦"],
        "Spruce Log"    : "brown",
        "Spruce Leaves" : "dark green",
        "Wheat Crops"   : ["green","🌾"],
        "Lava"          : "red",
        "Water"         : "blue", 
        "Bubble Column" : "blue",
        "Crafting Table": "brown",
    }

    inv_icons = {
        "Lapis Lazuli":"✨",
        "Raw Iron":"🪙",
        "Raw Copper":"🥉",
        "Raw Gold":"✨",
        "Redstone Dust":"🔴",
        "Diamond":"💎",
        "Emerald":"✨",
        "Wheat":"🌽",
        "Spruce Log":"🪵",
        "Spruce Sapling":"🌲",
        "Wheat Seeds":"🌿",
        "Coal":"🪨",
    }

    hand_icons = {
        "Wheat Seeds":"🌿",    
        "Stone Axe":"🪓",
        "Iron Axe":"🪓",
        "Diamond Axe":"🪓",
        "Stone Pickaxe":"⛏️",
        "Iron Pickaxe":"⛏️",
        "Diamond Pickaxe":"⛏️",
        "Cobblestone":"🪨",
        "Stone Brick":"🧱",
        "Bread":"🍞",
        "Stone Shovel":"⚒️",
        "Iron Shovel":"⚒️",
        "Diamond Shovel":"⚒️",
        "Stone Sword":"🗡️",
        "Iron Sword":"🗡️",
        "Diamond Sword":"🗡️",
    }

    button_mapping = [
        ["Come here"     , "come"],
        ["Follow me"     , "follow"],
        ["Farm Crops"    , "farm"],
        ["Chop Wood"     , "chop"],
        ["Deposit All"   , "deposit"],
        ["STOP!"         , "stop"],
        ["Mine Fast"     , "mine fast"],
        ["Mine 3x3"      , "mine 3x3"],
        ["Mine 5x5"      , "mine 5x5"],
        ["Mine Room"     , "mine room 5 5 3"],
        ["Mine Hall"     , "mine room 11 11 5"],
        ["Mine Shaft"    , "mineshaft 5 10"],
    ]

    def blockToIcon(self,name):
        if name in self.block_icons:
            return self.block_icons[name]
        else:
            return "grey"

    def blockToColor(self,name):
        if name in self.block_icons:
            l = self.block_icons[name]
            if type(l) == list:
                return l[0]
            else:
                return l
        else:
            return "grey"

    def perror(self, message):
        if hasattr(self, 'logFrame') and self.logFrame:
            self.logFrame.log(f'*** error: {message}')
        else:
            print(f'*** error: {message}')

    def pexception(self, message,e):
        if hasattr(self, 'logFrame') and self.logFrame:
            self.logFrame.log(f'*** exception: {message}')
            if self.debug_lvl >= 4:
                self.logFrame.log(str(e))
        else:
            print(f'*** exception: {message}')
            if self.debug_lvl >= 4:
                print(str(e))
        if not hasattr(self, 'logFrame') or not self.logFrame or self.debug_lvl < 4:
            with open("exception.debug", "w") as f:
                f.write("PyBit Minecraft Bot - Exception Dump")
                f.write(str(e))
                f.write("")
        self.lastException = e

    def pinfo(self, message):
        if self.debug_lvl > 0:
            if hasattr(self, 'logFrame') and self.logFrame:
                self.logFrame.log(message)
            else:
                print(message)

    def pdebug(self,message,lvl=4,end=""):
        if self.debug_lvl >= lvl:
            if hasattr(self, 'logFrame') and self.logFrame:
                self.logFrame.log(message)
            else:
                # Fallback to console during initialization
                print(message)

    def uiInventory(self, items):
        self.inv_uncommon_lines = []
        self.inv_common_lines = []

        if len(items) > 0:
            for i in items:
                if i not in self.inv_icons:
                    self.inv_uncommon_lines.append(f'{items[i]:>3} x {i}')
            for i in items:
                if i in self.inv_icons:
                    label = self.inv_icons[i]
                    self.inv_common_lines.append(f'{items[i]:>3} x {label}{i}')
        else:
            self.inv_uncommon_lines.append('    Inventory is Empty')


    def uiStatus(self, health, food, oxygen):
        self.status_bars = []
        
        if oxygen > 18:
            oxygen = 20

        fg_c, bg_c = botlib.colorHelper(health,20)
        self.status_bars.append({
            'text': f'{int(100*health/20):>3}%  Health',
            'fg': get_color(fg_c, COLOR_WHITE), 'bg': get_color(bg_c, COLOR_BLACK)
        })
        
        fg_c, bg_c = botlib.colorHelper(food,20)
        self.status_bars.append({
            'text': f'{int(100*food/20):>3}%  Food',
            'fg': get_color(fg_c, COLOR_WHITE), 'bg': get_color(bg_c, COLOR_BLACK)
        })

        fg_c, bg_c = botlib.colorHelper(oxygen,20)
        self.status_bars.append({
            'text': f'{int(100*oxygen/20):>3}%  Oxygen',
            'fg': get_color(fg_c, COLOR_WHITE), 'bg': get_color(bg_c, COLOR_BLACK)
        })

    def uiMap(self, blocks):
        self.map_data = blocks[0]

    def uiEquipment(self,item):
        if item in self.hand_icons:
            item = f'✋:  {self.hand_icons[item]} {item}'
        else:
            item = f'✋:  {item}'
        self.mainHandLabel_text = item

    def refreshMap(self):
        p = self.bot.entity.position

        blocks = []
        for x in range(0,13):
            new = []
            for z in range(0,13):
                new.append(0)
            blocks.append(new)

        for x in range(0,13):
            for z in range(0,13):
                v = Vec3(p.x+x-6,p.y+0.3,p.z+z-6)
                n = self.bot.blockAt(v).displayName
                blocks[x][z] = n

        self.uiMap([blocks])

    def refreshWorldStatus(self):

        t = self.bot.time.timeOfDay
        t = int(t)
        h = (int(t/1000)+6) % 24
        m = int( 60*(t % 1000)/1000)
        time_str = f'{h:02}:{m:02}'
        p = self.bot.entity.position
        pos_str = f'x: {int(p.x)}   y: {int(p.y)}   z: {int(p.z)}'
        
        self.placeLabel_text = f'  🧭  {pos_str}'
        self.connLabel_text = f'  🌐 {self.account["host"]}   {self.bot.player.ping} ms'
        
        if self.bot.time.isDay:
            self.timeLabel_text = f'  Time: 🌞 {time_str}'
            self.timeLabel_bg = get_color("light grey")
            self.timeLabel_fg = get_color("black")
        else:
            self.timeLabel_text = f'  Time: 🌙 {time_str}'
            self.timeLabel_bg = get_color("dark blue")
            self.timeLabel_fg = get_color("white")


    def refreshInventory(self):
        inventory = self.bot.inventory.items()
        iList = {}
        if inventory != []:
            for i in inventory:
                iname = i.displayName
                if iname not in iList:
                    iList[iname] = 0
                iList[iname] += i.count
        self.uiInventory(iList)

    def refreshEquipment(self):
        i_type, item = self.itemInHand()
        self.uiEquipment(item)
        pass

    def refreshStatus(self):
        o = self.bot.oxygenLevel
        if not o:
            o = 100
        self.uiStatus(self.bot.health, self.bot.food, o)
        pass

    def refreshActivity(self, txt):            
        if self.activity_major == False:
            status = f' ({self.activity_last_duration})'
        elif self.stopActivity:
            status = "🛑 Stop"
        else:
            status = str(datetime.timedelta(seconds=int(time.time()-self.activity_start)))
        self.activityTitleLabel_text = f'{self.activity_name} {status}'

        if txt:
            if isinstance(txt,str):
                lines = [txt]
            elif isinstance(txt,list):
                lines = txt
            else:
                return
            self.activityLines = lines[:6]


    def bossPlayer(self):
        return self.bossName.get_text()

    def refresherJob(self):
        # This runs in a thread, updating data. The main loop handles drawing.
        while self.running:
            try:
                self.refreshActivity(None)
                self.refreshWorldStatus()
                self.refreshStatus()
                self.refreshInventory()
                self.refreshMap()
            except Exception as e:
                self.perror(f"Exception in refresher thread: {e}")
            time.sleep(1)

    def do_command(self,cmd=None):
        # If cmd is None, it came from the entry box
        if cmd is None:
            cmd = self.cmdEntry.get_text()
            self.cmdEntry.set_text("")
        
        if cmd != "stop":
            if self.activity_major == True:
                self.pinfo("Cannot start new major activity while one is running.")
                return False
        self.handleCommand(cmd, self.bossPlayer())

    def _draw_frame(self, rect, text):
        """ Helper to draw a titled frame like ttk.LabelFrame """
        # Draw the main rect
        pygame.draw.rect(self.screen, COLOR_FRAME, rect)
        pygame.draw.rect(self.screen, COLOR_FRAME_BORDER, rect, 1)

        # Draw the title with a background-colored rectangle behind it
        text_surf = self.font.render(f" {text} ", True, COLOR_TEXT)
        text_rect = text_surf.get_rect(topleft=(rect.x + 8, rect.y - self.font.get_height() // 2))
        pygame.draw.rect(self.screen, COLOR_BG, text_rect)
        self.screen.blit(text_surf, text_rect)

    def _draw_ui(self):
        """ Main drawing function, called every frame """
        self.screen.fill(COLOR_BG)
        mouse_pos = pygame.mouse.get_pos()

        # World Status
        self._draw_frame(self.worldUI_rect, 'World Status')
        if hasattr(self, 'timeLabel_bg'):
             pygame.draw.rect(self.screen, self.timeLabel_bg, (25, 20, 190, self.font.get_height()))
             self.screen.blit(self.font.render(self.timeLabel_text, True, self.timeLabel_fg), (30, 20))
        if hasattr(self, 'placeLabel_text'):
             self.screen.blit(self.font.render(self.placeLabel_text, True, COLOR_TEXT), (30, 25 + self.font.get_height()))
        if hasattr(self, 'connLabel_text'):
             self.screen.blit(self.font.render(self.connLabel_text, True, COLOR_TEXT), (30, 30 + 2*self.font.get_height()))

        # Player Status
        self._draw_frame(self.statusUI_rect, 'Player Status')
        if hasattr(self, 'status_bars'):
            for i, bar in enumerate(self.status_bars):
                bar_rect = pygame.Rect(25, 130 + i * (self.font.get_height() + 4), 190, self.font.get_height()+2)
                pygame.draw.rect(self.screen, bar['bg'], bar_rect)
                self.screen.blit(self.font.render(bar['text'], True, bar['fg']), (bar_rect.x + 5, bar_rect.y))

        # Equipment
        self._draw_frame(self.equipmentUI_rect, 'Equipment')
        if hasattr(self, 'mainHandLabel_text'):
            self.screen.blit(self.emoji_font.render(self.mainHandLabel_text, True, COLOR_TEXT), (30, 245))

        # Area Map
        self._draw_frame(self.areaUI_rect, 'Area Map')
        map_surface_rect = pygame.Rect(240, 20, 200, 200)
        pygame.draw.rect(self.screen, get_color("black"), map_surface_rect)
        if hasattr(self, 'map_data'):
            cell_size = 14
            map_offset_x, map_offset_y = map_surface_rect.left + 12, map_surface_rect.top + 12
            for x in range(13):
                for z in range(13):
                    icon = self.blockToIcon(self.map_data[x][z])
                    if icon:
                        cell_rect = pygame.Rect(map_offset_x + x * cell_size, map_offset_y + z * cell_size, cell_size, cell_size)
                        if type(icon) is not list:
                            color = get_color(icon, "grey")
                            if color: pygame.draw.rect(self.screen, color, cell_rect)
                        else:
                            self.screen.blit(self.emoji_font.render(icon[1], True, COLOR_TEXT), cell_rect.center)
            self.screen.blit(self.emoji_font.render('🤖', True, COLOR_TEXT), (map_surface_rect.centerx-8, map_surface_rect.centery-8))

        # Activity
        self._draw_frame(self.activityUI_rect, 'Activity')
        if hasattr(self, 'activityTitleLabel_text'):
            self.screen.blit(self.emoji_font.render(self.activityTitleLabel_text, True, COLOR_TEXT), (250, 245))
        if hasattr(self, 'activityLines'):
            for i, line in enumerate(self.activityLines):
                self.screen.blit(self.font.render(line, True, COLOR_TEXT), (250, 265 + i * self.font.get_height()))
        
        # Inventory
        self._draw_frame(self.invUI_rect, 'Inventory')
        y_offset = 25
        if hasattr(self, 'inv_uncommon_lines'):
            for line in self.inv_uncommon_lines:
                self.screen.blit(self.font.render(line, True, COLOR_TEXT), (465, y_offset))
                y_offset += self.font.get_height()
            if self.inv_uncommon_lines and self.inv_common_lines:
                 pygame.draw.line(self.screen, COLOR_SEPARATOR, (470, y_offset+2), (650, y_offset+2), 1)
                 y_offset += 10
            for line in self.inv_common_lines:
                 self.screen.blit(self.emoji_font.render(line, True, COLOR_TEXT), (465, y_offset))
                 y_offset += self.font.get_height()
                 

        # Separators
        pygame.draw.line(self.screen, COLOR_SEPARATOR, (0, 430), (680, 430), 2)
        pygame.draw.line(self.screen, COLOR_SEPARATOR, (0, 550), (680, 550), 2)

        # Command Buttons
        for btn in self.command_buttons:
            rect, text, _ = btn
            color = COLOR_BUTTON_HOVER if rect.collidepoint(mouse_pos) else COLOR_BUTTON
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, COLOR_BUTTON_BORDER, rect, 1)
            text_surf = self.font.render(text, True, COLOR_TEXT)
            text_rect = text_surf.get_rect(center=rect.center)
            self.screen.blit(text_surf, text_rect)
        
        # Command Entry
        self.screen.blit(self.font.render("Command:", True, COLOR_TEXT), (15, 520))
        self.cmdEntry.draw(self.screen)
        
        self.doit_button_rect, _, _ = self.doit_button
        color = COLOR_BUTTON_HOVER if self.doit_button_rect.collidepoint(mouse_pos) else COLOR_BUTTON
        pygame.draw.rect(self.screen, color, self.doit_button_rect)
        pygame.draw.rect(self.screen, COLOR_BUTTON_BORDER, self.doit_button_rect, 1)
        text_surf = self.font.render("Do it!", True, COLOR_TEXT)
        self.screen.blit(text_surf, text_surf.get_rect(center=self.doit_button_rect.center))
        
        self.screen.blit(self.font.render("Boss:", True, COLOR_TEXT), (470, 520))
        self.bossName.draw(self.screen)

        # Log
        self.screen.blit(self.font.render("Activity Log", True, COLOR_TEXT), (20, 560))
        self.logFrame.draw(self.screen)

        pygame.display.flip()


    def initUI(self):
        pygame.init()
        self.screen = pygame.display.set_mode((680, 800))
        pygame.display.set_caption("PyBot - The friendly Minecraft Bot")
        
        # Fonts
        try:
            # Use a font that supports emojis, DejaVu is a good candidate
            self.emoji_font = pygame.font.SysFont("DejaVu Sans", 14)
        except:
            print("Emoji font not found, using default. Emojis may not render.")
            self.emoji_font = pygame.font.SysFont(None, 16)
        self.font = pygame.font.SysFont("monospace", 13)

        # UI Element Rects (from original .place calls)
        self.worldUI_rect = pygame.Rect(20, 10, 200, 100)
        self.statusUI_rect = pygame.Rect(20, 120, 200, 100)
        self.equipmentUI_rect = pygame.Rect(20, 230, 200, 180)
        self.areaUI_rect = pygame.Rect(240, 10, 200, 200)
        self.activityUI_rect = pygame.Rect(240, 230, 200, 180)
        self.invUI_rect = pygame.Rect(460, 10, 200, 400)
        
        # Command Buttons
        self.command_buttons = []
        btn_width, btn_height = 106, 30
        start_x, start_y = 10, 440
        for i, (text, cmd) in enumerate(self.button_mapping):
            row, col = divmod(i, 6)
            rect = pygame.Rect(start_x + col * (btn_width + 5), start_y + row * (btn_height + 5), btn_width, btn_height)
            # Use a lambda with a default argument to capture the current value of cmd
            callback = lambda c=cmd: self.do_command(c)
            self.command_buttons.append((rect, text, callback))

        # Command Entry & Boss Entry
        self.cmdEntry = InputBox(pygame.Rect(90, 515, 250, 25), self.font)
        self.doit_button = (pygame.Rect(350, 515, 60, 25), "Do it!", self.do_command)
        
        self.bossName = InputBox(pygame.Rect(515, 515, 130, 25), self.font)
        if hasattr(self, 'account'):
            self.bossName.set_text(self.account["master"])

        # Log Widget
        self.logFrame = LogWidget(pygame.Rect(0, 580, 680, 220), self.font)

        # Initialize data stores for UI elements
        self.activityLines = [""]*6
        self.mainHandLabel_text = ""
        self.uiInventory({})
        self.uiStatus(0,0,0)
        self.uiMap([[["Air"]*13]*13])
        self.refreshActivity("Idle")
        self.refreshWorldStatus()


    def mainloop(self):
        self.running = True
        self.clock = pygame.time.Clock()
        
        def run_refresher():
            self.refresherJob()
        
        refresher_thread = threading.Thread(target=run_refresher, daemon=True)
        refresher_thread.start()

        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Pass events to input boxes
                if self.cmdEntry.handle_event(event) == "submit":
                    self.do_command()
                self.bossName.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Check command buttons
                    for rect, text, callback in self.command_buttons:
                        if rect.collidepoint(event.pos):
                            callback()
                            break
                    # Check "Do it!" button
                    if self.doit_button[0].collidepoint(event.pos):
                        self.doit_button[2]()

            self._draw_ui()
            self.clock.tick(30) # Limit frame rate
        
        pygame.quit()
        # We should also signal the bot to disconnect and threads to stop gracefully
        if hasattr(self, 'bot'): self.bot.quit()
        sys.exit()

    def __init__(self, account):
        super().__init__(account)
        self.initUI()

if __name__ == "__main__":
    # Run in test mode
    print("UI Test - Part of PyBot, the friendly Minecraft Bot.")
    # To run in test mode, we bypass the need for an account and bot connection
    # by creating the class instance without calling its full __init__
    pybot = PyBotWithUI.__new__(PyBotWithUI)
    pybot.debug_lvl = 4 # for logging
    pybot.initUI()
    pybot.running = True

    # --- Populate with test data ---
    items = {item[0]: (i+1)*5 for i, item in enumerate(MineBot.miningEquipList)}
    pybot.uiInventory(items)
    pybot.uiStatus(20,15,10)
    blocks = [[["grey"]*13 for _ in range(13)]]
    blocks[0][6][5] = "Air"
    blocks[0][6][6] = "Lava"
    blocks[0][6][7] = "Water"
    blocks[0][5][6] = "Spruce Log"
    pybot.uiMap(blocks)
    pybot.uiEquipment("Stone Pickaxe")
    
    # Fake activity/world status
    pybot.activityTitleLabel_text = "Testing Mode"
    pybot.activityLines = ["Test1", "Test2", "Test3", "Line 4", "Line 5", "Line 6"]
    pybot.timeLabel_text = "  Time: 🌞 12:00"
    pybot.timeLabel_bg = get_color("light grey")
    pybot.timeLabel_fg = get_color("black")
    pybot.placeLabel_text = "  🧭 x: 100 y: 64 z: -200"
    pybot.connLabel_text = "  🌐 localhost   20 ms"
    pybot.bossName.set_text("Player")

    # The main loop now handles updates, so the old while loop is not needed.
    # We can simulate log messages for testing.
    a = 1
    log_timer = time.time()

    # Modified test mainloop
    pybot.clock = pygame.time.Clock()
    while pybot.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pybot.running = False
            
            # Simplified event handling for test mode
            if pybot.cmdEntry.handle_event(event) == "submit":
                pybot.logFrame.log(f"CMD: {pybot.cmdEntry.get_text()}")
                pybot.cmdEntry.set_text("")
            pybot.bossName.handle_event(event)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for rect, text, _ in pybot.command_buttons:
                    if rect.collidepoint(event.pos):
                        pybot.logFrame.log(f"Clicked: {text}")
                        break
                if pybot.doit_button[0].collidepoint(event.pos):
                    pybot.logFrame.log(f"CMD: {pybot.cmdEntry.get_text()}")
                    pybot.cmdEntry.set_text("")


        if time.time() - log_timer > 0.1:
            pybot.logFrame.log(f'{a} test and {a}*{a} = {a*a}')
            a += 1
            log_timer = time.time()
        
        # In test mode, we might need to manually update some things
        pybot.uiStatus( (a % 20)+1, 20-((a//2) % 20), 20)
        
        pybot._draw_ui()
        pybot.clock.tick(30)
    
    pygame.quit()
    sys.exit()