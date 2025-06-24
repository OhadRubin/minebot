from .bot import Vec3

def itemTypeAndName(bot,item_arg):

    if isinstance(item_arg,str):
        item_name = item_arg
        # Find this item in the inventory
        if bot.inventory.items != []:
            # find in inventory list
            for item in bot.inventory.items():
                if item.displayName == item_name:
                    item_type = item.type
                    break
            else:
                item_type = None
    elif item_arg.type and item_arg.displayName:
        item_type = item_arg.type
        item_name = item_arg.displayName
    else:
        item_type = None
        item_name = "Unknown"

    return item_type, item_name

def checkInHand(bot,item_arg):

    if not bot.heldItem:
        return False

    item_type, item_name = itemTypeAndName(bot,item_arg)

    if bot.heldItem.type == item_type:
        return True
    else:
        return False

def wieldItem(bot,item_arg):

    if not item_arg:
        print("trying to equip item 'None'.")
        return None

    # Translate argument into type and name

    item_type, item_name = itemTypeAndName(bot,item_arg)

    # check if we found it
    if item_type == None:
        print(f'cant find item {item_name} ({item_type}) to wield.')
        return None

    time.sleep(0.25)
    # Am I already holding it?
    if checkInHand(bot,item_type):
        return item_name

    # Equip the item
    print(f'      equip {item_name} ({item_type})',3)

    # Try wielding 5 times
    for i in range(0,5):
        try:
            bot.equip(item_type,"hand")
        except Exception as e:
            hand_type, hand_name = itemInHand(bot)
            print(f'wieldItem() try #{i}. In hand {hand_name} vs {item_name}',e)
            # Did it raise an exception, but we still have the right item? If yes, all good.
            if checkInHand(bot,item_type):
                return item_name
            time.sleep(1)
        else:
            break

    time.sleep(0.25)
    if not checkInHand(bot,item_name):
        print(f'Wielding item {item_name} failed after max retries!')
        return None

    return item_name


needs_iron_pickaxe = ["Gold Ore", "Redstone Ore", "Diamond Ore", "Emerald Ore"]
needs_diamond_pickaxe = ["Obsidian"]
needs_shovel = ["Dirt", "Gravel", "Sand"]
# This is what we are looking for
valuable_blocks = [ "Coal Ore", "Copper Ore", "Lapis Lazuli Ore", "Iron Ore", "Gold Ore", "Redstone Ore", "Diamond Ore", "Emerald Ore", "Block of Coal", ]
# These blocks never get mined up
ignored_blocks = [ "Torch", "Wall Torch", "Sign", "Air", "Cave Air", "Void Air", "Chest", "Crafting Table", "Furnace", "Ladder", "Glass", "Stone Bricks", "Chiseled Stone Bricks", "Stone Brick Stairs", "Water", "Flowing Water", "Bubble Column", ]
# These blocks we need to bridge over
dangerBlocks = { "Air", "Cave Air", "Void Air", "Lava", "Water", "Infested Stone", }
# These blocks will drop down, we need to dig them up until done
block_will_drop = [ "Gravel", "Sand", "Red Sand", "Pointed Dropstone", "Anvil," ]
block_will_flow = [ "Lava", "Water", ]
# Blocks that will drop down on you
dangerDropBlocks = block_will_flow + block_will_drop
# These blocks we use to fill holes or build bridges
fillBlocks = { "Stone Bricks", "Cobblestone", "Dirt" }


def mining_safety_check(bot, position):
    n = bot.blockAt(position).displayName
    if n in block_will_flow:
        stopActivity = True
        dangerType = "danger: "+n
        print(f'danger: {n}, aborting mining')
        return False
    return True

