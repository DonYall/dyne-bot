from datetime import datetime, timezone, timedelta
from dateutil.parser import parse
from db.client import supabase
from data.classes import classes
from db.faction_db import get_faction_upgrades, ensure_user_exists
import random


async def has_enough_gold(user_id, amount):
    try:
        response = supabase.table("users").select("gold").eq("id", user_id).execute()

        if response.data:
            return response.data[0]["gold"] >= amount
        return False
    except Exception as e:
        print(f"Error in has_enough_gold: {e}")
        return False


async def get_user_faction(user_id):
    try:
        response = supabase.table("users").select("faction").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["faction"]
        return None
    except Exception as e:
        print(f"Error in get_user_faction: {e}")
        return None


async def get_user_class(user_id):
    try:
        response = supabase.table("users").select("class").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["class"]
        return None
    except Exception as e:
        print(f"Error in get_user_class: {e}")
        return None


async def set_user_class(user_id, user_class):
    try:
        response = supabase.table("users").update({"class": user_class}).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error in set_user_class: {e}")


async def get_user_health(user_id):
    try:
        response = supabase.table("users").select("health").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["health"]
        return 100
    except Exception as e:
        print(f"Error in get_user_health: {e}")
        return 100


async def get_user_raid_wins(user_id):
    try:
        response = supabase.table("users").select("raid_wins").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["raid_wins"]
        return 0
    except Exception as e:
        print(f"Error in get_user_raid_wins: {e}")
        return 0


async def update_user_health(user_id, health):
    try:
        response = supabase.table("users").update({"health": health}).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error in update_user_health: {e}")


async def reset_user_stats(user_id):
    """
    Resets the user's stats when they hit 0 health.
    Health: back to 100
    Gold: 0
    Faction remains the same.
    Power remains the same.
    """
    try:
        await ensure_user_exists(user_id)
        supabase.table("users").update({"health": 100, "gold": 0}).eq("id", user_id).execute()
        print(f"User {user_id} stats reset due to 0 health.")
    except Exception as e:
        print(f"Error in reset_user_stats: {e}")


async def get_user_power(user_id):
    try:
        response = supabase.table("users").select("power").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["power"]
        return 0
    except Exception as e:
        print(f"Error in get_user_power: {e}")
        return 0


async def get_user_max_health(user_id):
    try:
        response = supabase.table("users").select("max_health").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["max_health"]
        return 100
    except Exception as e:
        print(f"Error in get_user_max_health: {e}")
        return 100


async def update_user_max_health(user_id, new_max_health):
    try:
        supabase.table("users").update({"max_health": new_max_health}).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error in update_user_max_health: {e}")


async def update_user_power(user_id, new_power):
    try:
        supabase.table("users").update({"power": new_power}).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error in update_user_power: {e}")


async def claim_hourly(user_id):
    try:
        await ensure_user_exists(user_id)
        response = supabase.table("users").select("last_hourly_claim, gold, hourly_multiplier").eq("id", user_id).execute()
        user_data = response.data[0]

        last_claim_time = parse(user_data["last_hourly_claim"])
        current_time = datetime.now(timezone.utc)
        if last_claim_time and (current_time - last_claim_time) < timedelta(hours=1):
            remaining_time = timedelta(hours=1) - (current_time - last_claim_time)
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"Please wait {hours}h {minutes}m {seconds}s before claiming again."

        base_reward = random.randint(50, 150)
        reward = int(base_reward * user_data["hourly_multiplier"])

        supabase.table("users").update(
            {
                "gold": user_data["gold"] + reward,
                "last_hourly_claim": current_time.isoformat(),
            }
        ).eq("id", user_id).execute()

        return f"You've claimed your hourly reward of {reward} gold!"
    except Exception as e:
        print(f"Error in claim_hourly: {e}")
        return "An error occurred while claiming your hourly reward."


