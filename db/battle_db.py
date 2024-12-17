import random
from db.user_db import (
    ensure_user_exists,
    get_user_class,
    get_user_health,
    update_user_health,
    reset_user_stats,
    get_user_final_attack,
    get_user_final_defense,
)
from data.classes import classes


async def multi_duel(team1_ids, team2_ids):
    """
    Executes a multi-team battle between two teams of varying sizes.
    team1_ids, team2_ids: lists of user_id strings (each up to length 4).
    Returns (response_string, winning_team_ids, losing_team_ids)
    If no winner, returns (response_string, None, None).
    """
    try:
        # Ensure all users exist and have classes
        team1_classes = {}
        team2_classes = {}

        for uid in team1_ids:
            await ensure_user_exists(uid)
            user_cls_name = await get_user_class(uid)
            if not user_cls_name or user_cls_name not in classes:
                return (f"<@{uid}> does not have a valid class.", None, None)
            team1_classes[uid] = classes[user_cls_name]

        for uid in team2_ids:
            await ensure_user_exists(uid)
            user_cls_name = await get_user_class(uid)
            if not user_cls_name or user_cls_name not in classes:
                return (f"<@{uid}> does not have a valid class.", None, None)
            team2_classes[uid] = classes[user_cls_name]

        # Check if any participant is too weak to fight (0 health)
        for uid in team1_ids:
            if await get_user_health(uid) <= 0:
                return (f"<@{uid}> is too weak to fight!", None, None)
        for uid in team2_ids:
            if await get_user_health(uid) <= 0:
                return (f"<@{uid}> is too weak to fight!", None, None)

        # Calculate each participant's effective attack and defense
        # We will do a single round of attacks:
        # For simplicity:
        # 1. Calculate total attack values for each team.
        # 2. Calculate total defense values for each team.
        # 3. Determine damage dealt by each team to the other.
        # We can sum up the team's total effective_attack and effective_defense, then compare.

        def calc_effective_stats(user_id, user_class):
            # Similar logic as duel
            # random rolls
            attack_roll = random.randint(1, 10)
            defense_roll = random.randint(1, 5)
            # get final attack/defense (including upgrades)
            # synergy or vulnerabilities/resistances can be considered by checking classes of all participants.
            # For simplicity, apply vulnerability/resistance based on random pairing:
            # We'll consider that vulnerabilities/resistances scale based on presence of an enemy class that triggers it.

            # Basic final attack/defense
            return attack_roll, defense_roll

        # To incorporate vulnerabilities/resistances in a team scenario,
        # we consider if the opposing team has classes that cause vulnerability or resistance.
        # For each user, we check if any enemy class triggers vulnerability/resistance.
        # If vulnerability found, attack_mod * 1.5
        # If resistance found, attack_mod * 0.5
        # If both found, they can stack or you handle accordingly (here we’ll just multiply factors).

        def compute_user_attack_defense(uid, uclass, enemy_classes):
            user_final_atk = 0
            user_final_def = 0

            # Get user final attack and defense from db
            # This includes faction upgrades, power, etc.
            # We already have get_user_final_attack and get_user_final_defense
            return user_final_atk, user_final_def  # We'll fill these in after synergy logic

        # Let’s implement the final logic now more concretely.

        # First, gather all enemy class names for synergy calculation:
        team1_class_names = [await get_user_class(uid) for uid in team1_ids]
        team2_class_names = [await get_user_class(uid) for uid in team2_ids]

        # Compute each user's effective attack and defense
        # We'll incorporate vulnerabilities/resistances:
        def get_attack_mod(u_cls_name, enemy_classes):
            # If user's class is in some enemy's resistances, user_attack_mod *=0.5
            # If user's class is in some enemy's vulnerabilities, user_attack_mod *=1.5
            # Check all enemies, if any enemy resists this user's class -> mod *0.5
            # If any enemy is vulnerable to this user's class -> mod *1.5

            user_attack_mod = 1.0
            for e_cls_name in enemy_classes:
                e_cls = classes[e_cls_name]
                if u_cls_name in e_cls.get("resistances", []):
                    user_attack_mod *= 0.5
                if u_cls_name in e_cls.get("vulnerabilities", []):
                    user_attack_mod *= 1.5
            return user_attack_mod

        team1_final_stats = []  # will hold (uid, effective_attack, effective_defense)
        for uid in team1_ids:
            u_cls_name = await get_user_class(uid)
            user_attack_mod = get_attack_mod(u_cls_name, team2_class_names)

            base_attack = await get_user_final_attack(uid)
            base_defense = await get_user_final_defense(uid)

            # random rolls as in duel
            attack_roll = random.randint(1, 10)
            defense_roll = random.randint(1, 5)

            effective_attack = (base_attack + attack_roll) * user_attack_mod
            effective_defense = base_defense + defense_roll

            team1_final_stats.append((uid, effective_attack, effective_defense))

        team2_final_stats = []
        for uid in team2_ids:
            u_cls_name = await get_user_class(uid)
            user_attack_mod = get_attack_mod(u_cls_name, team1_class_names)

            base_attack = await get_user_final_attack(uid)
            base_defense = await get_user_final_defense(uid)

            attack_roll = random.randint(1, 10)
            defense_roll = random.randint(1, 5)

            effective_attack = (base_attack + attack_roll) * user_attack_mod
            effective_defense = base_defense + defense_roll

            team2_final_stats.append((uid, effective_attack, effective_defense))

        # Sum up total attack and defense
        team1_total_attack = sum(x[1] for x in team1_final_stats)
        team1_total_defense = sum(x[2] for x in team1_final_stats)

        team2_total_attack = sum(x[1] for x in team2_final_stats)
        team2_total_defense = sum(x[2] for x in team2_final_stats)

        # Calculate damage dealt by each team to the other
        # If we simply do: damage_to_team2 = max(0, team1_total_attack - team2_total_defense)
        # damage_to_team1 = max(0, team2_total_attack - team1_total_defense)
        damage_to_team2 = max(0, team1_total_attack - team2_total_defense)
        damage_to_team1 = max(0, team2_total_attack - team1_total_defense)

        # Distribute damage equally among all members of the opposing team
        # For simplicity, just evenly split damage.
        def distribute_damage(team_stats, total_damage):
            if len(team_stats) == 0:
                return []
            damage_each = total_damage / len(team_stats)
            return [damage_each for _ in team_stats]

        team1_damage_taken = distribute_damage(team1_final_stats, damage_to_team1)
        team2_damage_taken = distribute_damage(team2_final_stats, damage_to_team2)

        # Update health
        team1_new_healths = []
        team2_new_healths = []
        response = "## Multi-Team Battle Result\n"
        response += "**Team 1:** " + ", ".join(f"<@{x}>" for x in team1_ids) + "\n"
        response += "**Team 2:** " + ", ".join(f"<@{x}>" for x in team2_ids) + "\n\n"

        # Update team 1 health
        for i, (uid, atk, dfn) in enumerate(team1_final_stats):
            old_hp = await get_user_health(uid)
            damage_taken = team1_damage_taken[i]
            new_hp = max(0, old_hp - damage_taken)
            await update_user_health(uid, new_hp)
            response += (
                f"- <@{uid}> ({await get_user_class(uid)}) took **{damage_taken:.1f} damage**. "
                f"{'They were defeated and will need to recover.' if new_hp <= 0 else f'Remaining health: **{new_hp}**.'}\n"
            )
            team1_new_healths.append(new_hp)

        # Update team 2 health
        for i, (uid, atk, dfn) in enumerate(team2_final_stats):
            old_hp = await get_user_health(uid)
            damage_taken = team2_damage_taken[i]
            new_hp = max(0, old_hp - damage_taken)
            await update_user_health(uid, new_hp)
            response += (
                f"- <@{uid}> ({await get_user_class(uid)}) took **{damage_taken:.1f} damage**. "
                f"{'They were defeated and will need to recover.' if new_hp <= 0 else f'Remaining health: **{new_hp}**.'}\n"
            )
            team2_new_healths.append(new_hp)

        # Check for defeated users and reset them
        for i, uid in enumerate(team1_ids):
            if team1_new_healths[i] <= 0:
                await reset_user_stats(uid)
        for i, uid in enumerate(team2_ids):
            if team2_new_healths[i] <= 0:
                await reset_user_stats(uid)

        # Determine winner
        team1_alive = any(hp > 0 for hp in team1_new_healths)
        team2_alive = any(hp > 0 for hp in team2_new_healths)

        winning_team = None
        losing_team = None

        if team1_alive and not team2_alive:
            winning_team = team1_ids
            losing_team = team2_ids
            response += "\n**Team 1 is victorious!**"
        elif team2_alive and not team1_alive:
            winning_team = team2_ids
            losing_team = team1_ids
            response += "\n**Team 2 is victorious!**"
        elif not team1_alive and not team2_alive:
            response += "\n**Both teams have been defeated!** It's a draw."
        else:
            # Both teams alive, decide by total damage dealt
            if damage_to_team2 > damage_to_team1:
                winning_team = team1_ids
                losing_team = team2_ids
                response += "\n**Team 1 wins by dealing more damage!**"
            elif damage_to_team1 > damage_to_team2:
                winning_team = team2_ids
                losing_team = team1_ids
                response += "\n**Team 2 wins by dealing more damage!**"
            else:
                response += "\n**No clear winner! It's a draw.**"

        return (response, winning_team, losing_team)
    except Exception as e:
        print(f"Error in multi_duel: {e}")
        return ("An error occurred during the multi-team battle.", None, None)
