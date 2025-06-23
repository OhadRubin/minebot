#
# Misc chat functions
#

import time
import datetime
import lib.botlib as botlib
import asyncio
import threading

from javascript import require, once, off
pathfinder = require('mineflayer-pathfinder')

class ChatBot:

    stopActivity = True
    activity_start = 0
    activity_name = "None"
    activity_major = False
    activity_last_duration = 0

    def __init__(self):
        print('chat ', end='')

        # Command : [function, name, major activity flag, min_arguments]

        self.commandList = {
                "analyze":      [self.analyzeBuild,             "Analyze building",     False, 0],
                "build":        [self.doBuild,                  "Build a blueprint",    True,  1],                
                "chop":         [self.chopWood,                 "Chop wood",            True,  0],                
                "deposit":      [self.depositToChest,           "Deposit all in chest", False, 0],
                "eat":          [self.eatFood,                  "Eat Something",        False, 0],
                "farm":         [self.doFarming,                "Farming",              True , 0],
                "hello":        [self.sayHello,                 "Say Hello",            False, 0],
                "inventory":    [self.printInventory,           "List Inventory",       False, 0],
                "mine":         [self.doMining,                 "Mine for resources",   True,  1],
                "sleep":        [self.sleepInBed,               "Sleep in a bed",       False, 0],
                "stop":         [self.stopThis,                 "Stop all activities",  False, 0],
                "status":       [self.sayStatus,                "Report status",        False, 0],
                "wake":         [self.wakeUp,                   "Stop sleeping",        False, 0],
                "yeet":         [self.exitGame,                 "Exit the game",        False, 0],
        }

    def chat(self,txt):
        self.bot.chat(txt)
        self.pdebug(f'  chat: {txt}',0)

    def sayStatus(self):
        self.pdebug(f'  level : {self.bot.experience.level}',0)
        self.pdebug(f'  health: {int(100*self.bot.health/20)}%',0)
        self.pdebug(f'  food  : {int(100*self.bot.food/20)}%',0)

    def sayHello(self):
        self.chat('hello to you too!')

    def startActivity(self, name):
        t_str = botlib.myTime()
        self.pdebug(60*'-',1)
        self.pdebug(f'{name:47} {t_str}',1)
        self.pdebug(60*'-',1)
        self.activity_start = time.time()
        self.activity_name = name
        self.stopActivity = False
        self.activity_major = True
        self.dangerType = None 
        self.speedMode = False

    async def endActivity(self):
        if self.activity_major:
            t_str = botlib.myTime()
            d_str = str(datetime.timedelta(seconds=int(time.time()-self.activity_start)))
            self.pdebug(f'Activity {self.activity_name} ended at {t_str} (duration: {d_str})',1)
            self.bot.clearControlStates('sneak', False)
            await self.eatFood()
        self.activity_last_duration = d_str
        self.bot.stopActivity = True
        self.activity_major = False

    def safeSleep(self,t):
        for i in range(0,t):
            time.sleep(1)
            if self.stopActivity:
                return False
        return True

    def stopThis(self):
        self.stopActivity = True

    async def sleepInBed(self):
        bed = self.findClosestBlock("White Bed",xz_radius=3,y_radius=1)
        if not bed:
            self.chat('cant find a White Bed nearby (I only use those)')
        else:
            await self.bot.sleep(bed)
            self.chat('good night!')

    async def wakeUp(self):
            await self.bot.wake()
            self.chat('i woke up!')

    def exitGame(self):
            # exit the game
            self.bot.quit()

    async def handleChat(self,sender, message, this, *rest):

        # check if order is incorrect to fix a bug we are seeing between Guido and Daniel
        if type(sender) != type(""):
            # reorder
            t = sender
            sender = message
            message =  this
            this = t

        message = message.strip()

        # Is this for me, or for someone else?
        if message.startswith(self.callsign):
            print(f'{sender} messaged me "{message}"')
            message = message[len(self.callsign):]
        elif sender != self.bossPlayer():
            return

        await self.handleCommand(message,sender)

    async def handleCommand(self, message, sender):

        # Handle standard commands

        message = message.lower()
        cmd = message.split()[0]
        args = message.split()[1:]

        if cmd in self.commandList:
            c = self.commandList[cmd]
            call_function = c[0]
            if c[2]:
                # Major activity
                if self.activity_major:
                    self.pdebug(f'*** error: major activity in progress, stop it first {self.activity_name}.')
                    return
                self.startActivity(c[1])
                def run_activity():
                    # For major activities, we need to handle potential async functions
                    async def run_async_activity():
                        if c[3] > 0:
                            if asyncio.iscoroutinefunction(call_function):
                                await call_function(args)
                            else:
                                call_function(args)
                        else:
                            if asyncio.iscoroutinefunction(call_function):
                                await call_function()
                            else:
                                call_function()
                    
                    if asyncio.iscoroutinefunction(call_function):
                        asyncio.run(run_async_activity())
                    else:
                        if c[3] > 0:
                            call_function(args)
                        else:
                            call_function()
                
                activity_thread = threading.Thread(target=run_activity)
                activity_thread.start()
            else:
                # Check if the function is async (based on known async methods)
                async_methods = {'sleepInBed', 'wakeUp'}
                if call_function.__name__ in async_methods:
                    if c[3] > 0:
                        await call_function(args)
                    else:
                        await call_function()
                else:
                    if c[3] > 0:
                        call_function(args)
                    else:
                        call_function()
            return

        # Legacy commands, need to clean up

        # come - try to get to the player
        if 'come' in message or 'go' in message:
            if message == 'come':
                player = self.bot.players[sender]
            elif 'go to' in message:
                player = self.bot.players[message[6:]]
            else:
                self.chat("No Clear Target")
            target = player.entity
            if not target:
                self.chat("I don't see you!")
                return
            pos = target.position
            async def run_come():
                await self.walkTo(pos.x, pos.y, pos.z)
            
            def run_come_sync():
                asyncio.run(run_come())
            
            come_thread = threading.Thread(target=run_come_sync)
            come_thread.start()

        if 'follow' in message:
            if message == 'follow':
                player = self.bot.players[sender]
            elif len(message) > 6:
                player = self.bot.players[message[7:]]
            else:
                self.chat("No Clear Target")
            target = player.entity
            if not target:
                self.chat("I don't see you!")
                return
            async def run_follow():
                while self.stopActivity != True:
                    self.bot.pathfinder.setGoal(pathfinder.goals.GoalFollow(player.entity, 1))
                    time.sleep(2)
            
            def run_follow_sync():
                asyncio.run(run_follow())
            
            follow_thread = threading.Thread(target=run_follow_sync)
            follow_thread.start()

        if message.startswith('moveto'):
            args = message[6:].split()
            if len(args) != 1:
                self.chat('Need name of location to move to.')
                return
            async def run_moveto():
                await self.gotoLocation(args[0])
            
            def run_moveto_sync():
                asyncio.run(run_moveto())
            
            moveto_thread = threading.Thread(target=run_moveto_sync)
            moveto_thread.start()

        if message.startswith('transfer to'):
            args = message[11:].split()
            if len(args) != 1:
                self.chat('Need name of target chest.')
                return
            async def run_transfer():
                await self.transferToChest(args[0])
            
            def run_transfer_sync():
                asyncio.run(run_transfer())
            
            transfer_thread = threading.Thread(target=run_transfer_sync)
            transfer_thread.start()


