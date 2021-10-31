import gamelib
import random
import math
import warnings
from sys import maxsize
import json

from gamelib.attacker import Attacker
from gamelib.observer import Observer

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0
        # This is a good place to do initial setup
        self.scored_on_locations = []
        self.damaged_turrets = {}
        self.dead_turrets = set()
        self.useless_turrets = []
        self.omitted_spawn_locations = set()
        self.opponent_mp = []
        self.defender = gamelib.Defender(config)
        self.attacker = gamelib.Attacker(self.config)
        self.past_history_stored = gamelib.DataStorage(config)

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        # game_state.attempt_spawn(DEMOLISHER, [24, 10], 3)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        # game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.our_strategy(game_state)

        game_state.submit_turn()
        self.dead_turrets = set()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def our_strategy(self, game_state):
        """
        First, we will update the observer and data storage unit
        Then we will place any interceptors
        Then we will update our defence
        Then we will construct our attack if necessary
        :param game_state:
        :return:
        """
        observer = Observer(self.config, game_state, self.damaged_turrets, self.dead_turrets,
                            self.omitted_spawn_locations, self.opponent_mp)
        self.past_history_stored.learning_and_update_info(game_state, self.scored_on_locations, observer)
        self.past_history_stored.is_attack_effective()

        self.attacker.interception_strategy(game_state, self.past_history_stored,
                                            observer.spawn_location_for_intercepter(game_state))

        # creation of the three objects
        attacker = Attacker(self.config)
        observer = Observer(self.config, game_state, self.damaged_turrets, self.dead_turrets, self.omitted_spawn_locations, self.opponent_mp)
        self.defender.update_state(game_state, self.scored_on_locations, self.damaged_turrets)
        self.attacker.offense_decision(game_state, observer.observer.min_health_for_attack(game_state), self.past_history_stored)


    def build_defences(self, game_state):
        """
        Build basic defenses using hardcoded locations.
        Remember to defend corners and avoid placing units in the front where enemy demolishers can attack them.
        """
        # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
        # More community tools available at: https://terminal.c1games.com/rules#Download

        # Place turrets that attack enemy units
        turret_locations = [[0, 13], [27, 13], [8, 11], [19, 11], [13, 11], [14, 11]]
        # attempt_spawn will try to spawn units if we have resources, and will check if a blocking unit is already there
        game_state.attempt_spawn(TURRET, turret_locations)

        # Place walls in front of turrets to soak up damage for them
        wall_locations = [[8, 12], [19, 12]]
        game_state.attempt_spawn(WALL, wall_locations)
        # upgrade walls so they soak more damage
        game_state.attempt_upgrade(wall_locations)

    def stall_with_interceptors(self, game_state):
        """
        Send out interceptors at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)

        # While we have remaining MP to spend lets send out interceptors randomly.
        while game_state.get_resource(MP) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]

            game_state.attempt_spawn(INTERCEPTOR, deploy_location)
            """
            We don't have to remove the location since multiple mobile 
            units can occupy the same space.
            """

    def least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET,
                                                                                             game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x=None, valid_y=None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (
                            valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at in json-docs.html in the root of the Starterkit.
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        friendly_turrets = state["p2Units"][2]
        deaths = events["death"]
        spawns = events["spawn"]
        self.opponent_mp.append(state["p2Stats"][2])

        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

        self.damaged_turrets.clear()
        for turret in friendly_turrets:
            location = (turret[0], turret[1])
            damage = 75 - turret[2]
            if damage > 0:
                self.damaged_turrets[tuple(location)] = damage

        for death in deaths:
            location = tuple(death[0])
            unit_owner_self = True if death[3] == 1 else False
            unit_is_turret = True if death[1] == 2 else False
            removed_by_owner = death[4]
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if unit_owner_self and not removed_by_owner and unit_is_turret:
                # Removes it from the damaged dict
                self.damaged_turrets.pop(tuple(location), None)
                self.dead_turrets.add(location)

        opponent_attacked = False

        for spawn in spawns:
            location = tuple(spawn[0])
            is_intercepter = True if spawn[1] == 5 else False
            is_scout = True if spawn[1] == 3 else False
            is_demolisher = True if spawn[1] == 4 else False
            unit_owner_self = True if spawn[3] == 1 else False
            if is_intercepter and not unit_owner_self:
                self.omitted_spawn_locations.add(location)
            if (is_scout or is_demolisher) and not unit_owner_self:
                opponent_attacked = True

        if len(spawns) == 0:
            opponent_attacked = True

        if not opponent_attacked:
            self.opponent_mp.pop()

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()