import random
from math import floor

import gamelib

class Attacker:


    def __init__(self, config):
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

    def offense_decision(self, game_state, best_location, past_data_stored):
        """
        :param past_data_stored: the dataStorageUnit presented in the system
        :param game_state:
        :param best_location: a dictionary containing a min_value for keys and an array of locations
        :return:
        """
        safest_path_val = -10
        # gamelib.debug_write("dictionary location is {}".format(len(best_location.keys())))
        if game_state.get_resource(MP, 0) > past_data_stored.min_mobile_units_needed:
            for min_val in min(best_location.keys()):
                if min_val == 0:
                    # attack the weakness immediately
                    gamelib.debug_write("spawn scouts")
                    game_state.attempt_spawn(SCOUT, best_location.get(min_val), floor(game_state.get_resource(MP, 0)))
                    break
                else:
                    if safest_path_val < 0 or min_val < safest_path_val:
                        safest_path_val = min_val

            if safest_path_val > 0:
                tuple_combo = self.get_health_for_combo(game_state)
                if best_location.get(safest_path_val) is not None and tuple_combo[2] >= safest_path_val:
                    gamelib.debug_write("bes location is {}".format(safest_path_val))
                    self.spawn_demo_scout_combo(self.get_a_location(best_location.get(safest_path_val)), game_state, tuple_combo)
        else:
            # no enough resources to start an offense, for now just sent an interceptor on highest chance of attack
            intercept_location = past_data_stored.chances_of_opponent_attack(game_state)
            if len(intercept_location) > 0:
                game_state.attempt_spawn(INTERCEPTOR, intercept_location, 1)


    def get_a_location(self, location_array):
        """
        For now, just find a random location, in the future might need better management
        :param location_array: an array of locations
        :return: a location
        """
        deploy_index = random.randint(0, len(location_array) - 1)
        return location_array[deploy_index]

    def get_health_for_combo(self, game_state):

        if game_state.get_resource(SP, 1) > 12:
            # high chance of an upgraded turret
            demolisher_count = 2
        else:
            demolisher_count = 1

        scout_count = floor(game_state.get_resource(MP, 0) - demolisher_count * 3)
        total_health_val = scout_count * 15 + demolisher_count * 5

        return tuple((scout_count, demolisher_count, total_health_val))


    def spawn_demo_scout_combo(self, location, game_state, tuple_combo):
        """
        spawn squad of mobile units consisting of demolisher and scout

        :param location: a coordination
        :param game_state: current game state
        :param tuple_combo: tuple containing (scout_count, demolisher_count)
        :return:
        """

        game_state.attempt_spawn(DEMOLISHER, location, tuple_combo[1])

        if location[0] <= 13:
            if location[0] == 13:
                new_location = [location[0]-1, location[1]+1]
            else:
                new_location = [location[0]+1, location[1]-1]
            game_state.attempt_spawn(SCOUT, new_location, tuple_combo[0])
        else:
            if location[0] == 14:
                new_location = [location[0]+1, location[1]+1]
            else:
                new_location = [location[0]-1, location[1]-1]
            game_state.attempt_spawn(SCOUT, new_location, tuple_combo[0])
        gamelib.debug_write("new location to spawn scout at: {}".format(new_location))

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
        while game_state.get_resource(MP, 0) >= game_state.type_cost(INTERCEPTOR)[MP] and len(deploy_locations) > 0:
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