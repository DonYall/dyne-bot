import random
from datetime import datetime, timezone
from db.client import supabase
from data.classes import classes
from db.user_db import (
    ensure_user_exists,
    get_user_class,
    get_user_health,
    update_user_health,
    get_user_balance,
    update_user_gold,
    get_user_power,
    get_user_max_health,
    reset_user_stats,
)
from data.bosses import bosses


def calculate_party_damage(users_info, boss):
    """
    users_info: list of dict with keys: class_name, power, attack, defense, health, synergy_classes
    synergy bonus: if user has at least one synergy class present in party, +10% damage
    Damage formula: Similar to duels: (base_attack + power + rand(1-10)) * synergy_mod - boss_defense
    Sum damage from all participants.
    """
    total_damage = 0
    individuals = []
    party_classes = [u["class_name"] for u in users_info]

    for u in users_info:
        synergy_bonus = 1.0
        for s_class in classes[u["class_name"]]["synergies"]:
            if s_class in party_classes and s_class != u["class_name"]:
                synergy_bonus = 1.1
                break

        base_attack = classes[u["class_name"]].get("attack", 10)
        user_attack = base_attack + u["power"]
        roll = 1 + (random.randint(1, 10))
        effective_attack = (user_attack + roll) * synergy_bonus
        damage_dealt = max(0, effective_attack - boss["defense"])
        total_damage += damage_dealt
        individuals.append({"user_id": u["user_id"], "damage": damage_dealt})
    return total_damage, individuals


def boss_attack(users_info, boss):
    """
    Boss attacks back. Each user takes some damage.
    Boss damage distribution: boss_attack * random factor - user defense
    """
    results = []
    for u in users_info:
        user_defense = classes[u["class_name"]].get("defense", 5)
        roll = 1 + (random.randint(1, 5))
        boss_eff_attack = boss["attack"] + roll
        dmg_to_user = max(0, boss_eff_attack - user_defense)
        results.append({"user_id": u["user_id"], "damage": dmg_to_user})
    return results


async def check_cooldown(user_id, boss_name):
    response = supabase.table("boss_cooldowns").select("last_attempt").eq("user_id", user_id).eq("boss", boss_name).execute()
    cooldown = bosses[boss_name]["cooldown"]
    if response.data and len(response.data) > 0:
        last_attempt = datetime.fromisoformat(response.data[0]["last_attempt"])
        now = datetime.now(timezone.utc)
        if (now - last_attempt).total_seconds() < cooldown:
            remaining = cooldown - (now - last_attempt).total_seconds()
            return False, remaining
    return True, 0


async def update_cooldown(user_id, boss_name):
    now = datetime.now(timezone.utc).isoformat()
    response = supabase.table("boss_cooldowns").select("*").eq("user_id", user_id).eq("boss", boss_name).execute()
    if response.data and len(response.data) > 0:
        supabase.table("boss_cooldowns").update({"last_attempt": now}).eq("user_id", user_id).eq("boss", boss_name).execute()
    else:
        supabase.table("boss_cooldowns").insert({"user_id": user_id, "boss": boss_name, "last_attempt": now}).execute()


async def create_raid(leader_id, faction, boss_name):
    await ensure_user_exists(leader_id)
    can_fight, remaining = await check_cooldown(leader_id, boss_name)
    if not can_fight:
        return f"You must wait {int(remaining)}s before challenging {boss_name} again."

    supabase.table("raids").insert({"leader_id": leader_id, "faction": faction, "boss": boss_name, "active": True}).execute()
    response = (
        supabase.table("raids")
        .select("*")
        .eq("leader_id", leader_id)
        .eq("active", True)
        .eq("boss", boss_name)
        .order("id", desc=True)
        .limit(1)
        .execute()
    )
    raid_id = response.data[0]["id"]
    supabase.table("raid_participants").insert({"raid_id": raid_id, "user_id": leader_id, "ready": False, "damage_dealt": 0}).execute()
    return f"Raid against {boss_name} started! Use /invite_raid to invite faction members, they must /join_raid, and then /ready_raid. Once all ready, /begin_raid."


async def invite_to_raid(leader_id, target_id):
    raid_response = supabase.table("raids").select("*").eq("leader_id", leader_id).eq("active", True).execute()
    if not raid_response.data:
        return "You are not leading an active raid."
    raid_id = raid_response.data[0]["id"]
    faction = raid_response.data[0]["faction"]

    user_faction_response = supabase.table("users").select("faction").eq("id", target_id).execute()
    if not user_faction_response.data or user_faction_response.data[0]["faction"] != faction:
        return "You can only invite members of your own faction."

    supabase.table("raid_invitations").insert({"raid_id": raid_id, "user_id": target_id}).execute()

    return f"Invited <@{target_id}> to the raid."


async def add_raid_participant(user_id):
    invite_response = supabase.table("raid_invitations").select("*").eq("user_id", user_id).execute()
    if not invite_response.data:
        return "You have no invitations."
    raid_id = invite_response.data[0]["raid_id"]
    part_response = supabase.table("raid_participants").select("*").eq("raid_id", raid_id).eq("user_id", user_id).execute()
    if part_response.data:
        return "You are already in the raid."
    supabase.table("raid_participants").insert({"raid_id": raid_id, "user_id": user_id, "ready": False, "damage_dealt": 0}).execute()
    return "You joined the raid. Use /ready_raid when you are prepared."


async def ready_participant(user_id):
    part_response = supabase.table("raid_participants").select("*").eq("user_id", user_id).execute()
    if not part_response.data:
        return "You are not in any raid."
    raid_id = part_response.data[0]["raid_id"]

    supabase.table("raid_participants").update({"ready": True}).eq("user_id", user_id).execute()

    all_ready_response = supabase.table("raid_participants").select("ready").eq("raid_id", raid_id).execute()
    if all(r["ready"] for r in all_ready_response.data):
        return "You are ready. All participants are ready! Leader can now /begin_raid."
    return "You are ready. Waiting for others..."


