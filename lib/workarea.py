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
        # Find the starting chest
        # self.start_chest = self.pybotk( #
        # self.start_chest = self.pybot.findClosestBlock(
        #     "Chest", xz_radius=6, y_radius=20
        # )
        # print(f"{self.start_chest=}")
        assert not self.notorch, "Not yet implemented"
        if self.notorch:
            # Area with arbitrary direction, we pick point in front of chest
            p = self.start_chest.getProperties()
            self.d = botlib.strDirection(p["facing"])
            self.start = botlib.addVec3(self.start_chest.position, self.d)

            # Origin
            self.origin = self.start

        print("starting findBlocks")
        print(self.pybot.bot.entity.position)
        torch_ids = (
            self.pybot.displayname_to_id["Redstone Torch"]
            + self.pybot.displayname_to_id["Torch"]
        )
        torch_blocks = self.pybot.bot.findBlocks(
            {
                "matching": torch_ids,
                "maxDistance": 100,
                "count": 200,
            },
        )
        torch_blocks = list(iter(torch_blocks))

        chest_blocks = self.pybot.bot.findBlocks(
            {
                "matching": self.pybot.displayname_to_id["Chest"],
                "maxDistance": 100,
                "count": 200,
            },
        )
        chest_blocks = list(iter(chest_blocks))
        print(f"{len(chest_blocks)=}")
        print(f"{len(torch_blocks)=}")
        self.start_chest = None
        for chest in chest_blocks:
            for torch in torch_blocks:
                if chest is None or torch is None:
                    continue
                d = subVec3(chest, torch)
                L = lenVec3(d)
                print(f"{chest}, {torch}, {L=}")
                if L == 1 and chest.y == torch.y:
                    self.start_chest = chest
                    self.start_torch = torch
                    break

            # if chest.position.distanceTo(torch.position) < 1 and chest.position.y == torch.position.y:
            if self.start_chest:
                break
        else:
            self.pybot.chat(
                "Can't find starting position. Place a chest and torch on the ground to mark the direction."
            )
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

        self.d = subVec3(self.start_torch, self.start_chest)
        # if lenVec3(self.d) != 1:
        #     self.pybot.chat("Can't find starting position. Torch is not next to chest.")
        #     return False

        self.start = self.start_chest # findBlocks actually returns a Vec3 so it's already a position
        # self.start = self.start_chest.position

        # Origin
        self.origin = self.pybot.Vec3(
            self.start.x + 2 * self.d.x, self.start.y, self.start.z + 2 * self.d.z
        )

        # Vector directions
        self.forwardVector = self.d
        self.backwardVector = botlib.invVec3(self.d)

        # Note that we flip build area vs. world coordinates. Left Handed vs Right handed.
        self.leftVector = botlib.rotateLeft(self.d)
        self.rightVector = botlib.rotateRight(self.d)

        self.latx = self.rightVector.x
        self.latz = self.rightVector.z

        # Done. Set flag.
        self.valid = True
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
