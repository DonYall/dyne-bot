from db.faction_db import faction_has_enough_resources, spend_faction_resources, update_faction_upgrade, is_leader
from db.user_db import get_user_faction


async def purchase_faction_upgrade(user_id, upgrade: str):
    faction_name = await get_user_faction(user_id)
    if not faction_name:
        return "You are not in a faction."
    if not await is_leader(user_id):
        return "Only the faction leader can purchase upgrades."

    ups = {
        "power": ("power_bonus", 1000, 1),
        "hourly": ("hourly_bonus", 2000, 0.05),
        "attack": ("attack_bonus", 1500, 1),
        "defense": ("defense_bonus", 1500, 1),
    }

    if upgrade.lower() not in ups:
        return "Invalid upgrade. Available: power, hourly, attack, defense."

    col, cost, increment = ups[upgrade.lower()]

    # Check and spend faction resources
    if not await faction_has_enough_resources(faction_name, cost):
        return "Your faction doesn't have enough resources."
    success = await spend_faction_resources(faction_name, cost)
    if not success:
        return "Failed to purchase upgrade due to resource error."

    await update_faction_upgrade(faction_name, col, increment)
    return f"Successfully purchased {upgrade} upgrade for your faction!"
