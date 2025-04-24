class Dog:
    def speak(self):
        return "woof!"


class Cat:
    def speak(self):
        return "Meow!"


def animal_factory(animal_type):
    """
    Factory function to create animal objects.
    :param animal_type: str, type of animal to create
    :return: instance of Dog or Cat
    """
    if animal_type == "dog":
        return Dog()
    elif animal_type == "cat":
        return Cat()
    else:
        raise ValueError(f"Unknown animal type: {animal_type}")
