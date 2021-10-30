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
        self.cur_attacked_location = []

    def offense_decision(self, game_state, best_location, past_data_stored):
        """
        :param past_data_stored: the dataStorageUnit presented in the system
        :param game_state:
        :param best_location: a dictionary containing a min_value for keys and an array of locations
        :return:
        """
        # only record the attacked location this round
        self.cur_attacked_location = []
        safest_path_val = -10
        # gamelib.debug_write("dictionary location is {}".format(len(best_location.keys())))
        if game_state.get_resource(MP, 0) > past_data_stored.min_mobile_units_needed:
            for min_val in best_location:

                # check if the locations present are not recorded as blacklist
                list_of_locations = best_location.get(min_val)

                if len(list_of_locations) > 0:
                    for location in list_of_locations:
                        if location not in past_data_stored.blacklisted_location:
                            if min_val == 0:
                                # attack the weakness immediately
                                gamelib.debug_write("spawn scouts")
                                game_state.attempt_spawn(SCOUT, self.get_a_location(best_location.get(min_val)), floor(game_state.get_resource(MP, 0)))
                                self.cur_attacked_location.extend([self.get_a_location(best_location.get(min_val)), ])
                                gamelib.debug_write("47 cur_attacked_location is {}".format(self.cur_attacked_location))
                                break
                            else:
                                if safest_path_val < 0 or min_val < safest_path_val:
                                    safest_path_val = min_val

            if safest_path_val > 0:
                tuple_combo = self.get_health_for_combo(game_state)
                if best_location.get(safest_path_val) is not None and len(best_location.get(safest_path_val)) > 0:
                    target_spawn_location = self.get_a_location(best_location.get(safest_path_val))
                    if tuple_combo[2] > safest_path_val:
                        # the combo can punch through opponent frontline
                        gamelib.debug_write("bes location is {}".format(safest_path_val))
                        self.spawn_demo_scout_combo(target_spawn_location, game_state, tuple_combo)
                    else:
                        demolisher_count = self.demolish_strategy(game_state, past_data_stored)
                        # since we cannot tell if the demolisher is effective, we can only guess
                        if demolisher_count > 2:
                            game_state.attempt_spawn(DEMOLISHER, target_spawn_location, demolisher_count)
                            self.cur_attacked_location.extend([target_spawn_location, ])
                            gamelib.debug_write("67 cur_attacked_location is {}".format(self.cur_attacked_location))

            past_data_stored.previous_attack_location = self.cur_attacked_location

    def demolish_strategy(self, game_state, past_data_stored):
        """
        utilise a percentage of our current resources to create a team only for demolisher
        :param game_state:
        :param past_data_stored:
        :return:
        """
        MP_owned = game_state.get_resource(MP, 0)
        return floor(MP_owned * past_data_stored.percent_MP_for_demolition / 3)


    def interception_strategy(self, game_state, past_data_stored):

        # assume opponent will not attack
        if game_state.get_resource(MP, 1) < past_data_stored.min_MP_enemy_needed:
            pass

        # find highest possible point of interception
        highest_val = -10
        intercept_location = None
        # dictionary chance_of_attack has tuple as key and int as val
        if past_data_stored.chance_of_attack is not None:
            for location in past_data_stored.chance_of_attack:
                chance = past_data_stored.chance_of_attack.get(location)
                if chance > highest_val:
                    highest_val = chance
                    intercept_location = location

        # idea is that we only attack if we do not have enough SP or too much MP
        if intercept_location is not None and game_state.get_resource(SP, 0) < 5 \
                and game_state.get_resource(MP, 0) > past_data_stored.max_MP_enemy_needed:
            intercept_location = list(intercept_location)
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
        self.cur_attacked_location.extend([location, ])
        gamelib.debug_write("141 cur_attacked_location is {}".format(self.cur_attacked_location))

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
        self.cur_attacked_location.extend([new_location, ])
        gamelib.debug_write("156 cur_attacked_location is {}".format(self.cur_attacked_location))
        gamelib.debug_write("new location to spawn scout at: {}".format(new_location))

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