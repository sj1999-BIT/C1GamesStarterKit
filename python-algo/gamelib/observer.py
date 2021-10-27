import gamelib

class Observer:
    def __init__(self, config, game_state):
        self.game_state = game_state

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


    #doesn't account for destruction of buildings, walls
    def min_health_for_attack(self):
        """
        This function will return health needed to reach target edge without considering shielding / destruction of walls / turrets
        It gets the path the unit will take then checks the damage along that path
        """
        damages = {}
        location_options = self.game_state.game_map.get_edge_locations(
            self.game_state.game_map.BOTTOM_LEFT) + self.game_state.game_map.get_edge_locations(self.game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own structures
        # since we can't deploy units there.
        location_options = self.filter_blocked_locations(location_options, self.game_state)

        # Get the damage estimate each path will take
        for location in location_options:
            path = self.game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of enemy turrets that can attack each location and multiply by turret damage
                damage += len(self.game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(TURRET, self.game_state.config).damage_i
                """
                all_support_locations = self.game_state.game_map.get_locations_in_range(path_location, gamelib.GameUnit(SUPPORT, self.game_state.config).shieldRange)

                # Accumulates shield amount from support structures around location that can support each location
                for support_location in all_support_locations:
                    for unit in self.game_state.game_map[support_location]:
                        if unit.shieldPerUnit > 0 and unit.player_index == 0:
                            damage -= unit.shieldPerUnit
<<<<<<< HEAD
                """
            #Adds location for the key corresponding to damage
            if damages.get(damage) is None:
                damages[damage] = [location]
            else:
                temp = damages[damage]
                temp.append(location)
                damages[damage] = temp

        # Now just return the dictionary of damages and locations
        return damages
=======
            damages.append(damage)

        # Now just return the location that takes least damage
        return min(damages)
>>>>>>> 6242b483a89b4f1d1417396faf6e34dc28d5c2fc

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
            if damage == 0:
                spawn_location.append(location)

        # Now just return the location that does not take damage
        return spawn_location

    def our_weakness_location(self, game_state):
        """
        This function will return spawn locations that will not take any damage for enemy mobile units.
        Works similar to function for friendly units
        """
        spawn_location = []
        location_options = game_state.game_map.get_edge_locations(
            game_state.game_map.TOP_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT)

        # Remove locations that are blocked by enemy structures
        # since we can't deploy units there.
        location_options = self.filter_blocked_locations(location_options, game_state)

        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            damage = 0
            for path_location in path:
                # Get number of friendly turrets that can attack each location and multiply by turret damage
                damage += len(game_state.get_attackers(path_location, 1)) * gamelib.GameUnit(TURRET,
                                                                                             game_state.config).damage_i
            if damage == 0:
                spawn_location.append(location)

        # Now just return the location that does not take damage
        return spawn_location

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered