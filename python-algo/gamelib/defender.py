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
        self.scored_on_locations = []
        self.damaged_turrets = {}

    def update_state(self, game_state, scored_on_locations, damaged_turrets):
        self.game_state = game_state
        self.scored_on_locations = scored_on_locations
        self.damaged_turrets = list(sorted(list(damaged_turrets.items()), key=lambda x: x[1], reverse=True))

        self.defend_left_right_side()
        self.defend_center_region()

        # Now build reactive defenses based on where the enemy scored
        self.build_reactive_defense()

        self.build_more_walls()

        self.support_damaged_structures()

        self.build_last_resort_walls()

        self.build_remaining_front_walls()

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
            self.game_state.attempt_spawn(TURRET, (x, self.game_state.HALF_ARENA - 2))
            self.game_state.attempt_spawn(WALL, (x, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((x, self.game_state.HALF_ARENA - 1))

        # Build supports afterwards
        for x in x_coords:
            self.game_state.attempt_spawn(SUPPORT, (x, self.game_state.HALF_ARENA - 3))

    def build_reactive_defense(self):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build turret one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1] + 2]
            self.game_state.attempt_spawn(TURRET, build_location)

    def support_damaged_structures(self):
        # Try 4 different positions
        deltas = ((0, -1), (1, 0), (-1, 0), (0, 1))
        for damaged_turret in self.damaged_turrets:
            for dx, dy in deltas:
                success = self.game_state.attempt_spawn(SUPPORT,
                                                        (damaged_turret[0][0] + dx, damaged_turret[0][1] + dy))
                if success:
                    break

    def build_more_walls(self):
        x_coords = [6, 22, 10, 18, 14]

        # Build turrets first
        for x in x_coords:
            self.game_state.attempt_spawn(WALL, (x - 1, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_spawn(WALL, (x + 1, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((x - 1, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((x + 1, self.game_state.HALF_ARENA - 1))

    def build_last_resort_walls(self):
        for x in range(7):
            self.game_state.attempt_spawn(WALL, (8 + x, 5))
        for x in range(5):
            self.game_state.attempt_spawn(WALL, (13 + x, 3))
        for x in range(2):
            self.game_state.attempt_spawn(WALL, (12 + x, 1))

    def build_remaining_front_walls(self):
        for i in range(13):
            self.game_state.attempt_spawn(WALL, (i, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_spawn(WALL, (27 - i, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((i, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((27 - i, self.game_state.HALF_ARENA - 1))
