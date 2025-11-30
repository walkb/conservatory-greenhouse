import typing
from typing import Dict, List, Any
from datetime import date
import strawberry
import requests


def get_plants():
    url = "http://127.0.0.1:8000"
    response = requests.get(url + "/plants")
    plants = []
    if response.status_code == 200:
        data: List[Dict[str, Any]] = response.json()
        for plant in data:
            photos: List[Photo] = []
            for photo in plant["photos"]:
                photos.append(
                    Photo(
                        id=photo["id"],
                        plant_id=photo["plant_id"],
                        date=photo["date"],
                        path=photo["path"],
                    )
                )
            plants.append(Plant(id=plant["id"], name=plant["name"], photos=photos))
    return plants


@strawberry.type
class Photo:
    plant_id: int
    id: int
    path: str
    date: str


@strawberry.type
class Plant:
    id: int
    name: str
    photos: List[Photo]


@strawberry.type
class Query:
    plants: typing.List[Plant] = strawberry.field(resolver=get_plants)


schema = strawberry.Schema(query=Query)