async def mineBlock(bot, x ,y =None,z=None):
    if not y and not z:
        v = x
    else:
        v = Vec3(x,y,z)

    b = bot.blockAt(v)

    if not b:
        print(f'No block at ({v.x},{v.y},{v.z})')
        return 0

    print(f'Block at ({v.x},{v.y},{v.z}): {b.displayName}')

    if not hasattr(b, 'displayName') or not b.displayName:
        print(f'Block has no displayName')
        return 0

    if b.displayName in ignored_blocks:
        print(f'Ignoring block: {b.displayName}')
        return 0

    print(f'Attempting to mine: {b.displayName}')

    # Use the JavaScript bot directly
    await bot.dig(b, True)  # forceLook=True
    print(f'Mining started for {b.displayName}')

    # Check if block was mined
    new_block = bot.blockAt(v)
    if not new_block or new_block.displayName in ignored_blocks:
        print(f'Successfully mined {b.displayName}')
        return 1
    else:
        print(f'Block still there: {new_block.displayName}')
        return 0


def get_current_position(bot):
    """Get the bot's current position as a Vec3."""
    return bot.entity.position

def get_front_block_position(bot):
    """Calculate the position of the block directly in front of the bot."""
    import math
    
    pos = bot.entity.position
    yaw = bot.entity.yaw
    
    print(f"Debug - Current yaw: {yaw}")
    
    # Calculate the front block position based on yaw
    # Yaw 0 = south, π/2 = west, π = north, 3π/2 = east
    front_x = pos.x - math.sin(yaw)
    front_z = pos.z + math.cos(yaw)
    front_y = pos.y
    
    print(f"Debug - Calculated front position: ({front_x}, {front_y}, {front_z})")
    
    # Round to get block coordinates
    block_pos = Vec3(math.floor(front_x), math.floor(front_y), math.floor(front_z))
    print(f"Debug - Block coordinates: ({block_pos.x}, {block_pos.y}, {block_pos.z})")
    
    return block_pos

async def mine_front_block(bot):
    """Mine the block directly in front of the bot."""
    current_pos = get_current_position(bot)
    front_pos = get_front_block_position(bot)
    
    print(f"Bot position: ({current_pos.x:.2f}, {current_pos.y:.2f}, {current_pos.z:.2f})")
    print(f"Mining block at: ({front_pos.x}, {front_pos.y}, {front_pos.z})")
    result = await mineBlock(bot, front_pos)
    return result

async def equip_pickaxe(bot):
    """Find and equip the best available pickaxe"""
    pickaxe_types = [
        "Netherite Pickaxe",
        "Diamond Pickaxe", 
        "Iron Pickaxe",
        "Stone Pickaxe",
        "Wooden Pickaxe"
    ]
    
    print("Looking for pickaxe in inventory...")
    
    # Find the best pickaxe in inventory
    for pickaxe_name in pickaxe_types:
        for item in bot.inventory.items():
            if hasattr(item, 'displayName') and item.displayName == pickaxe_name:
                print(f"Found {pickaxe_name}, equipping...")
                try:
                    await bot.equip(item, "hand")
                    print(f"Successfully equipped {pickaxe_name}")
                    return True
                except Exception as e:
                    print(f"Failed to equip {pickaxe_name}: {e}")
                    return False
    
    print("No pickaxe found in inventory")
    return False

#
# Definition of a work area to do stuff in (e.g. build, mine etc.)
# Main purpose is to handle relative to absolute coordinates
#

# Area in front of chest+torch
#   x is lateral (torch is 0)
#   z is depth (torch is at -1)
#   y is height (chest is at 0)
#
#   NOTE: This means this is a LEFT HANDED coordinate system while
#         Minecraft uses a RIGHT HANDED coordinate system. Yes, I know.
#         It still makes more sense this way.