async def heal_user(user_id):
    resp = supabase.table("users").select("last_heal, health, max_health").eq("id", user_id).execute()
    if not resp.data:
        return "User not found."
    user_data = resp.data[0]

    last_heal = user_data["last_heal"]
    now = datetime.now(timezone.utc)
    cooldown = timedelta(minutes=30)
    if last_heal:
        if (now - datetime.fromisoformat(last_heal)) < cooldown:
            remaining = cooldown - (now - datetime.fromisoformat(last_heal))
            m, s = divmod(remaining.seconds, 60)
            return f"Please wait {m}m {s}s before healing again."

    current_health = user_data["health"]
    max_health = user_data["max_health"]
    heal_amount = int(max_health * 0.10)
    new_health = min(max_health, current_health + heal_amount)
    supabase.table("users").update({"health": new_health, "last_heal": now.isoformat()}).eq("id", user_id).execute()
    return f"You have healed {new_health - current_health} health! Current health: {new_health}/{max_health}"


async def get_user_balance(user_id):
    try:
        response = supabase.table("users").select("gold").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["gold"]
        return 0
    except Exception as e:
        print(f"Error in get_user_balance: {e}")
        return 0


async def update_user_gold(user_id, gold):
    try:
        supabase.table("users").update({"gold": gold}).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error in update_user_gold: {e}")


async def get_user_power(user_id):
    try:
        response = supabase.table("users").select("power").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["power"]
        return 0
    except Exception as e:
        print(f"Error in get_user_power: {e}")
        return 0


async def get_user_final_power(user_id):
    user_power = await get_user_power(user_id)
    faction_name = await get_user_faction(user_id)
    faction_bonus = 0
    if faction_name:
        ups = await get_faction_upgrades(faction_name)
        faction_bonus = ups["power_bonus"]
    return user_power + faction_bonus


async def get_user_final_attack(user_id):
    final_power = await get_user_final_power(user_id)
    user_base_attack = classes[await get_user_class(user_id)]["attack"]
    faction_name = await get_user_faction(user_id)
    f_attack_bonus = 0
    if faction_name:
        ups = await get_faction_upgrades(faction_name)
        f_attack_bonus = ups["attack_bonus"]
    return user_base_attack + final_power + f_attack_bonus


async def get_user_final_defense(user_id):
    base_def = 5
    faction_name = await get_user_faction(user_id)
    f_def_bonus = 0
    if faction_name:
        ups = await get_faction_upgrades(faction_name)
        f_def_bonus = ups["defense_bonus"]
    return base_def + f_def_bonus


async def get_user_max_health(user_id):
    try:
        response = supabase.table("users").select("max_health").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["max_health"]
        return 100
    except Exception as e:
        print(f"Error in get_user_max_health: {e}")
        return 100


async def update_user_max_health(user_id, new_max):
    try:
        supabase.table("users").update({"max_health": new_max}).eq("id", user_id).execute()
    except Exception as e:
        print(f"Error in update_user_max_health: {e}")


async def get_user_hourly_multiplier(user_id):
    try:
        resp = supabase.table("users").select("hourly_multiplier").eq("id", user_id).execute()
        user_multi = resp.data[0]["hourly_multiplier"] if resp.data else 1.0
        faction_name = await get_user_faction(user_id)
        f_multi = 0.0
        if faction_name:
            ups = await get_faction_upgrades(faction_name)
            f_multi = ups["hourly_bonus"]
        return user_multi * (1 + f_multi)
    except Exception as e:
        print(f"Error in get_user_hourly_multiplier: {e}")
        return 1.0


