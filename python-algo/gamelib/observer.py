import gamelib

class Observer:
    def __init__(self, config, game_state, damaged_turrets, dead_turrets, omitted_spawn_locations, opponent_mp):
        self.game_state = game_state
        self.damaged_turrets = damaged_turrets
        self.dead_turrets = dead_turrets
        self.omitted_spawn_locations = omitted_spawn_locations
        self.opponent_mp = opponent_mp

        global WALL, SUPPORT, TURRET, SCOUT, DEMOLISHER, INTERCEPTOR, REMOVE, UPGRADE, STRUCTURE_TYPES, ALL_UNITS, UNIT_TYPE_TO_INDEX, MP, SP
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

    def min_health_for_attack(self, game_state):
        """
        This function will return health needed to reach target edge without considering shielding / destruction of walls / turrets
        It gets the path the unit will take then checks the damage along that path
        """
        damages = {}
        location_options = game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        location_options = self.filter_blocked_locations(location_options, game_state)
        location_options = self.filter_omitted_locations(location_options, game_state)

        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            if len(path) < 2:
                continue
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, game_state.config).damage_i
                """
                all_support_locations = self.game_state.game_map.get_locations_in_range(path_location, gamelib.GameUnit(SUPPORT, self.game_state.config).shieldRange)

                # Accumulates shield amount from support structures around location that can support each location
                for support_location in all_support_locations:
                    for unit in self.game_state.game_map[support_location]:
                        if unit.shieldPerUnit > 0 and unit.player_index == 0:
                            damage -= unit.shieldPerUnit
                """
            # Adds location for the key corresponding to damage
            if damages.get(damage) is None:
                damages[damage] = [location]
            else:
                temp = damages[damage]
                temp.append(location)
                damages[damage] = temp

        # return the dictionary of damages and locations
        gamelib.debug_write("Debug: {}".format(damages))
        if len(damages) == 0:
            gamelib.debug_write("DANGER")
        return damages

    def generate_our_attacker_location(self, game_state):
        """
        This function will return spawn locations that will not take any damage for friendly mobile units.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        spawn_location = []
        location_options = game_state.game_map.get_edge_locations(
            game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        location_options = self.filter_blocked_locations(location_options, game_state)

        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET,
                                                                                             game_state.config).damage_i
            if damage == 0 and len(path) > 2:
                spawn_location.append(location)

        # Now just return the spawn locations that do not take damage
        return spawn_location

    def our_weakness_location(self, game_state):
        """
        This function will return spawn locations that will not take any damage for enemy mobile units.
        Works similar to function for friendly units
        """
        location_options = game_state.game_map.get_edge_locations(
            game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)

        # Remove locations that are blocked by enemy structures
        # since we can't deploy units there.
        location_options = self.filter_blocked_locations(location_options, game_state)

        vulnerable_locations = []

        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of friendly turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 1)) * gamelib.GameUnit(TURRET,
                                                                                             game_state.config).damage_i
            if damage == 0 and len(path) > 2:
                vulnerable_locations.append(path_location[-4])

        # Now just return the location that does not take damage
        return vulnerable_locations

    def get_damaged_structures(self, game_state):
        """
        This function will return a dictionary of locations and damage of damaged friendly turrets.
        """
        return self.damaged_turrets

    def get_destroyed_structures(self, game_state):
        """
        This function will return a list of locations of destroyed friendly turrets.
        """
        return self.dead_turrets

    def spawn_location_for_intercepter(self, game_state):
        """
        This function will return spawn locations for intercepters. It first calculates the most probable enemy spawn location, then
        the most suitable friendly spawn location for intercepting the attack.
        """
        intercepter_spawn_location = []
        location_options = game_state.game_map.get_edge_locations(
            game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)

        # Remove locations that are blocked by enemy structures
        # since we can't deploy units there.
        location_options = self.filter_blocked_locations(location_options, game_state)

        vulnerable_locations = []

        min_damage = 10000000
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            edge = path[-1]

            damage = 0
            for path_location in path:
                # Get number of friendly turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 1)) * gamelib.GameUnit(TURRET,game_state.config).damage_i
            if len(path) < 2:
                continue
            if damage < min_damage:
                min_damage = damage
                intercepter_spawn_location.clear()
                intercepter_spawn_location.append(edge)
            elif damage == min_damage:
                intercepter_spawn_location.append(edge)

        # Now just return the location that does not take damage
        return intercepter_spawn_location

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def filter_omitted_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            path = game_state.find_path_to_edge(location)
            edge = path[-1]
            ommit = False
            for ommited_location in self.omitted_spawn_locations:
                distance = game_state.game_map.distance_between_locations(list(ommited_location), edge)
                if distance <= 2:
                    ommit = True
            if not ommit:
                filtered.append(location)
        return filtered

    def tilted_formation(self, game_state):
        location_options = game_state.game_map.get_edge_locations(
            game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)

        location_count = []

        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            for path_location in path:
                if path_location[1] == 14:
                    location_count.append(path_location[0])
                    break
        all_left = True
        all_right = True
        for location in location_count:
            if location <= 13:
                all_right = False
            if location > 13:
                all_left = False

        average = sum(location_count) / len(location_count)

        if all_right or all_left:
            return average
        else:
            return -1

    def useless_turrets(self, game_state):
        location_options = game_state.game_map.get_edge_locations(
            game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)

        useful_turrets = set()
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            if path == None:
                continue
            for path_location in path:
                defenders = game_state.get_attackers(path_location, 1)
                for defender in defenders:
                    useful_turrets.add(tuple([defender.x, defender.y]))
        friendly_turrets = set()

        all_locations = game_state.game_map.get_locations_in_range([13,13], 15)

        for location in all_locations:
            x, y = map(int, location)
            unit = game_state.game_map[x, y]
            if len(unit) == 0:
                continue
            else:
                unit = unit[0]
            gamelib.debug_write(unit)
            gamelib.debug_write(unit.player_index)
            gamelib.debug_write(unit.unit_type)
            if unit.player_index == 0 and unit.unit_type == "DF":
                friendly_turrets.add(tuple([x, y]))

        useless_turrets = friendly_turrets.difference(useful_turrets)
        useless_turrets = list(useless_turrets)

        return useless_turrets

    def average_opponent_attack_mp(self):
        return sum(self.opponent_mp)/len(self.opponent_mp)
