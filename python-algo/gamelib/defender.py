class Defender:
    def __init__(self, config):
        self.config = config
        self.game_state = None

    def update_state(self, game_state):
        self.game_state = game_state

        self.defend_left_right_side()

    def defend_left_right_side(self):
        locations = []

        # Horizontal line of defence
        for x in range(0, 3):
            locations.append((x, self.game_state.HALF_ARENA - 1))
            locations.append((self.game_state.ARENA_SIZE - 1 - x, self.game_state.HALF_ARENA - 1))

        # Diagonal line of defence
        for x in range(0, 3):
            locations.append((x, self.game_state.HALF_ARENA - 1 - x))
            locations.append((self.game_state.ARENA_SIZE - 1 - x, self.game_state.HALF_ARENA - 1 - x))

        # Spawn walls
        self.game_state.attempt_spawn(self.game_state.WALL, locations)

        # Spawn turret
        locations = []
        locations.append((2, self.game_state.HALF_ARENA - 2))
        locations.append((self.game_state.ARENA_SIZE - 3, self.game_state.HALF_ARENA - 2))
        self.game_state.attempt_spawn(self.game_state.TURRET, locations)
