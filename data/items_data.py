items = {
    1: {"name": "Iron Ore", "rarity": "common", "description": "A chunk of iron ore.", "obtain_methods": ["hourly", "raid"]},
    2: {"name": "Wood Plank", "rarity": "common", "description": "A sturdy plank of wood.", "obtain_methods": ["hourly"]},
    3: {"name": "Iron Ingot", "rarity": "uncommon", "description": "Refined iron, ready for crafting.", "obtain_methods": []},
    4: {"name": "Sword Hilt", "rarity": "uncommon", "description": "A hilt for forging a sword.", "obtain_methods": ["raid"]},
    5: {"name": "Iron Sword", "rarity": "rare", "description": "A finely crafted iron sword.", "obtain_methods": []},
}

crafting_recipes = [
    {"id": 1, "output_item_id": 3, "inputs": [{"item_id": 1, "quantity": 2}]},
    {"id": 2, "output_item_id": 5, "inputs": [{"item_id": 3, "quantity": 1}, {"item_id": 4, "quantity": 1}]},
]
