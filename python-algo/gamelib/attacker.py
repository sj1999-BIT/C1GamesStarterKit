import random

import gamelib

class Attacker:


    def __init__(self, config, game_state):
        self.game_state = game_state
        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, MP, SP
        WALL = config["unitInformation"][0]["shorthand"]
        SUPPORT = config["unitInformation"][1]["shorthand"]
        TURRET = config["unitInformation"][2]["shorthand"]
        SCOUT = config["unitInformation"][3]["shorthand"]
        DEMOLISHER = config["unitInformation"][4]["shorthand"]
        INTERCEPTOR = config["unitInformation"][5]["shorthand"]
        MP = 1
        SP = 0

    def offense_decision(self, game_state, best_location):
        """
        :param game_state:
        :param best_location: a dictionary containing a min_value for keys and an array of locations
        :return:
        """
        safest_path_val = -10
        for min_val in best_location.keys():
            if min_val == 0:
                # attack the weakness immediately
                game_state.attempt_spawn(SCOUT, best_location.get(min_val), 1000)
                break
            else:
                if safest_path_val < 0 or min_val < safest_path_val:
                    safest_path_val = min_val
        if self.game_state.get_resource(MP, 0) > 16:
            # [[13, 0], [14, 0], [0, 13], [0, 14]]
            # Only spawn Scouts every other turn
            # Sending more at once is better since attacks can only hit a single scout at a time
            self.spawn_demo_scout_combo(self.get_a_location(best_location.get(safest_path_val)))

    def get_a_location(self, location_array):
        """
        For now, just find a random location, in the future might need better management
        :param location_array: an array of locations
        :return: a location
        """
        deploy_index = random.randint(0, len(location_array) - 1)
        return location_array[deploy_index]

    def spawn_demo_scout_combo(self, location):
        """
        spawn squad of mobile units consisting of demolisher and scout
        :param location: a coordination
        :return: void
        """

        if self.game_state.get_resource(SP, 1) > 12:
            # high chance of an upgraded turret
            self.game_state.attempt_spawn(DEMOLISHER, location, 2)
        else:
            self.game_state.attempt_spawn(DEMOLISHER, location, 1)

        if location[0] <= 13:
            if location[0] == 13:
                new_location = [location[0]-1, location[1]+1]
            else:
                new_location = [location[0]+1, location[1]-1]
            self.game_state.attempt_spawn(SCOUT, new_location, 1000)
        else:
            if location[0] == 14:
                new_location = [location[0]+1, location[1]+1]
            else:
                new_location = [location[0]-1, location[1]-1]
            self.game_state.attempt_spawn(SCOUT, new_location, 1000)
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