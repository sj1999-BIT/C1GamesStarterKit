import random
import gamelib

def set_constants(config):
    global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, REMOVE, UPGRADE, STRUCTURE_TYPES, ALL_UNITS, UNIT_TYPE_TO_INDEX, MP, Sp
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
    MP = 1
    SP = 0

    ALL_UNITS = [SCOUT, DEMOLISHER, INTERCEPTOR, WALL, SUPPORT, TURRET]
    STRUCTURE_TYPES = [WALL, SUPPORT, TURRET]


class Defender:
    def __init__(self, config):
        self.config = config
        set_constants(config)
        self.game_state = None
        self.scored_on_locations = []
        self.damaged_turrets = {}
        self.analytics = None


        self.location_to_be_left_empty = (14, 14)
        self.previous_emptied_location = self.location_to_be_left_empty

    def controlled_wall_spawn(self, location):
        if location != self.location_to_be_left_empty and location != self.previous_emptied_location:
            self.game_state.attempt_spawn(WALL, location)

    def update_state(self, game_state, scored_on_locations, damaged_turrets, analytics):

        self.game_state = game_state
        self.analytics = analytics
        self.scored_on_locations = scored_on_locations
        self.damaged_turrets = list(sorted(list(damaged_turrets.items()), key=lambda x: x[1], reverse=True))
        x = random.randrange(3, self.game_state.ARENA_SIZE - 3)

        while self.game_state.contains_stationary_unit((x, self.game_state.HALF_ARENA - 3)):
            x = random.randrange(3, self.game_state.ARENA_SIZE - 3)
        self.game_state.attempt_remove((x, self.game_state.HALF_ARENA - 2))
        self.location_to_be_left_empty = (x, self.game_state.HALF_ARENA - 2)

        #self.locations_to_be_removed = analytics.locations_of_useless_turret

        if self.analytics.is_delay_attack_mode:
            self.build_delay_attack_structures()

        self.defend_frontline_corners()

        self.defend_frontline_center()

        self.upgrade_frontline_center()

        self.defend_remaining_frontline()

        self.defend_center_region()

        self.support_damaged_structures()

        self.upgrade_all_turrets_and_support()

        self.previous_emptied_location = self.location_to_be_left_empty
        #
        # self.build_last_resort_walls()
        #
        # self.build_remaining_front_walls()

        # self.defend_left_right_side()
        # self.defend_center_region()

    def defend_frontline_corners(self):

        # Build walls first
        for x in range(0, 3):
            self.controlled_wall_spawn((x, self.game_state.HALF_ARENA - 1))
            self.controlled_wall_spawn((self.game_state.ARENA_SIZE - 1 - x, self.game_state.HALF_ARENA - 1))

        # Build turrets next
        self.game_state.attempt_spawn(TURRET, (1, self.game_state.HALF_ARENA - 2))
        self.game_state.attempt_spawn(TURRET, (self.game_state.ARENA_SIZE - 2, self.game_state.HALF_ARENA - 2))

        # Build side walls next
        self.controlled_wall_spawn((2, self.game_state.HALF_ARENA - 2))
        self.controlled_wall_spawn((self.game_state.ARENA_SIZE - 3, self.game_state.HALF_ARENA - 2))

        # Upgrade walls last
        for x in range(0, 3):
            self.game_state.attempt_upgrade((x, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((self.game_state.ARENA_SIZE - 1 - x, self.game_state.HALF_ARENA - 1))

    def defend_frontline_center(self):
        # Build a few walls first
        for dx in range(3):
            self.controlled_wall_spawn(((self.game_state.ARENA_SIZE - 1) // 2 - dx, self.game_state.HALF_ARENA - 2))
            self.controlled_wall_spawn(((self.game_state.ARENA_SIZE - 1) // 2 + dx, self.game_state.HALF_ARENA - 2))

        # Build turret next

        self.game_state.attempt_spawn(TURRET, ((self.game_state.ARENA_SIZE - 1) // 2, self.game_state.HALF_ARENA - 3))

        # Build remaining walls last
        for dx in range(3, 6):
            self.controlled_wall_spawn(((self.game_state.ARENA_SIZE - 1) // 2 - dx, self.game_state.HALF_ARENA - 2))
            self.controlled_wall_spawn(((self.game_state.ARENA_SIZE - 1) // 2 + dx, self.game_state.HALF_ARENA - 2))

    def upgrade_frontline_center(self):
        # Upgrade frontline center walls
        for dx in range(6):
            self.game_state.attempt_upgrade(
                ((self.game_state.ARENA_SIZE - 1) // 2 - dx, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade(
                ((self.game_state.ARENA_SIZE - 1) // 2 + dx, self.game_state.HALF_ARENA - 1))

    def defend_remaining_frontline(self):
        # Build remaining walls
        for x in range(8, 2, -1):
            self.controlled_wall_spawn((x, self.game_state.HALF_ARENA - 2))
            self.controlled_wall_spawn((self.game_state.ARENA_SIZE - 1 - x, self.game_state.HALF_ARENA - 2))

        # Upgrade remaining walls
        for x in range(8, 2, -1):
            self.game_state.attempt_upgrade((x, self.game_state.HALF_ARENA - 2))
            self.game_state.attempt_upgrade((self.game_state.ARENA_SIZE - 1 - x, self.game_state.HALF_ARENA - 2))


    def build_delay_attack_structures(self):
        # Build delay attack walls
        for x in range(7):
            self.game_state.attempt_spawn(WALL, (8 + x, 5))
        for x in range(5):
            self.game_state.attempt_spawn(WALL, (13 + x, 3))
        for x in range(2):
            self.game_state.attempt_spawn(WALL, (12 + x, 1))

        # Build left interceptor zone
        for dx in range(3):
            self.game_state.attempt_spawn(WALL, (3 + dx, self.game_state.HALF_ARENA - 4))
        self.game_state.attempt_spawn(WALL, (6, self.game_state.HALF_ARENA - 5))
        for dy in range(3):
            self.game_state.attempt_spawn(WALL, (7, self.game_state.HALF_ARENA - 6 - dy))

        # Build right interceptor zone
        for dx in range(3):
            self.game_state.attempt_spawn(WALL, (self.game_state.ARENA_SIZE - 4 - dx, self.game_state.HALF_ARENA - 4))
        self.game_state.attempt_spawn(WALL, (self.game_state.ARENA_SIZE - 7, self.game_state.HALF_ARENA - 5))
        for dy in range(3):
            self.game_state.attempt_spawn(WALL, (self.game_state.ARENA_SIZE - 8, self.game_state.HALF_ARENA - 6 - dy))

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
            self.game_state.attempt_spawn(TURRET, (x, self.game_state.HALF_ARENA - 3))
            self.controlled_wall_spawn((x, self.game_state.HALF_ARENA - 2))
            self.game_state.attempt_upgrade((x, self.game_state.HALF_ARENA - 2))

        # Build supports afterwards
        for x in x_coords:
            self.game_state.attempt_spawn(SUPPORT, (x, self.game_state.HALF_ARENA - 4))

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
        deltas = (0, -1)
        for damaged_turret in self.damaged_turrets:
            self.game_state.attempt_spawn(SUPPORT, (damaged_turret[0][0] + deltas[0], damaged_turret[0][1] + deltas[1]))

    def build_more_walls(self):
        x_coords = [6, 22, 10, 18, 14]

        # Build turrets first
        for x in x_coords:
            self.controlled_wall_spawn((x - 1, self.game_state.HALF_ARENA - 1))
            self.controlled_wall_spawn((x + 1, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((x - 1, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((x + 1, self.game_state.HALF_ARENA - 1))

    def build_last_resort_walls(self):
        for x in range(7):
            self.controlled_wall_spawn((8 + x, 5))
        for x in range(5):
            self.controlled_wall_spawn((13 + x, 3))
        for x in range(2):
            self.controlled_wall_spawn((12 + x, 1))

    def build_remaining_front_walls(self):
        for i in range(10):
            self.controlled_wall_spawn((i, self.game_state.HALF_ARENA - 1))
            self.controlled_wall_spawn((27 - i, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((i, self.game_state.HALF_ARENA - 1))
            self.game_state.attempt_upgrade((27 - i, self.game_state.HALF_ARENA - 1))

    def upgrade_all_turrets_and_support(self):
        locations = []
        # Build turrets next
        self.game_state.attempt_upgrade((1, self.game_state.HALF_ARENA - 2))
        locations.extend([list((1, self.game_state.HALF_ARENA - 2)), ])
        self.game_state.attempt_upgrade((self.game_state.ARENA_SIZE - 2, self.game_state.HALF_ARENA - 2))
        locations.extend([list((self.game_state.ARENA_SIZE - 2, self.game_state.HALF_ARENA - 2)), ])
        self.game_state.attempt_upgrade(((self.game_state.ARENA_SIZE - 1) // 2, self.game_state.HALF_ARENA - 3))
        locations.extend([list(((self.game_state.ARENA_SIZE - 1) // 2, self.game_state.HALF_ARENA - 3)), ])

        x_coords = [6, 22, 10, 18, 14]

        # Build turrets first
        for x in x_coords:
            self.game_state.attempt_upgrade((x, self.game_state.HALF_ARENA - 3))
            locations.extend([list((x, self.game_state.HALF_ARENA - 3)), ])

        for location in locations:
            self.game_state.attempt_upgrade((location[0], location[1] - 1))