async def is_raid_leader(user_id):
    raid_response = supabase.table("raids").select("*").eq("leader_id", user_id).eq("active", True).execute()
    return bool(raid_response.data)


async def get_raid_info(user_id):
    participants_response = supabase.table("raid_participants").select("*").eq("user_id", user_id).execute()
    if not participants_response.data:
        return "You are not in a raid."
    raid_id = participants_response.data[0]["raid_id"]
    raid_response = supabase.table("raids").select("*").eq("id", raid_id).execute()
    raid = raid_response.data[0]
    participants_response = supabase.table("raid_participants").select("user_id, ready").eq("raid_id", raid_id).execute()
    participants_list = [f"<@{p['user_id']}> - {'Ready' if p['ready'] else 'Not Ready'}" for p in participants_response.data]
    return f"Raid against {raid['boss']} (Leader: <@{raid['leader_id']}>)\nParticipants:\n" + "\n".join(participants_list)


async def cancel_raid(user_id):
    raid_response = supabase.table("raids").select("*").eq("leader_id", user_id).eq("active", True).execute()
    if not raid_response.data:
        return "No active raid found or you are not the leader."
    raid_id = raid_response.data[0]["id"]
    supabase.table("raids").update({"active": False}).eq("id", raid_id).execute()
    return "Raid canceled."


async def increase_raid_wins(user_id):
    try:
        response = supabase.table("users").select("raid_wins").eq("id", user_id).execute()
        if not response.data:
            return f"User with ID {user_id} does not exist."

        update_response = supabase.table("users").update({"raid_wins": response.data[0]["raid_wins"] + 1}).eq("id", user_id).execute()
        return f"Raid wins incremented for user {user_id}."
    except Exception as e:
        print(f"Error in increase_raid_wins: {e}")
        return "An error occurred while updating raid wins."


async def start_raid_battle(leader_id):
    try:
        raid_response = supabase.table("raids").select("*").eq("leader_id", leader_id).eq("active", True).execute()
        if not raid_response.data:
            return "No active raid found or you are not the leader."
        raid = raid_response.data[0]
        raid_id = raid["id"]

        participants_response = supabase.table("raid_participants").select("*").eq("raid_id", raid_id).execute()
        participants = participants_response.data
        if not participants:
            return "No participants in the raid!"
        if not all(p["ready"] for p in participants):
            return "Not all participants are ready."

        boss = bosses[raid["boss"]]
        boss_name = boss["name"]

        for p in participants:
            can_fight, remaining = await check_cooldown(p["user_id"], raid["boss"])
            if not can_fight:
                return f"<@{p['user_id']}> must wait {int(remaining)}s before fighting this boss again."

        users_info = []
        for p in participants:
            user_id = p["user_id"]
            class_name = await get_user_class(user_id)
            power = await get_user_power(user_id)
            user_health = await get_user_health(user_id)
            user_max_health = await get_user_max_health(user_id)
            users_info.append({"user_id": user_id, "class_name": class_name, "power": power, "health": user_health, "max_health": user_max_health})

        total_damage, individuals = calculate_party_damage(users_info, boss)
        boss_health = boss["health"] - total_damage

        response = f"### RAID RESULTS: {raid['boss']}\n"
        response += f"The raid party assembled under the leadership of <@{leader_id}> faced the fearsome **{boss_name}**.\n\n"

        if boss_health > 0:
            boss_results = boss_attack(users_info, boss)
            response += f"The party dealt a total of **{total_damage} damage**, leaving the {boss_name} with **{boss_health} HP**.\n"
            response += "However, the boss fought back fiercely:\n\n"

            for r in boss_results:
                user_id = r["user_id"]
                damage_taken = r["damage"]
                cur_health = await get_user_health(user_id)
                new_health = max(0, cur_health - damage_taken)
                await update_user_health(user_id, new_health)

                response += (
                    f"- <@{user_id}> ({r['class_name']}) took **{damage_taken} damage**. " + "They were defeated and will need to recover."
                    if new_health <= 0
                    else f"Remaining health: **{new_health}**."
                )

                if new_health <= 0:
                    await reset_user_stats(user_id)

            response += f"\nThe raid ends with the party retreating to regroup and plan their next assault.\n"
        else:
            reward = boss["reward_gold"]
            sum_damage = sum(i["damage"] for i in individuals)
            response += (
                f"The party unleashed a devastating assault, dealing a total of **{total_damage} damage** and defeating the **{boss_name}**!\n\n"
            )
            response += f"### Loot Distribution:\n"

            for i in individuals:
                user_id = i["user_id"]
                await increase_raid_wins(user_id)
                portion = 0
                if sum_damage > 0:
                    portion = int((i["damage"] / sum_damage) * reward)
                cur_gold = await get_user_balance(user_id)
                await update_user_gold(user_id, cur_gold + portion)
                response += f"- <@{user_id}> ({i['class_name']}) dealt **{int(i['damage'])} damage** " f"and earned **{portion} gold**.\n"

            supabase.table("raids").update({"active": False}).eq("id", raid_id).execute()
            response += f"\nWith the boss defeated, the raid party celebrates their victory and claims their hard-earned rewards."

        for i in individuals:
            supabase.table("raid_participants").update({"damage_dealt": i["damage"]}).eq("raid_id", raid_id).eq("user_id", i["user_id"]).execute()

        for p in participants:
            await update_cooldown(p["user_id"], raid["boss"])

        return response

    except Exception as e:
        print(f"Error in start_raid_battle: {e}")
        return "An error occurred during the raid battle."
