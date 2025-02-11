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
        For defense we will use a spread out layout and some interceptors early on.
        We will place turrets near locations the opponent managed to score on.
        For offense we will use long range demolishers if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Scouts to try and score quickly.
        """
        # # First, place basic defenses
        # self.build_defences(game_state)
        # # Lastly, if we have spare SP, let's build some supports
        # support_locations = [[13, 2], [14, 2], [13, 3], [14, 3]]
        # game_state.attempt_spawn(SUPPORT, support_locations)
        observer = Observer(self.config, game_state, self.damaged_turrets, self.dead_turrets,
                            self.past_history_stored.cur_interceptor_location, game_state.get_resource(MP, 1))
        self.past_history_stored.learning_and_update_info(game_state, self.scored_on_locations, observer)
        gamelib.debug_write("intercept-strategy")
        if len(self.scored_on_locations) > 0:
            self.attacker.interception_strategy(game_state, self.past_history_stored, self.scored_on_locations[0])
        gamelib.debug_write("defender-update")
        self.defender.update_state(game_state, self.scored_on_locations, self.damaged_turrets, self.past_history_stored)
        # creation of the three objects
        gamelib.debug_write("offensive-strategy")
        self.attacker.offense_decision(game_state, observer.generate_our_attacker_location(game_state),
                                       observer.min_health_for_attack(game_state), self.past_history_stored)

        gamelib.debug_write("current game SP {}".format(game_state.get_resource(SP, 0)))


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
        damages = events["damage"]
        deaths = events["death"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

        for damage in damages:
            location = tuple(damage[0])
            damage_taken = damage[1]
            unit_owner_self = True if damage[4] == 1 else False
            unit_is_turret = True if damage[2] == 2 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if unit_owner_self and unit_is_turret:
                if tuple(location) in self.damaged_turrets:
                    self.damaged_turrets[tuple(location)] += damage_taken
                else:
                    self.damaged_turrets[tuple(location)] = damage_taken

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



if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()