from db.client import supabase
from datetime import datetime, timedelta, timezone


async def get_user_faction(user_id):
    try:
        response = supabase.table("users").select("faction").eq("id", user_id).execute()
        if response.data:
            return response.data[0]["faction"]
        return None
    except Exception as e:
        print(f"Error in get_user_faction: {e}")
        return None


async def ensure_user_exists(user_id):
    try:
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        if response.data and len(response.data) > 0:
            return
        supabase.table("users").insert({"id": user_id}).execute()
    except Exception as e:
        print(f"Error in ensure_user_exists: {e}")


async def create_faction(faction_name, leader_id):
    try:
        print(f"Creating faction `{faction_name}` with leader {leader_id}.")
        await ensure_user_exists(leader_id)
        print("User exists.")

        response = supabase.table("factions").insert({"name": faction_name, "leader_id": leader_id}).execute()

        print(f"Faction `{faction_name}` created with leader {leader_id}.")
    except Exception as e:
        print(f"Error in create_faction: {e}")


async def is_faction_name_taken(faction_name):
    try:
        response = supabase.table("factions").select("*").eq("name", faction_name).execute()
        if response.data:
            return True
        return False
    except Exception as e:
        print(f"Error in is_faction_name_taken: {e}")
        return False


async def add_member_to_faction(user_id, faction_name, role="member"):
    try:
        await ensure_user_exists(user_id)

        response = supabase.table("users").update({"faction": faction_name}).eq("id", user_id).execute()

        response = supabase.table("faction_members").insert({"user_id": user_id, "faction": faction_name, "role": role}).execute()

        print(f"User {user_id} added to faction `{faction_name}`.")
    except Exception as e:
        print(f"Error in add_member_to_faction: {e}")


async def remove_member_from_faction(user_id):
    try:
        await ensure_user_exists(user_id)

        response = supabase.table("users").update({"faction": None}).eq("id", user_id).execute()

        print(f"User {user_id} removed from their faction.")
    except Exception as e:
        print(f"Error in remove_member_from_faction: {e}")


async def get_faction_members(faction_name):
    try:
        response = supabase.table("users").select("id").eq("faction", faction_name).execute()

        if response.data:
            return [member["id"] for member in response.data]
        return []
    except Exception as e:
        print(f"Error in get_faction_members: {e}")
        return []


async def get_faction_leader(faction_name):
    try:
        response = supabase.table("factions").select("leader_id").eq("name", faction_name).execute()

        return response.data[0]["leader_id"]
    except Exception as e:
        print(f"Error in get_faction_leader: {e}")
        return 0


async def update_faction_resources(faction_name, resources):
    try:
        response = supabase.table("factions").update({"resources": resources}).eq("name", faction_name).execute()

        print(f"Resources of faction `{faction_name}` updated.")
    except Exception as e:
        print(f"Error in update_faction_resources: {e}")


async def has_enough_resources(faction_name, amount):
    try:
        response = supabase.table("factions").select("resources").eq("name", faction_name).execute()

        if response.data:
            return response.data[0]["resources"] >= amount
        return False
    except Exception as e:
        print(f"Error in has_enough_resources: {e}")
        return False


async def is_leader(user_id):
    try:
        response = supabase.table("factions").select("leader_id").eq("leader_id", user_id).execute()

        return bool(response.data)
    except Exception as e:
        print(f"Error in is_leader: {e}")
        return False


async def remove_faction(faction_name):
    try:
        response = supabase.table("factions").delete().eq("name", faction_name).execute()
        print(f"Faction `{faction_name}` removed.")
    except Exception as e:
        print(f"Error in remove_faction: {e}")


async def get_top_factions_by_score():
    resp = supabase.table("factions").select("name, resources, power_bonus, hourly_bonus, attack_bonus, defense_bonus").execute()
    if not resp.data:
        return []

    factions_data = resp.data
    for f in factions_data:
        resources = f.get("resources", 0)
        p_bonus = f.get("power_bonus", 0)
        h_bonus = f.get("hourly_bonus", 0.0)
        a_bonus = f.get("attack_bonus", 0)
        d_bonus = f.get("defense_bonus", 0)
        score = resources + (p_bonus * 1000) + (h_bonus * 2000) + (a_bonus * 500) + (d_bonus * 500)
        f["score"] = score

    factions_data.sort(key=lambda x: x["score"], reverse=True)
    return factions_data[:10]


async def get_faction_upgrades(faction_name):
    try:
        resp = supabase.table("factions").select("power_bonus, hourly_bonus, attack_bonus, defense_bonus").eq("name", faction_name).execute()
        if resp.data and len(resp.data) > 0:
            return resp.data[0]
        return {"power_bonus": 0, "hourly_bonus": 0.0, "attack_bonus": 0, "defense_bonus": 0}
    except Exception as e:
        print(f"Error in get_faction_upgrades: {e}")
        return {"power_bonus": 0, "hourly_bonus": 0.0, "attack_bonus": 0, "defense_bonus": 0}


async def update_faction_upgrade(faction_name, upgrade_type, amount):
    try:
        ups = await get_faction_upgrades(faction_name)
        new_val = ups[upgrade_type] + amount
        supabase.table("factions").update({upgrade_type: new_val}).eq("name", faction_name).execute()
    except Exception as e:
        print(f"Error in update_faction_upgrade: {e}")


async def get_faction_resources(faction_name):
    try:
        resp = supabase.table("factions").select("resources").eq("name", faction_name).execute()
        if resp.data:
            return resp.data[0]["resources"]
        return 0
    except Exception as e:
        print(f"Error in get_faction_resources: {e}")
        return 0


async def faction_has_enough_resources(faction_name, amount):
    resources = await get_faction_resources(faction_name)
    return resources >= amount


async def spend_faction_resources(faction_name, amount):
    try:
        current = await get_faction_resources(faction_name)
        if current < amount:
            return False
        new_amount = current - amount
        supabase.table("factions").update({"resources": new_amount}).eq("name", faction_name).execute()
        return True
    except Exception as e:
        print(f"Error in spend_faction_resources: {e}")
        return False


async def faction_income(user_id):
    try:
        faction_name = await get_user_faction(user_id)
        if not faction_name:
            return "You are not in a faction."

        resp = supabase.table("factions").select("resources, last_income_trigger").eq("name", faction_name).execute()
        if not resp.data:
            return "Faction not found?"
        f_data = resp.data[0]
        last_trigger = f_data.get("last_income_trigger")
        now = datetime.now(timezone.utc)
        if last_trigger:
            lt = datetime.fromisoformat(last_trigger)
            if (now - lt) < timedelta(days=1):
                remaining = timedelta(days=1) - (now - lt)
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                return f"Wait {hours}h {minutes}m before using this again."

        resources = f_data["resources"]
        new_resources = int(resources * 1.05)
        supabase.table("factions").update({"resources": new_resources, "last_income_trigger": now.isoformat()}).eq("name", faction_name).execute()
        return f"Your faction's resources increased from {resources} to {new_resources}!"
    except Exception as e:
        print(f"Error in faction_income: {e}")
        return "An error occured"
