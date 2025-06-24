# Definition of a work area to do stuff in (e.g. build, mine etc.)
# Main purpose is to handle relative to absolute coordinates
#

import time
import lib.botlib as botlib
from lib.botlib import strDirection, addVec3, subVec3, lenVec3

# Area in front of chest+torch
#   x is lateral (torch is 0)
#   z is depth (torch is at -1)
#   y is height (chest is at 0)
#
#   NOTE: This means this is a LEFT HANDED coordinate system while
#         Minecraft uses a RIGHT HANDED coordinate system. Yes, I know.
#         It still makes more sense this way.

class workArea:

    #
    # Initialize a work area
    #

    valuables = None
    status = "all good"
    blocks_mined = 0
    last_break = 0
    break_interval = 100

    def __init__(self,pybot,width,height,depth, notorch=False):
        self.valid = False
        self.pybot = pybot
        self.notorch = notorch

        if width % 2 != 1:
            self.pybot.perror(f'Error: width={width} but only odd width work areas are supported.')
            return None

        self.width = width
        self.width2 = int((width-1)/2)
        self.height = height
        self.depth = depth

    def initialize(self):
        """Async initialization that finds chest and torch"""
        print("=== CRAZY DEBUG: Starting workArea.initialize() ===")
        print(f"CRAZY DEBUG: self.notorch = {self.notorch}")
        print(f"CRAZY DEBUG: Bot position = {self.pybot.bot.entity.position}")
        print(f"CRAZY DEBUG: Bot health = {self.pybot.bot.health}")
        print(f"CRAZY DEBUG: Work area dimensions - width:{self.width} height:{self.height} depth:{self.depth}")
        
        # Find the starting chest
        # self.start_chest = self.pybotk( #
        # self.start_chest = self.pybot.findClosestBlock(
        #     "Chest", xz_radius=6, y_radius=20
        # )
        # print(f"{self.start_chest=}")
        print("CRAZY DEBUG: Checking notorch assertion...")
        assert not self.notorch, "Not yet implemented"
        print("CRAZY DEBUG: Passed notorch assertion")
        
        if self.notorch:
            print("CRAZY DEBUG: In notorch branch (this shouldn't happen)")
            # Area with arbitrary direction, we pick point in front of chest
            p = self.start_chest.getProperties()
            self.d = botlib.strDirection(p["facing"])
            self.start = botlib.addVec3(self.start_chest.position, self.d)

            # Origin
            self.origin = self.start

        print("CRAZY DEBUG: About to start findBlocks")
        print("starting findBlocks")
        print(self.pybot.bot.entity.position)
        
        # Check what's in displayname_to_id
        print("CRAZY DEBUG: Full displayname_to_id dict keys:")
        all_keys = list(self.pybot.displayname_to_id.keys())
        print(f"CRAZY DEBUG: Total keys in displayname_to_id: {len(all_keys)}")
        for i, key in enumerate(sorted(all_keys)):
            if i < 20:  # Print first 20 keys
                print(f"CRAZY DEBUG: displayname_to_id['{key}'] = {self.pybot.displayname_to_id[key]}")
        
        # THEORY_5_DEBUG: Check what block IDs we're searching for
        print(f"THEORY_5_DEBUG: Torch IDs = {self.pybot.displayname_to_id.get('Torch', 'NOT_FOUND')}")
        print(f"THEORY_5_DEBUG: Redstone Torch IDs = {self.pybot.displayname_to_id.get('Redstone Torch', 'NOT_FOUND')}")
        print(f"THEORY_5_DEBUG: Chest IDs = {self.pybot.displayname_to_id.get('Chest', 'NOT_FOUND')}")
        
        print("CRAZY DEBUG: Building torch_ids...")
        redstone_torch_ids = self.pybot.displayname_to_id.get("Redstone Torch", [])
        torch_ids_basic = self.pybot.displayname_to_id.get("Torch", [])
        print(f"CRAZY DEBUG: redstone_torch_ids = {redstone_torch_ids}")
        print(f"CRAZY DEBUG: torch_ids_basic = {torch_ids_basic}")
        
        torch_ids = (
            self.pybot.displayname_to_id["Redstone Torch"]
            + self.pybot.displayname_to_id["Torch"]
        )
        print(f"THEORY_5_DEBUG: Combined torch_ids = {torch_ids}")
        
        print("CRAZY DEBUG: About to call bot.findBlocks for torches...")
        torch_blocks = self.pybot.bot.findBlocks(
            {
                "matching": torch_ids,
                "maxDistance": 100,
                "count": 200,
            },
        )
        print(f"CRAZY DEBUG: Raw torch_blocks result = {torch_blocks}")
        torch_blocks = list(iter(torch_blocks))
        print(f"CRAZY DEBUG: torch_blocks after list conversion = {torch_blocks}")

        print("CRAZY DEBUG: About to call bot.findBlocks for chests...")
        chest_ids = self.pybot.displayname_to_id["Chest"]
        print(f"CRAZY DEBUG: chest_ids = {chest_ids}")
        
        chest_blocks = self.pybot.bot.findBlocks(
            {
                "matching": self.pybot.displayname_to_id["Chest"],
                "maxDistance": 100,
                "count": 200,
            },
        )
        print(f"CRAZY DEBUG: Raw chest_blocks result = {chest_blocks}")
        chest_blocks = list(iter(chest_blocks))
        print(f"CRAZY DEBUG: chest_blocks after list conversion = {chest_blocks}")
        
        print(f"{len(chest_blocks)=}")
        print(f"{len(torch_blocks)=}")
        
        # THEORY_5_DEBUG: Let's see what blocks ARE available nearby
        print("THEORY_5_DEBUG: Searching for any blocks within 10 blocks to see what exists...")
        all_nearby_blocks = self.pybot.bot.findBlocks({
            "maxDistance": 10,
            "count": 100,
        })
        print(f"CRAZY DEBUG: all_nearby_blocks = {all_nearby_blocks}")
        nearby_block_types = set()
        for block_pos in all_nearby_blocks:
            print(f"CRAZY DEBUG: Checking block at {block_pos}")
            block = self.pybot.bot.blockAt(block_pos)
            print(f"CRAZY DEBUG: Block object = {block}")
            if block:
                print(f"CRAZY DEBUG: Block displayName = {getattr(block, 'displayName', 'NO_DISPLAY_NAME')}")
                if hasattr(block, 'displayName') and block.displayName != "Air":
                    nearby_block_types.add(block.displayName)
        print(f"THEORY_5_DEBUG: Nearby block types = {sorted(nearby_block_types)}")
        
        # THEORY_6_DEBUG: Check bot's inventory to see what we can place
        print("THEORY_6_DEBUG: Checking bot inventory for chest and torch...")
        inventory_items = list(self.pybot.bot.inventory.items())
        print(f"THEORY_6_DEBUG: Total inventory items: {len(inventory_items)}")
        for item in inventory_items:
            print(f"THEORY_6_DEBUG: Inventory item: {item.count}x {item.displayName} (type: {item.type})")
        
        has_chest = self.pybot.invItemCount("Chest") > 0
        has_torch = self.pybot.invItemCount("Torch") > 0
        print(f"THEORY_6_DEBUG: has_chest={has_chest}, has_torch={has_torch}")
        
        if len(chest_blocks) == 0 and len(torch_blocks) == 0:
            print("THEORY_6_DEBUG: No chest+torch setup found, but bot should place them!")
            if has_chest and has_torch:
                print("THEORY_6_DEBUG: Bot has both chest and torch - will place them!")
                return self.place_initial_setup()
            else:
                print(f"THEORY_6_DEBUG: Bot missing items - chest:{has_chest}, torch:{has_torch}")
                print("THEORY_7_DEBUG: Attempting to give bot required items...")
                return self.give_and_place_setup()
        
        print("CRAZY DEBUG: Setting self.start_chest = None and starting search loop...")
        self.start_chest = None
        print(f"CRAZY DEBUG: Starting nested loop - {len(chest_blocks)} chests x {len(torch_blocks)} torches")
        
        for i, chest in enumerate(chest_blocks):
            print(f"CRAZY DEBUG: Checking chest {i}: {chest}")
            for j, torch in enumerate(torch_blocks):
                print(f"CRAZY DEBUG: Checking torch {j}: {torch}")
                if chest is None or torch is None:
                    print(f"CRAZY DEBUG: Skipping null chest or torch")
                    continue
                print(f"CRAZY DEBUG: Computing distance between chest {chest} and torch {torch}")
                d = subVec3(chest, torch)
                print(f"CRAZY DEBUG: subVec3 result d = {d}")
                L = lenVec3(d)
                print(f"CRAZY DEBUG: lenVec3 result L = {L}")
                print(f"CRAZY DEBUG: chest.y = {chest.y}, torch.y = {torch.y}")
                print(f"{chest}, {torch}, {L=}")
                if L == 1 and chest.y == torch.y:
                    print(f"CRAZY DEBUG: FOUND MATCH! chest={chest}, torch={torch}")
                    self.start_chest = chest
                    self.start_torch = torch
                    break
                else:
                    print(f"CRAZY DEBUG: No match - L={L} (need 1), same_y={chest.y == torch.y}")

            # if chest.position.distanceTo(torch.position) < 1 and chest.position.y == torch.position.y:
            if self.start_chest:
                print(f"CRAZY DEBUG: Breaking outer loop - found match!")
                break
        else:
            print(f"CRAZY DEBUG: No matching chest+torch found in nested loop")
            self.pybot.chat(
                "Can't find starting position. Place a chest and torch on the ground to mark the direction."
            )
            print(f"CRAZY DEBUG: About to assert False and crash...")
            assert False, "crashing"

        # if not self.start_chest:
        #     self.pybot.chat("Can't find starting position. Place a chest on the ground to mark it.")
        #     return False

        # else:

        # Determine "forward" direction from chest+torch
        # torch = self.pybot.findClosestBlock("Torch", xz_radius=6, y_radius=20)
        # r_torch = self.pybot.findClosestBlock(
        #     "Redstone Torch", xz_radius=6, y_radius=20
        # )

        # # Redstone Torch has precedence
        # if r_torch:
        #     self.start_torch = r_torch
        # else:
        #     self.start_torch = torch

        # print(f"{self.start_torch=}")

        # if not self.start_torch:
        #     self.pybot.chat("Can't find starting position. Place chest, and torch on the ground next to it to mark the direction.")
        #     return False

        # if self.start_torch.position.y != self.start_chest.position.y:
        #     self.pybot.chat("Can't find starting position. Chest and torch at different levels??")
        #     return False

        # Direction of the Area
        print(f"CRAZY DEBUG: Found valid chest+torch pair! Now computing direction...")
        print(f"CRAZY DEBUG: self.start_chest = {self.start_chest}")
        print(f"CRAZY DEBUG: self.start_torch = {self.start_torch}")

        # torch_blocks = self.pybot.bot.findBlocks(
        #     {
        #         "matching": [
        #             self.pybot.displayname_to_id["Redstone Torch"],
        #             self.pybot.displayname_to_id["Torch"],
        #         ],
        #         "maxDistance": 10,
        #         "count": 10,
        #     }
        # )
        # print(f"{torch_blocks=}")

        print(f"CRAZY DEBUG: Computing direction vector from torch to chest...")
        self.d = subVec3(self.start_torch, self.start_chest)
        print(f"CRAZY DEBUG: Direction vector self.d = {self.d}")
        # if lenVec3(self.d) != 1:
        #     self.pybot.chat("Can't find starting position. Torch is not next to chest.")
        #     return False

        print(f"CRAZY DEBUG: Setting self.start = self.start_chest")
        self.start = self.start_chest # findBlocks actually returns a Vec3 so it's already a position
        print(f"CRAZY DEBUG: self.start = {self.start}")
        # self.start = self.start_chest.position

        # Origin
        print(f"CRAZY DEBUG: Computing origin point...")
        origin_x = self.start.x + 2 * self.d.x
        origin_y = self.start.y
        origin_z = self.start.z + 2 * self.d.z
        print(f"CRAZY DEBUG: Origin calculation: start=({self.start.x},{self.start.y},{self.start.z}), d=({self.d.x},{self.d.y},{self.d.z})")
        print(f"CRAZY DEBUG: Origin coords: ({origin_x},{origin_y},{origin_z})")
        self.origin = self.pybot.Vec3(origin_x, origin_y, origin_z)
        print(f"CRAZY DEBUG: self.origin = {self.origin}")

        # Vector directions
        print(f"CRAZY DEBUG: Setting up direction vectors...")
        self.forwardVector = self.d
        self.backwardVector = botlib.invVec3(self.d)
        print(f"CRAZY DEBUG: forwardVector = {self.forwardVector}")
        print(f"CRAZY DEBUG: backwardVector = {self.backwardVector}")

        # Note that we flip build area vs. world coordinates. Left Handed vs Right handed.
        self.leftVector = botlib.rotateLeft(self.d)
        self.rightVector = botlib.rotateRight(self.d)
        print(f"CRAZY DEBUG: leftVector = {self.leftVector}")
        print(f"CRAZY DEBUG: rightVector = {self.rightVector}")

        self.latx = self.rightVector.x
        self.latz = self.rightVector.z
        print(f"CRAZY DEBUG: latx = {self.latx}, latz = {self.latz}")

        # Done. Set flag.
        print(f"CRAZY DEBUG: Setting self.valid = True and returning True")
        self.valid = True
        print(f"CRAZY DEBUG: workArea.initialize() completed successfully!")
        return True

    def place_initial_setup(self):
        """Place a chest and torch for the bot to start mining"""
        print("THEORY_6_DEBUG: Placing initial chest+torch setup...")
        
        # Get bot's current position
        bot_pos = self.pybot.bot.entity.position
        print(f"THEORY_6_DEBUG: Bot position: {bot_pos}")
        
        # Place chest at bot's feet
        chest_pos = self.pybot.Vec3(int(bot_pos.x), int(bot_pos.y) - 1, int(bot_pos.z))
        print(f"THEORY_6_DEBUG: Placing chest at {chest_pos}")
        
        # Wield and place chest
        if self.pybot.wieldItem("Chest"):
            try:
                # Place chest on the ground below bot
                ground_block = self.pybot.bot.blockAt(chest_pos)
                if ground_block.displayName == "Air":
                    print("THEORY_6_DEBUG: Ground is air, can't place chest there")
                    return False
                
                face_vector = self.pybot.Vec3(0, 1, 0)  # Place on top
                result = self.pybot.bot.placeBlock(ground_block, face_vector)
                print(f"THEORY_6_DEBUG: Chest placement result: {result}")
                time.sleep(1)
            except Exception as e:
                print(f"THEORY_6_DEBUG: Failed to place chest: {e}")
                return False
        else:
            print("THEORY_6_DEBUG: Failed to wield chest")
            return False
        
        # Place torch next to chest (1 block north)
        torch_pos = self.pybot.Vec3(int(bot_pos.x), int(bot_pos.y) - 1, int(bot_pos.z) + 1)
        print(f"THEORY_6_DEBUG: Placing torch at {torch_pos}")
        
        if self.pybot.wieldItem("Torch"):
            try:
                ground_block = self.pybot.bot.blockAt(torch_pos)
                if ground_block.displayName == "Air":
                    print("THEORY_6_DEBUG: Ground is air, can't place torch there")
                    return False
                    
                face_vector = self.pybot.Vec3(0, 1, 0)  # Place on top
                result = self.pybot.bot.placeBlock(ground_block, face_vector)
                print(f"THEORY_6_DEBUG: Torch placement result: {result}")
                time.sleep(1)
            except Exception as e:
                print(f"THEORY_6_DEBUG: Failed to place torch: {e}")
                return False
        else:
            print("THEORY_6_DEBUG: Failed to wield torch")
            return False
        
        print("THEORY_6_DEBUG: Initial setup placed! Now re-initializing...")
        # Now try to initialize again with the placed blocks
        return self.initialize()

    def give_and_place_setup(self):
        """Give bot required items and place them"""
        print("THEORY_7_DEBUG: Giving bot chest and torch via creative mode...")
        
        try:
            # Try using creative mode to give items
            print("THEORY_7_DEBUG: Attempting creative.setInventorySlot for chest...")
            chest_item = self.pybot.Item(177, 1)  # Chest ID is 177
            self.pybot.bot.creative.setInventorySlot(9, chest_item)
            
            print("THEORY_7_DEBUG: Attempting creative.setInventorySlot for torch...")
            torch_item = self.pybot.Item(171, 1)  # Torch ID is 171 
            self.pybot.bot.creative.setInventorySlot(10, torch_item)
            
            time.sleep(0.5)
            
            # Check if it worked
            has_chest_now = self.pybot.invItemCount("Chest") > 0
            has_torch_now = self.pybot.invItemCount("Torch") > 0
            print(f"THEORY_7_DEBUG: After giving items - chest:{has_chest_now}, torch:{has_torch_now}")
            
            if has_chest_now and has_torch_now:
                print("THEORY_7_DEBUG: Successfully gave items! Now placing setup...")
                return self.place_initial_setup()
            else:
                print("THEORY_7_DEBUG: Creative mode item giving failed")
                return False
                
        except Exception as e:
            print(f"THEORY_7_DEBUG: Creative mode failed: {e}")
            print("THEORY_7_DEBUG: Trying chat command approach...")
            
            # Try using chat commands to give items  
            try:
                self.pybot.bot.chat("/give @s chest 1")
                time.sleep(0.5)
                self.pybot.bot.chat("/give @s torch 1") 
                time.sleep(0.5)
                
                has_chest_now = self.pybot.invItemCount("Chest") > 0
                has_torch_now = self.pybot.invItemCount("Torch") > 0
                print(f"THEORY_7_DEBUG: After chat commands - chest:{has_chest_now}, torch:{has_torch_now}")
                
                if has_chest_now and has_torch_now:
                    print("THEORY_7_DEBUG: Chat command worked! Now placing setup...")
                    return self.place_initial_setup()
                else:
                    print("THEORY_7_DEBUG: Chat commands also failed")
                    return False
                    
            except Exception as e2:
                print(f"THEORY_7_DEBUG: Chat command also failed: {e2}")
                print("THEORY_7_DEBUG: All methods failed - bot needs manual setup")
                return False

    def xRange(self):
        return range(-self.width2, self.width2+1)

    def yRange(self):
        return range(0,self.height)

    def zRange(self):
        return range(0,self.depth)

    def toWorld(self,x,y,z):
        return self.pybot.Vec3(self.origin.x+self.latx*x+self.d.x*z,
                    self.origin.y+y,
                    self.origin.z+self.latz*x+self.d.z*z)

    # Convert position relative to absolute coordinates

    def toWorldV3(self,v):
        return self.pybot.Vec3(self.origin.x+self.latx*v.x+self.d.x*v.z,
                    self.origin.y+v.y,
                    self.origin.z+self.latz*v.x+self.d.z*v.z)

    # Convert direction relative to absolute coordinates

    def dirToWorldV3(self,v):
        return self.pybot.Vec3(self.latx*v.x+self.d.x*v.z,
                    v.y,
                    self.latz*v.x+self.d.z*v.z)

    # Minecraft block at relative coordinates

    def blockAt(self, *argv):
        if len(argv) == 3:
            return self.pybot.bot.blockAt(self.toWorld(argv[0],argv[1],argv[2]))
        else:
            return self.pybot.bot.blockAt(self.toWorldV3(argv[0]))

    # Returns a list of all blocks in the workArea

    def allBlocks(self):
        blocks = []

        for z in self.zRange():
            for y in self.yRange():
                for x in self.xRange():
                    blocks.append(Vec3(x,y,z))
        return blocks

    # Returns a list of all blocks in the workArea

    def allBlocksWorld(self):
        blocks = []

        for z in self.zRange():
            for y in self.yRange():
                for x in self.xRange():
                    blocks.append(self.toWorld(x,y,z))
        return blocks

    # Convert position relative to absolute coordinates

    def walkTo(self, *argv):
        if len(argv) == 3:
            v = self.toWorld(argv[0],argv[1],argv[2])
        else:
            v = self.toWorldV3(argv[0])
        self.pybot.walkTo(v)

    def walkToBlock(self, *argv):
        if len(argv) == 3:
            v = self.toWorld(argv[0],argv[1],argv[2])
        else:
            v = self.toWorldV3(argv[0])
        self.pybot.walkToBlock(v)

    # More precise version (0.3 blocks)

    def walkToBlock3(self, *argv):
        if len(argv) == 3:
            v = self.toWorld(argv[0],argv[1],argv[2])
        else:
            v = self.toWorldV3(argv[0])
        self.pybot.walkToBlock3(v)

    # String area direction as North, South etc.

    def directionStr(self):
        return botlib.directionStr(self.d)

    # Walk back to Torch

    def walkToStart(self):
        self.pybot.walkToBlock3(self.start)

    # Restock from Chest

    def restock(self, item_list):
        self.walkToStart()
        self.pybot.restockFromChest(item_list)
        self.pybot.eatFood()
