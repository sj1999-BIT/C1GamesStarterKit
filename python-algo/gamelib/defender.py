def set_constants(config):
    global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, REMOVE, UPGRADE, STRUCTURE_TYPES, ALL_UNITS, UNIT_TYPE_TO_INDEX
    UNIT_TYPE_TO_INDEX = {}
    WALL = config["unitInformation"][0]["shorthand"]
    UNIT_TYPE_TO_INDEX[WALL] = 0
    SUPPORT = config["unitInformation"][1]["shorthand"]
    UNIT_TYPE_TO_INDEX[SUPPORT] = 1
    TURRET = config["unitInformation"][2]["shorthand"]
    UNIT_TYPE_TO_INDEX[TURRET] = 2
    SCOUT = config["unitInformation"][3]["shorthand"]
    UNIT_TYPE_TO_INDEX[SCOUT] = 3
    DEMOLISHER = config["unitInformation"][4]["shorthand"]
    UNIT_TYPE_TO_INDEX[DEMOLISHER] = 4
    INTERCEPTOR = config["unitInformation"][5]["shorthand"]
    UNIT_TYPE_TO_INDEX[INTERCEPTOR] = 5
    REMOVE = config["unitInformation"][6]["shorthand"]
    UNIT_TYPE_TO_INDEX[REMOVE] = 6
    UPGRADE = config["unitInformation"][7]["shorthand"]
    UNIT_TYPE_TO_INDEX[UPGRADE] = 7

    ALL_UNITS = [SCOUT, DEMOLISHER, INTERCEPTOR, WALL, SUPPORT, TURRET]
    STRUCTURE_TYPES = [WALL, SUPPORT, TURRET]

class Defender:
    def __init__(self, config):
        self.config = config
        set_constants(config)
        self.game_state = None

    def update_state(self, game_state):
        self.game_state = game_state

        self.defend_left_right_side()
        self.defend_center_region()

    def defend_left_right_side(self):
        locations = []
        # Spawn walls
        # Horizontal line of defence
        for x in range(0, 3):
            locations.append((x, self.game_state.HALF_ARENA - 1))
            locations.append((self.game_state.ARENA_SIZE - 1 - x, self.game_state.HALF_ARENA - 1))

        # Diagonal line of defence
        for x in range(0, 3):
            locations.append((x, self.game_state.HALF_ARENA - 1 - x))
            locations.append((self.game_state.ARENA_SIZE - 1 - x, self.game_state.HALF_ARENA - 1 - x))

        self.game_state.attempt_spawn(WALL, locations)

        # Spawn turret
        locations = []
        locations.append((2, self.game_state.HALF_ARENA - 2))
        locations.append((self.game_state.ARENA_SIZE - 3, self.game_state.HALF_ARENA - 2))
        self.game_state.attempt_spawn(TURRET, locations)

    def defend_center_region(self):
        x_coords = [6, 22, 10, 18, 14]

        # Build turrets first
        for x in x_coords:
            self.game_state.attempt_spawn(TURRET, [(x, self.game_state.HALF_ARENA - 2)])

        # Build supports afterwards
        for x in x_coords:
            self.game_state.attempt_spawn(SUPPORT, [(x, self.game_state.HALF_ARENA - 3)])