class WorkArea:
    def __init__(self, bot, width, height, depth, notorch=False):
        self.valid = False
        self.bot = bot
        self.status = "all good"
        self.blocks_mined = 0
        self.last_break = 0
        self.break_interval = 100

        if width % 2 != 1:
            print(f'Error: width={width} but only odd width work areas are supported.')
            return None

        self.width = width
        self.width2 = int((width-1)/2)
        self.height = height
        self.depth = depth

        # Find starting chest
        chest_blocks = self.bot.js_bot.findBlocks({
            'matching': [self.bot.js_bot.registry.blocksByName["chest"].id],
            'maxDistance': 128,
            'count': 1
        },
        # useExtraInfo=False
        )
        chest_pos = chest_blocks[0] if chest_blocks else None

        if not chest_pos:
            print("Can't find starting position. Place a chest on the ground to mark it.")
            return None

        self.start_chest = chest_pos

        if notorch:
            # Area with arbitrary direction, we pick point in front of chest
            self.d = Vec3(1, 0, 0)  # Default direction
            self.start = Vec3(self.start_chest.x + self.d.x, self.start_chest.y, self.start_chest.z + self.d.z)
            self.origin = self.start
        else:
            # Determine "forward" direction from chest+torch
            torch_blocks = self.bot.js_bot.findBlocks({
                'matching': [self.bot.js_bot.registry.blocksByName["torch"].id],
                'maxDistance': 3,
                'count': 1
            })
            torch_pos = torch_blocks[0] if torch_blocks else None

            r_torch_blocks = self.bot.js_bot.findBlocks({
                'matching': [self.bot.js_bot.registry.blocksByName["redstone_torch"].id],
                'maxDistance': 3,
                'count': 1
            })
            r_torch_pos = r_torch_blocks[0] if r_torch_blocks else None

            self.start_torch = r_torch_pos if r_torch_pos else torch_pos
            if not self.start_torch:
                print("Can't find starting position. Place chest, and torch on the ground next to it to mark the direction.")
                return None

            # Direction vector from chest to torch
            self.d = Vec3(
                self.start_torch.x - self.start_chest.x,
                0,
                self.start_torch.z - self.start_chest.z
            )

            self.start = Vec3(self.start_chest.x, self.start_chest.y, self.start_chest.z)
            self.origin = Vec3(
                self.start.x + 2 * self.d.x,
                self.start.y,
                self.start.z + 2 * self.d.z
            )

        # Vector directions
        self.forwardVector = self.d
        self.backwardVector = Vec3(-self.d.x, self.d.y, -self.d.z)

        # Left/right vectors (rotated 90 degrees)
        self.leftVector = Vec3(-self.d.z, 0, self.d.x)
        self.rightVector = Vec3(self.d.z, 0, -self.d.x)

        self.latx = self.rightVector.x
        self.latz = self.rightVector.z

        self.valid = True

    def xRange(self):
        return range(-self.width2, self.width2+1)

    def yRange(self):
        return range(0, self.height)

    def zRange(self):
        return range(0, self.depth)

    def toWorld(self, x, y, z):
        return Vec3(
            self.origin.x + self.latx * x + self.d.x * z,
            self.origin.y + y,
            self.origin.z + self.latz * x + self.d.z * z
        )

    def toWorldV3(self, v):
        return Vec3(
            self.origin.x + self.latx * v.x + self.d.x * v.z,
            self.origin.y + v.y,
            self.origin.z + self.latz * v.x + self.d.z * v.z
        )

    def dirToWorldV3(self, v):
        return Vec3(
            self.latx * v.x + self.d.x * v.z,
            v.y,
            self.latz * v.x + self.d.z * v.z
        )

    def blockAt(self, *argv):
        if len(argv) == 3:
            return self.bot.blockAt(self.toWorld(argv[0], argv[1], argv[2]))
        else:
            return self.bot.blockAt(self.toWorldV3(argv[0]))

    def allBlocks(self):
        blocks = []
        for z in self.zRange():
            for y in self.yRange():
                for x in self.xRange():
                    blocks.append(Vec3(x, y, z))
        return blocks

    def allBlocksWorld(self):
        blocks = []
        for z in self.zRange():
            for y in self.yRange():
                for x in self.xRange():
                    blocks.append(self.toWorld(x, y, z))
        return blocks