async def duel(user_id, opponent_id):
    """
    Simulates a battle between two users with the updated system.
    Returns a tuple: (response_string, winner_id, loser_id)
    If there's no clear winner, winner_id and loser_id will be None.
    """
    try:
        await ensure_user_exists(user_id)
        await ensure_user_exists(opponent_id)

        user_cls_name = await get_user_class(user_id)
        opponent_cls_name = await get_user_class(opponent_id)

        user_class = classes.get(user_cls_name)
        opponent_class = classes.get(opponent_cls_name)

        user_health = await get_user_health(user_id)
        opponent_health = await get_user_health(opponent_id)

        if not user_class or not opponent_class:
            return (
                "One or both users do not have a class. Set a class using /select_class.",
                None,
                None,
            )

        if user_health <= 0:
            return (
                f"<@{user_id}> is too weak to fight! Heal up before dueling again.",
                None,
                None,
            )
        if opponent_health <= 0:
            return (
                f"<@{opponent_id}> is too weak to fight! They're out of commission.",
                None,
                None,
            )

        user_final_attack = await get_user_final_attack(user_id)
        user_final_defense = await get_user_final_defense(user_id)
        opponent_final_attack = await get_user_final_attack(opponent_id)
        opponent_final_defense = await get_user_final_defense(opponent_id)

        user_vulnerabilities = user_class.get("vulnerabilities", [])
        user_resistances = user_class.get("resistances", [])
        opponent_vulnerabilities = opponent_class.get("vulnerabilities", [])
        opponent_resistances = opponent_class.get("resistances", [])

        user_attack_mod = 1.0
        opponent_attack_mod = 1.0

        if user_cls_name in opponent_resistances:
            user_attack_mod *= 0.5
        if opponent_cls_name in user_resistances:
            opponent_attack_mod *= 0.5
        if user_cls_name in opponent_vulnerabilities:
            opponent_attack_mod *= 1.5
        if opponent_cls_name in user_vulnerabilities:
            user_attack_mod *= 1.5

        user_attack_roll = random.randint(1, 10)
        opponent_attack_roll = random.randint(1, 10)

        user_effective_attack = (user_final_attack + user_attack_roll) * user_attack_mod
        opponent_effective_attack = (opponent_final_attack + opponent_attack_roll) * opponent_attack_mod

        user_defense_roll = random.randint(1, 5)
        opponent_defense_roll = random.randint(1, 5)

        user_effective_defense = user_final_defense + user_defense_roll
        opponent_effective_defense = opponent_final_defense + opponent_defense_roll

        user_damage = max(0, user_effective_attack - opponent_effective_defense)
        opponent_damage = max(0, opponent_effective_attack - user_effective_defense)

        new_user_health = max(0, user_health - opponent_damage)
        new_opponent_health = max(0, opponent_health - user_damage)

        await update_user_health(user_id, new_user_health)
        await update_user_health(opponent_id, new_opponent_health)

        response = f"## <@{user_id}> vs <@{opponent_id}>\n"
        response += f"<@{user_id}> attacks with {user_effective_attack:.1f} power vs {opponent_effective_defense:.1f} defense, dealing {user_damage:.1f} damage.\n"
        response += f"<@{opponent_id}> attacks with {opponent_effective_attack:.1f} power vs {user_effective_defense:.1f} defense, dealing {opponent_damage:.1f} damage.\n"
        response += f"\n<@{user_id}> now has {new_user_health:.1f} HP."
        response += f"\n<@{opponent_id}> now has {new_opponent_health:.1f} HP."

        winner_id = None
        loser_id = None

        if new_user_health <= 0 and new_opponent_health > 0:
            winner_id = opponent_id
            loser_id = user_id
            response += f"\n**<@{user_id}> has been defeated!**"
        elif new_opponent_health <= 0 and new_user_health > 0:
            winner_id = user_id
            loser_id = opponent_id
            response += f"\n**<@{opponent_id}> has been defeated!**"
        elif new_user_health <= 0 and new_opponent_health <= 0:
            response += "\n**Both fighters have fallen!** It's a draw."
        else:
            if user_damage > opponent_damage:
                winner_id = user_id
                loser_id = opponent_id
                response += "\n**By dealing more damage, <@" + user_id + "> wins this round!**"
            elif opponent_damage > user_damage:
                winner_id = opponent_id
                loser_id = user_id
                response += "\n**By dealing more damage, <@" + opponent_id + "> wins this round!**"
            else:
                response += "\n**No one has a clear advantage! It's a draw.**"

        if new_user_health <= 0:
            await reset_user_stats(user_id)
        if new_opponent_health <= 0:
            await reset_user_stats(opponent_id)

        return (response, winner_id, loser_id)

    except Exception as e:
        print(f"Error in duel: {e}")
        return ("An error occurred during the duel.", None, None)


