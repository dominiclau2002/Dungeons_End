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

# # Example Usage
# if __name__ == "__main__":
#     d6 = Dice(6)  # Standard 6-sided dice (D6)
#     print(f"Rolling 1d6: {d6.roll()}")  # Rolls one 6-sided dice
#     print(f"Rolling 3d6: {d6.roll(3)}")  # Rolls three 6-sided dice

# roll 1d6
# GET http://127.0.0.1:5007/roll?sides=6

# roll 3d20
# GET http://127.0.0.1:5007/roll?sides=20&count=3