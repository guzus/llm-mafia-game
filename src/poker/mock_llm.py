"""
Mock LLM implementation for testing the poker game without making API calls.
"""

import random


def get_mock_response(model_name, prompt):
    """
    Generate a mock response for testing.

    Args:
        model_name (str): The name of the LLM model.
        prompt (str): The prompt sent to the model.

    Returns:
        str: A mock response.
    """
    # Extract game state information from the prompt
    hole_cards = None
    community_cards = None
    chips = None
    current_bet = None

    for line in prompt.split("\n"):
        if "Your hole cards:" in line:
            hole_cards = line.split("Your hole cards:")[1].strip()
        elif "Community cards:" in line:
            community_cards = line.split("Community cards:")[1].strip()
        elif "Your chips:" in line:
            chips = line.split("Your chips:")[1].strip()
        elif "Current bet to call:" in line:
            current_bet = line.split("Current bet to call:")[1].strip()

    # Generate a response based on the game state
    if community_cards and "None" in community_cards:  # Pre-flop
        return _generate_preflop_action(hole_cards, current_bet, chips)
    else:
        return _generate_postflop_action(
            hole_cards, community_cards, current_bet, chips
        )


def _generate_preflop_action(hole_cards, current_bet, chips):
    """Generate a pre-flop action."""
    # Check if we have a strong starting hand
    strong_hand = False

    # Check for pairs
    if hole_cards and (
        "A♠, A♥" in hole_cards
        or "A♦, A♣" in hole_cards
        or "K♠, K♥" in hole_cards
        or "K♦, K♣" in hole_cards
    ):
        strong_hand = True

    # Check for high cards
    if hole_cards and "A" in hole_cards and "K" in hole_cards:
        strong_hand = True

    if strong_hand:
        # With a strong hand, raise or bet
        if current_bet and int(current_bet) > 0:
            raise_amount = min(int(current_bet) * 3, int(chips) if chips else 100)
            return f"I have a strong hand. I'll RAISE {raise_amount}."
        else:
            bet_amount = min(20, int(chips) if chips else 100)
            return f"I have a strong hand. I'll BET {bet_amount}."
    else:
        # With a weak hand, check or call if the bet is small, otherwise fold
        if not current_bet or int(current_bet) == 0:
            return "I'll CHECK."
        elif int(current_bet) < 20:
            return "I'll CALL."
        else:
            return "I'll FOLD."


def _generate_postflop_action(hole_cards, community_cards, current_bet, chips):
    """Generate a post-flop action."""
    # Randomly decide if we have a good hand
    has_good_hand = random.random() < 0.3

    if has_good_hand:
        # With a good hand, bet or raise
        if current_bet and int(current_bet) > 0:
            if int(current_bet) > int(chips) // 2 if chips else 500:
                return "I'm going ALL-IN!"
            else:
                raise_amount = min(int(current_bet) * 2, int(chips) if chips else 100)
                return f"I have a good hand. I'll RAISE {raise_amount}."
        else:
            bet_amount = min(30, int(chips) if chips else 100)
            return f"I have a good hand. I'll BET {bet_amount}."
    else:
        # With a weak hand, check or call if the bet is small, otherwise fold
        if not current_bet or int(current_bet) == 0:
            return "I'll CHECK."
        elif current_bet and int(current_bet) < int(chips) // 10 if chips else 100:
            return "I'll CALL."
        else:
            return "I'll FOLD."
