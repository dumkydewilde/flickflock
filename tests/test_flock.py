import pytest
from flickflock.flock import Flock

people_object = [
    {
        "name": "Alice", 
        "id": "A",
        "works" : [
            {
                "title": "A movie",
                "id": 1
            },
            {
                "title": "B film",
                "id": 2
            }
        ]     
    },
    {
        "name": "Bob", 
        "id": "B",
        "works" : [
            {
                "title": "A movie",
                "id": 1
            },
            {
                "title": "C-level films",
                "id": 3
            }
        ]     
    }
]

works_object = [
    {
        "name" : "A movie",
        "id": 1

    },
    {
        "name" : "B film",
        "id" : 2
    }    
]

def test_flock():
    flock = Flock()
    assert flock

def test_set_flock_name():
    flock = Flock()
    flock.set_flock_name("test_flock")
    assert flock.flock_name == "test_flock"