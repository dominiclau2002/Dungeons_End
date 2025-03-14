import random

class Dice:
    """
    A class that simulates rolling one or multiple dice.
    """

    def __init__(self, sides=6):
        """
        Initializes a dice with a given number of sides.
        
        :param sides: (int) The number of sides on the dice. Default is 6 (D6).
        """
        self.sides = sides

    def roll(self, count=1):
        """
        Rolls multiple dice and returns the results.
        
        :param count: (int) The number of dice to roll.
        :return: (list) A list of roll results.
        """
        return [random.randint(1, self.sides) for _ in range(count)]
