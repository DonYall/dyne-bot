import random
from datetime import datetime, timedelta, timezone
from db.client import supabase


async def ensure_user_exists(user_id):
    """
    Ensures a user exists in the `users` table. If not, creates a new entry.
    """
    try:
        # print(f"Ensuring user {user_id} exists.")
        response = supabase.table("users").select("*").eq("id", user_id).execute()
        if response.data and len(response.data) > 0:
            return

        insert_data = {"id": user_id}
        response = supabase.table("users").insert(insert_data).execute()

        print(f"User {user_id} created.")
    except Exception as e:
        print(f"Error in ensure_user_exists: {e}")


async def create_faction(faction_name, leader_id):
    """
    Creates a new faction with the given name and sets the user as the leader.
    """
    try:
        print(f"Creating faction `{faction_name}` with leader {leader_id}.")
        await ensure_user_exists(leader_id)
        print("User exists.")

        response = (
            supabase.table("factions")
            .insert({"name": faction_name, "leader_id": leader_id})
            .execute()
        )

        print(f"Faction `{faction_name}` created with leader {leader_id}.")
    except Exception as e:
        print(f"Error in create_faction: {e}")


async def is_faction_name_taken(faction_name):
    """
    Checks if a faction name is already taken.
    """
    try:
        response = (
            supabase.table("factions").select("*").eq("name", faction_name).execute()
        )
        if response.data:
            return True
        return False
    except Exception as e:
        print(f"Error in is_faction_name_taken: {e}")
        return False


async def get_user_faction(user_id):
    """
    Returns the name of the faction the user is in, or None if they're not in any.
    """
    try:
        await ensure_user_exists(user_id)

        response = supabase.table("users").select("faction").eq("id", user_id).execute()

        if response.data:
            return response.data[0]["faction"]
        return None
    except Exception as e:
        print(f"Error in get_user_faction: {e}")
        return None


async def add_member_to_faction(user_id, faction_name, role="member"):
    """
    Adds a user to a faction.
    """
    try:
        await ensure_user_exists(user_id)

        response = (
            supabase.table("users")
            .update({"faction": faction_name})
            .eq("id", user_id)
            .execute()
        )

        response = (
            supabase.table("faction_members")
            .insert({"user_id": user_id, "faction": faction_name, "role": role})
            .execute()
        )

        print(f"User {user_id} added to faction `{faction_name}`.")
    except Exception as e:
        print(f"Error in add_member_to_faction: {e}")


async def remove_member_from_faction(user_id):
    """
    Removes a user from their current faction.
    """
    try:
        await ensure_user_exists(user_id)

        response = (
            supabase.table("users")
            .update({"faction": None})
            .eq("id", user_id)
            .execute()
        )

        print(f"User {user_id} removed from their faction.")
    except Exception as e:
        print(f"Error in remove_member_from_faction: {e}")


async def get_faction_members(faction_name):
    """
    Returns a list of user IDs in the given faction.
    """
    try:
        response = (
            supabase.table("users").select("id").eq("faction", faction_name).execute()
        )

        if response.data:
            return [member["id"] for member in response.data]
        return []
    except Exception as e:
        print(f"Error in get_faction_members: {e}")
        return []


async def update_faction_resources(faction_name, resources):
    """
    Updates the resources of a faction.
    """
    try:
        response = (
            supabase.table("factions")
            .update({"resources": resources})
            .eq("name", faction_name)
            .execute()
        )

        print(f"Resources of faction `{faction_name}` updated.")
    except Exception as e:
        print(f"Error in update_faction_resources: {e}")


async def update_user_gold(user_id, gold):
    """
    Updates the gold of a user.
    """
    try:
        response = (
            supabase.table("users").update({"gold": gold}).eq("id", user_id).execute()
        )

        print(f"Gold of user {user_id} updated.")
    except Exception as e:
        print(f"Error in update_user_gold: {e}")


async def has_enough_gold(user_id, amount):
    """
    Checks if a user has enough gold.
    """
    try:
        response = supabase.table("users").select("gold").eq("id", user_id).execute()

        if response.data:
            return response.data[0]["gold"] >= amount
        return False
    except Exception as e:
        print(f"Error in has_enough_gold: {e}")
        return False


