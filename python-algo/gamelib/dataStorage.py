import null


class dataStorage:

    def __init__(self):
        self.game_state = null
        # store the dictionary to keys min_health_val to each coordinates
        self.dict_for_attack_path = null
        # store the list of structures and their coordinates that have been damaged
        self.list_record_for_our_damaged_structure = null
        # store the list of structures and their coordinates that have been destroyed
        self.list_record_for_our_destroyed_structure = null
        # store a dictionary of locations and how much dmg is done using that location for attack
        self.previous_attack_result = null
        

