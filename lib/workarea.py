# Definition of a work area to do stuff in (e.g. build, mine etc.)
# Main purpose is to handle relative to absolute coordinates
#

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
                    blocks.append(self.toVec3(x,y,z))
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
