#
#  The python Minecraft Bot to rule them all.
#  Poggers!
#
#  (c) 2021 by Guido Appenzeller & Daniel Appenzeller
#

import javascript
from javascript import require, once, off
import time
import asyncio
import argparse

from lib.inventory import InventoryManager
from lib.movement import MovementManager
from lib.farming import FarmBot
from lib.mine import MineBot
from lib.build import BuildBot
from lib.chat import ChatBot
from lib.combat import CombatBot
from lib.gather import GatherBot
from src.bot import create_bot


#
# Main Bot Class
#
# Additional Methods are added via Mixin inheritance and are in the various modules
#

# import debugpy
# from debugpy import breakpoint
import os


# # def setup_debugpy(host="localhost", port=5678):

# import debugpy
# print("Setting up debugpy")
# debugpy.listen(5678)
# debugpy.wait_for_client()
# print("Debugpy setup complete")

class PyBot(ChatBot, FarmBot, MineBot, GatherBot, BuildBot, CombatBot, MovementManager, InventoryManager):

    def __init__(self,account):
        # This is the Mineflayer bot
        self.bot = None
        self.account = account
        self.callsign = self.account['user'][0:2]+":"
        self.debug_lvl = 3
        self.lastException = None

        self.stopActivity = False
        self.dangerType = None

        self.speedMode = False # Move fast 

        # Create bot using working wrapper
        options = {
            'host': self.account['host'],
            'port': self.account.get('port', 25565),
            'username': self.account['user'],
            'auth': 'microsoft' if 'password' in self.account else 'offline',
            'version': self.account['version'],
            'hideErrors': False,
        }
        if 'password' in self.account:
            options['password'] = self.account['password']

        self.bot = create_bot(options)

        # Access JavaScript objects through the bot wrapper
        self.mcData = self.bot.mc_data
        # Import Vec3 at module level like in working src/bot.py
        from src.bot import Vec3
        self.Vec3 = Vec3

        # TODO: Original JavaScript setup - may need to restore some functionality:
        # mineflayer = require('mineflayer')
        # bot = mineflayer.createBot({...})
        self.mcData = require("minecraft-data")(self.bot.bot.version)
        self.Block = require("prismarine-block")(self.bot.bot.version)
        self.Item = require("prismarine-item")(self.bot.bot.version)
        self.Vec3 = require("vec3").Vec3
        pathfinder = require("mineflayer-pathfinder")
        self.bot.bot.loadPlugin(pathfinder.pathfinder)
        movements = pathfinder.Movements(self.bot.bot, self.mcData)
        movements.blocksToAvoid.delete(self.mcData.blocksByName.wheat.id)
        self.bot.bot.pathfinder.setMovements(movements)

        # Initialize modules
        # Python makes this hard as __init__ of mixin classes is not called automatically

        print(f'pybot - a smart minecraft bot by Guido and Daniel Appenzeller.')

        classes = PyBot.mro()
        print('  modules: ', end='')
        for c in classes[1:]:
            c.__init__(self)
        print('.')

    # Debug levels:
    #   0=serious error
    #   1=important info or warning
    #   2=major actions or events
    #   3=each action, ~1/second
    #   4=spam me!
    #   5=everything

    def perror(self, message):
        print(f'*** error: {message}')

    def pexception(self, message,e):
        print(f'*** exception: {message}')
        if self.debug_lvl >= 4:
            print(e)
        else:
            with open("exception.debug", "w") as f:
                f.write("PyBit Minecraft Bot - Exception Dump")
                f.write(str(e))
                f.write("")
        self.lastException = e

    def pinfo(self, message):
        if self.debug_lvl > 0:
            print(message)

    def pdebug(self,message,lvl=4,end="\n"):
        if self.debug_lvl >= lvl:
            print(message,end=end)

    # Dummy functions, they get overriden by the GUI if we have it

    def mainloop(self):
        pass

    def refreshInventory(self):
        pass

    def refreshEquipment(self):
        pass

    def refreshStatus(self):
        pass

    def refreshActivity(self,txt):
        pass

    def bossPlayer(self):
        return self.account["master"]

#
# Run the bot.
# Note that we can run with or without UI
#

if __name__ == "__main__":

    parser = argparse.ArgumentParser(prog='python pybot.py')
    parser.add_argument('--nowindow', action='store_true', help='run in the background, i.e. without the Tk graphical UI')
    parser.add_argument('--verbose', '-v', action='count', default=0, help='verbosity from 1-5. Use as -v, -vv, -vvv etc.')
    parser.add_argument("--message", "-m", type=str, help="override master player name")
    args = parser.parse_args()
    argsd = vars(args)

    # Import credentials and server info, create the bot and log in
    from lib.account import account
    if  argsd["nowindow"]:
        pybot = PyBot(account.account)
    else:
        from lib.ui import PyBotWithUI
        pybot = PyBotWithUI(account.account)
    pybot.pdebug(f'Connected to server {account.account["host"]}.',0)
    if 'verbose' in argsd:
        pybot.debug_lvl = argsd['verbose']
    if "message" in argsd and argsd["message"]:
        account.account["master"] = argsd["message"]

    # Import list of known locations. Specific to the world.
    if account.locations:
        pybot.myLocations = account.locations

    #
    # Main Loop - We are driven by chat commands
    #

    # Report status
    # while not pybot.bot.health:
    #     time.sleep(1)

    # @pybot.bot.on_chat
    # def handle_chat(sender, message, this, *rest):
    #     pybot.handleChat(sender, message, this, *rest)

    @pybot.bot.on_spawn
    def handle_spawn():
        print("Bot spawned, waiting for chunks to load...")
        import asyncio
        import threading

        async def run_async():
            print("Mining thread started!")
            # Give a moment for debugger to attach if needed
            # import time
            # await pybot.bot
            

            # print("Waiting 10 seconds for debugger attachment...")
            # time.sleep(3)
            # breakpoint()
            await pybot.stripMine(3, 3, 5)

        def run_sync():
            # Optional: wait for debugger
            # debugpy.debug_this_thread()
            # breakpoint()
            asyncio.run(run_async())
        time.sleep(1)
        thread = threading.Thread(target=run_sync)
        thread.start()

    # @pybot.bot.on_health
    # def handle_health():
    #     pybot.healthCheck()

    # Initial healing - run in a separate thread since it may take time
    # def run_initial_heal():
    #     asyncio.run(pybot.healToFull())

    # import threading
    # heal_thread = threading.Thread(target=run_initial_heal)
    # heal_thread.start()

    if pybot.debug_lvl >= 4:
        pybot.printInventory()
    pybot.pdebug(f'Ready.',0)

    pybot.mainloop()
    # The spawn event
    # once(pybot.bot, 'login')
    # pybot.bot.chat('Bot '+pybot.bot.callsign+' joined.')
