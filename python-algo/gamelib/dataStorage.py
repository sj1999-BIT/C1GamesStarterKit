import gamelib
import random

class DataStorage:

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

        self.previous_game_state = None
        # store the dictionary to keys min_health_val to each coordinates
        self.dict_for_attack_path = None
        # store the list of structures and their coordinates that have been damaged
        self.list_record_for_our_damaged_structure = None
        # store the list of structures and their coordinates that have been destroyed
        self.list_record_for_our_destroyed_structure = None
        # store a dictionary of locations and how much dmg is done using that location for attack
        self.previous_attack_result = None
        # predict future possible attack location
        self.chance_of_attack = {}
        # set an adjustable value of attack units
        self.min_mobile_units_needed = 8
        # set an adjustable value of possible mini MP required by opponent to start an attack
        self.min_MP_enemy_needed = 8

    def learning_and_update_info(self, game_state, attacked_locations):
        self.update_future_attack_prediction(attacked_locations)
        self.chances_of_opponent_attack(game_state)

    def update_future_attack_prediction(self, attacked_locations):
        """
        updates the coordinates potential chance of attack
        :param attacked_location:
        """
        gamelib.debug_write("location for future attack".format(attacked_locations))
        for location in attacked_locations:
            tuple_location = tuple(location)
            if tuple_location in self.chance_of_attack.keys():
                self.chance_of_attack.update({tuple_location: self.chance_of_attack.get(tuple_location) / 2 + 0.5})
            else:
                self.chance_of_attack.update({tuple_location: 0.5})

    def chances_of_opponent_attack(self, game_state):
        target_location = []
        if game_state.get_resource(MP, 1) > self.min_MP_enemy_needed:
            highest_val = 0
            for tuple_location in self.chance_of_attack.keys():
                if highest_val < self.chance_of_attack.get(tuple_location):
                    highest_val = self.chance_of_attack.get(tuple_location)
                    target_location = list(tuple_location)
        return target_location






        