async def has_enough_resources(faction_name, amount):
    """
    Checks if a faction has enough resources.
    """
    try:
        response = (
            supabase.table("factions")
            .select("resources")
            .eq("name", faction_name)
            .execute()
        )

        if response.data:
            return response.data[0]["resources"] >= amount
        return False
    except Exception as e:
        print(f"Error in has_enough_resources: {e}")
        return False


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

        response = (
            supabase.table("factions")
            .select("resources")
            .eq("name", faction_name)
            .execute()
        )
        faction_resources = response.data[0]["resources"]

        if user_gold < amount:
            return False

        user_gold -= amount
        faction_resources += amount

        response = (
            supabase.table("users")
            .update({"gold": user_gold})
            .eq("id", user_id)
            .execute()
        )
        response = (
            supabase.table("factions")
            .update({"resources": faction_resources})
            .eq("name", faction_name)
            .execute()
        )

        return "Gold deposited successfully."
    except Exception as e:
        print(f"Error in deposit_gold_to_faction: {e}")
        return "An error occurred while depositing gold."


async def claim_hourly(user_id):
    """
    Allows a user to claim their hourly reward if eligible.
    """
    try:
        await ensure_user_exists(user_id)

        response = (
            supabase.table("users")
            .select("last_hourly_claim, gold")
            .eq("id", user_id)
            .execute()
        )
        user_data = response.data[0]

        last_claim_time = user_data["last_hourly_claim"]
        current_time = datetime.now(timezone.utc)

        if last_claim_time and (
            current_time - datetime.fromisoformat(last_claim_time)
        ) < timedelta(hours=2):
            remaining_time = timedelta(hours=1) - (
                current_time - datetime.fromisoformat(last_claim_time)
            )
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"Please wait {hours}h {minutes}m {seconds}s before claiming again."

        reward = random.randint(50, 150)

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


async def coinflip(challenger_id, opponent_id, amount):
    """
    Executes a coinflip between two users.
    """
    try:
        await ensure_user_exists(challenger_id)
        await ensure_user_exists(opponent_id)

        challenger_response = (
            supabase.table("users").select("gold").eq("id", challenger_id).execute()
        )
        opponent_response = (
            supabase.table("users").select("gold").eq("id", opponent_id).execute()
        )

        challenger_gold = challenger_response.data[0]["gold"]
        opponent_gold = opponent_response.data[0]["gold"]

        if challenger_gold < amount:
            return f"You don't have enough gold to bet {amount}."
        if opponent_gold < amount:
            return f"Opponent doesn't have enough gold to bet {amount}."

        supabase.table("users").update({"gold": challenger_gold - amount}).eq(
            "id", challenger_id
        ).execute()
        supabase.table("users").update({"gold": opponent_gold - amount}).eq(
            "id", opponent_id
        ).execute()

        winner_id = challenger_id if random.choice([True, False]) else opponent_id

        supabase.table("users").update(
            {
                "gold": supabase.table("users")
                .select("gold")
                .eq("id", winner_id)
                .execute()
                .data[0]["gold"]
                + (amount * 2)
            }
        ).eq("id", winner_id).execute()

        return f"Coinflip result: {'You win!' if winner_id == challenger_id else 'You lose!'} {amount} gold goes to the winner."
    except Exception as e:
        print(f"Error in coinflip: {e}")
        return "An error occurred during the coinflip."


async def get_user_balance(user_id):
    """
    Returns the gold balance of a user.
    """
    try:
        response = supabase.table("users").select("gold").eq("id", user_id).execute()
        return response.data[0]["gold"]
    except Exception as e:
        print(f"Error in get_user_balance: {e}")
        return 0


async def is_leader(user_id):
    """
    Checks if a user is a faction leader.
    """
    try:
        response = (
            supabase.table("factions")
            .select("leader_id")
            .eq("leader_id", user_id)
            .execute()
        )

        return bool(response.data)
    except Exception as e:
        print(f"Error in is_leader: {e}")
        return False


async def remove_faction(faction_name):
    """
    Removes a faction and its members.
    """
    try:
        response = (
            supabase.table("factions").delete().eq("name", faction_name).execute()
        )
        print(f"Faction `{faction_name}` removed.")
    except Exception as e:
        print(f"Error in remove_faction: {e}")


async def get_top_factions():
    """
    Returns the top 10 factions by resources.
    """
    try:
        response = (
            supabase.table("factions")
            .select("name, resources")
            .order("resources", desc=True)
            .limit(10)
            .execute()
        )

        return response.data
    except Exception as e:
        print(f"Error in get_top_factions: {e}")
        return []