async def stripMine(bot, width=3, height=3, valrange=3):
    """Strip mining function"""
    z_torch = 0
    z = 0
    area = WorkArea(bot, width, height, 99999)
    
    if not area.valid:
        print("Could not create work area")
        return
    
    while True:
        while area.blocks_mined - area.last_break < area.break_interval:
            if not mining_safety_check(bot, area.toWorld(0, 0, z)):
                break
            
            # Mine the main tunnel
            for x in area.xRange():
                await mineColumn(bot, area, x, z, height)
                await floorMine(bot, area, x, z, 2)
                await ceilingMine(bot, area, x, z, height + 2)
            
            z += 1

async def mineColumn(bot, area, x, z, height):
    """Mine a column at given coordinates"""
    print(f'mineColumn(x:{x},z:{z},height:{height})')
    
    # Check if we need to do anything
    for y in range(0, height):
        if area.blockAt(x, y, z).displayName not in ignored_blocks:
            break
    else:
        return True

    # Check for infested blocks
    for y in range(0, height):
        block = area.blockAt(x, y, z)
        if hasattr(block, 'displayName') and block.displayName == "Infested Stone":
            print(f'Located {block.displayName}, aborting!')
            area.status = "* Silverfish *"
            return False

    # Try to mine the column
    for tries in range(0, 10):
        done = True
        for y in range(0, height):
            block = area.blockAt(x, y, z)
            if hasattr(block, 'displayName') and block.displayName not in ignored_blocks:
                done = False
                world_pos = area.toWorld(x, y, z)
                await mineBlock(bot, world_pos)
                area.blocks_mined += 1
                import time
                time.sleep(0.1)
        if done:
            break
    
    return True

async def floorMine(bot, area, x, z, depth):
    """Check for goodies in the floor"""
    if depth > 0:
        max_d = 0
        for d in range(1, depth + 1):
            block = area.blockAt(x, -d, z)
            if hasattr(block, 'displayName') and block.displayName in valuable_blocks:
                max_d = d
        
        if max_d > 0:
            # Mine valuable blocks
            for d in range(1, max_d + 1):
                world_pos = area.toWorld(x, -d, z)
                await mineBlock(bot, world_pos)
    
    return True

async def ceilingMine(bot, area, x, z, max_height):
    """Mine valuable blocks in ceiling"""
    max_y = 0
    for y in range(2, max_height):
        block = area.blockAt(x, y, z)
        if hasattr(block, 'displayName') and block.displayName in valuable_blocks:
            max_y = y
    
    if max_y > 0:
        for y in range(2, max_y + 1):
            block = area.blockAt(x, y, z)
            if hasattr(block, 'displayName') and block.displayName not in ignored_blocks:
                world_pos = area.toWorld(x, y, z)
                await mineBlock(bot, world_pos)
    
    return True

async def do_floor_mining(bot):
    """Do 3x3 floor mining around bot position"""
    try:
        # First equip iron pickaxe
        print("Equipping iron pickaxe...")
        for item in bot.inventory.items():
            if hasattr(item, 'displayName') and "Pickaxe" in item.displayName:
                await bot.equip(item, "hand")
                print(f"Equipped {item.displayName}")
                break
        
        pos = bot.entity.position
        mined_count = 0
        
        # Mine 3x3 area around bot
        for x_offset in [-1, 0, 1]:
            for z_offset in [-1, 0, 1]:
                for depth in [1, 2, 3]:  # Mine 3 blocks down
                    mine_pos = Vec3(
                        int(pos.x) + x_offset,
                        int(pos.y) - depth,
                        int(pos.z) + z_offset
                    )
                    print(f"Mining at {mine_pos.x}, {mine_pos.y}, {mine_pos.z}")
                    result = await mineBlock(bot, mine_pos)
                    if result:
                        mined_count += 1
        
        print(f"Floor mining complete! Blocks mined: {mined_count}")
    except Exception as e:
        print(f"Error in floor mining: {e}")
        import traceback
        traceback.print_exc()