# async def claim_hourly(user_id):
#     """
#     Allows a user to claim their hourly reward if eligible.
#     """
#     try:
#         await ensure_user_exists(user_id)

#         response = supabase.table("users").select("last_hourly_claim, gold").eq("id", user_id).execute()
#         user_data = response.data[0]

#         last_claim_time = user_data["last_hourly_claim"]
#         current_time = datetime.now(timezone.utc)

#         if last_claim_time and (current_time - datetime.fromisoformat(last_claim_time)) < timedelta(hours=1):
#             remaining_time = timedelta(hours=1) - (current_time - datetime.fromisoformat(last_claim_time))
#             hours, remainder = divmod(remaining_time.seconds, 3600)
#             minutes, seconds = divmod(remainder, 60)
#             return f"Please wait {hours}h {minutes}m {seconds}s before claiming again."

#         reward = random.randint(50, 150)

#         supabase.table("users").update(
#             {
#                 "gold": user_data["gold"] + reward,
#                 "last_hourly_claim": current_time.isoformat(),
#             }
#         ).eq("id", user_id).execute()

#         return f"You've claimed your hourly reward of {reward} gold!"
#     except Exception as e:
#         print(f"Error in claim_hourly: {e}")
#         return "An error occurred while claiming your hourly reward."


async def coinflip(challenger_id, opponent_id, amount):
    """
    Executes a coinflip between two users.
    """
    try:
        await ensure_user_exists(challenger_id)
        await ensure_user_exists(opponent_id)

        challenger_response = supabase.table("users").select("gold").eq("id", challenger_id).execute()
        opponent_response = supabase.table("users").select("gold").eq("id", opponent_id).execute()

        challenger_gold = challenger_response.data[0]["gold"]
        opponent_gold = opponent_response.data[0]["gold"]

        if challenger_gold < amount:
            return f"You don't have enough gold to bet {amount}."
        if opponent_gold < amount:
            return f"Opponent doesn't have enough gold to bet {amount}."

        supabase.table("users").update({"gold": challenger_gold - amount}).eq("id", challenger_id).execute()
        supabase.table("users").update({"gold": opponent_gold - amount}).eq("id", opponent_id).execute()

        winner_id = challenger_id if random.choice([True, False]) else opponent_id

        supabase.table("users").update(
            {"gold": supabase.table("users").select("gold").eq("id", winner_id).execute().data[0]["gold"] + (amount * 2)}
        ).eq("id", winner_id).execute()

        return f"Coinflip result: {'You win!' if winner_id == challenger_id else 'You lose!'} {amount} gold goes to the winner."
    except Exception as e:
        print(f"Error in coinflip: {e}")
        return "An error occurred during the coinflip."


async def deposit_gold_to_faction(user_id, amount):
    """
    Deposits gold from a user to their faction.
    """

    try:
        await ensure_user_exists(user_id)
        faction_name = await get_user_faction(user_id)

        if not faction_name:
            return False

        response = supabase.table("users").select("gold").eq("id", user_id).execute()
        user_gold = response.data[0]["gold"]

        response = supabase.table("factions").select("resources").eq("name", faction_name).execute()
        faction_resources = response.data[0]["resources"]

        if user_gold < amount:
            return False

        user_gold -= amount
        faction_resources += amount

        response = supabase.table("users").update({"gold": user_gold}).eq("id", user_id).execute()
        response = supabase.table("factions").update({"resources": faction_resources}).eq("name", faction_name).execute()

        return "Gold deposited successfully."
    except Exception as e:
        print(f"Error in deposit_gold_to_faction: {e}")
        return "An error occurred while depositing gold."
