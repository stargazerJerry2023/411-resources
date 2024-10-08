from typing import Any, Optional

class Animal:
    def __init__(self, animal_id: int, species: str, age: Optional[int] = None, health_status: Optional[str] = None):
        self.animal_id = animal_id
        self.sepcies = species
        self.age = age
        self.health_status = health_status
    

    def get_animal_by_id(self, animal_id: int) -> Optional[Animal]
        return self.animals.get(animal_id)

    def get_animal_details(self, animal_id) -> dict[str, Any]:
        return {
            "animal_id": self.animal_id,
            "species": self.species,
            "age": self.age,
            "health_status": self.health_status,
        }

    def update_animal_details(self, animal_id: int, **kwargs: Any) -> None:
