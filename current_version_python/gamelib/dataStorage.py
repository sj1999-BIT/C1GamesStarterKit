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

        self.dict_for_attack_path = None

        # record attributes from previous game_state
        self.cur_game_state = None
        self.observer = None
        self.previous_opponent_MP = -10
        self.previous_opponent_SP = -10
        self.previous_self_MP = -10
        self.previous_self_SP = -10
        self.my_health = 30
        self.enemy_health = 30

        # store the list of structures and their coordinates that have been damaged
        self.list_record_for_our_damaged_structure = None

        # store the list of structures and their coordinates that have been destroyed
        self.list_record_for_our_destroyed_structure = None

        # store a dictionary of locations and how much dmg is done using that location for attack
        self.previous_attack_location = []

        # predict future possible attack location
        self.chance_of_attack = {}

        # set an adjustable value of attack units
        self.min_mobile_units_needed = 8

        # set an adjustable value of possible mini MP required by opponent to start an attack
        self.min_MP_enemy_needed = 8

        # set a maximum value of MP to prevent our guys from no attacking for too long
        self.max_MP_enemy_needed = 15

        # set a portion of resources that could be used for only demolishing purpose
        self.percent_MP_for_demolition = 0.6

        # set a list of blackListed location to not attacked again
        self.blacklisted_location = []



    def learning_and_update_info(self, game_state, attacked_locations, observer):
        """
        Update the values in the storage unit
        :param game_state:
        :param attacked_locations: places attacked by the opponent
        :param observer:
        :return:
        """
        if self.cur_game_state is not None:
            self.previous_opponent_MP = self.cur_game_state.get_resource(MP, 1)
            self.previous_opponent_SP = self.cur_game_state.get_resource(SP, 1)
            self.previous_self_MP = self.cur_game_state.get_resource(MP, 0)
            self.previous_self_SP = self.cur_game_state.get_resource(SP, 0)
            self.my_health = self.cur_game_state.my_health
            self.enemy_health = self.cur_game_state.enemy_health

        self.cur_game_state = game_state
        self.update_future_interception_prediction(attacked_locations)
        self.chances_of_opponent_attack(game_state)
        self.observer = observer

        self.min_mobile_units_needed *= 0.9

        # for now we don't have observer's function, we guess if its been attacked
        if len(observer.damaged_turrets) > 0:
            self.min_mobile_units_needed = (self.previous_opponent_MP + self.min_MP_enemy_needed) / 2

        # remove a random blacklisted location to prevent total unable to offense
        if (len(self.blacklisted_location)) > 0:
            deploy_index = random.randint(0, len(self.blacklisted_location) - 1)
            self.blacklisted_location.remove(self.blacklisted_location[deploy_index])



    def update_future_interception_prediction(self, attacked_locations):
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


    def is_attack_effective(self):
        MP_used_for_attack = self.previous_self_MP - self.cur_game_state.get_resource(MP, 0)
        gamelib.debug_write("the list is {}".format(self.previous_attack_location))
        if self.enemy_health == self.cur_game_state.enemy_health:
            self.blacklisted_location.extend(self.previous_attack_location)
            self.min_mobile_units_needed += 1
        else:
            self.min_mobile_units_needed = (MP_used_for_attack + self.min_mobile_units_needed) / 2











        

