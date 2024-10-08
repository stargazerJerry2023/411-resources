from typing import Optional

from wildlife_tracker.animal_managment.animal import Animal

class AnimalManager:

    def __init__(self) -> None:
        animals: dict[int, Animal] = {}

    def get_animal_by_id(self, animal_id: int) -> Optional[Animal]:
        return self.animals.get(animal_id)

    def register_animal(self, Animal) -> None:
        self.animals[Animal.animal_id] = Animal

    def remove_animal(self, animal_id: int) -> None:
        del self.animals[animal_id]
