"""
Game logic for the LLM Poker Game.
"""

import random
import uuid
import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from poker_player import PokerPlayer
from card import Deck, HandEvaluator
from poker_templates import PokerAction
import poker_config as config
from src.logger import GameLogger, Color


class PokerGame:
    """Represents a poker game with LLM players."""

    def __init__(self, models=None, language=None):
        """
        Initialize a poker game.

        Args:
            models (list, optional): List of model names to use as players.
            language (str, optional): Language for game prompts and interactions. Defaults to config.LANGUAGE.
        """
        self.game_id = str(uuid.uuid4())
        self.hand_number = 0
        self.players = []
        self.active_players = []  # Players still in the current hand
        self.deck = Deck()
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = config.BIG_BLIND
        self.dealer_position = 0
        self.current_player_index = 0
        self.betting_round = "pre-flop"  # pre-flop, flop, turn, river
        self.language = language if language is not None else config.LANGUAGE
        self.round_actions = []
        self.previous_rounds = []

        # Use provided models or default from config
        self.models = models if models else config.MODELS

        # Set random seed if specified
        if config.RANDOM_SEED is not None:
            random.seed(config.RANDOM_SEED)

        # Initialize logger
        self.logger = GameLogger()

    def setup_game(self):
        """
        Set up the game by creating players and assigning positions.

        Returns:
            bool: True if setup successful, False otherwise.
        """
        # Check if we have enough models
        if len(self.models) < config.PLAYERS_PER_GAME:
            self.logger.error(
                f"Not enough models. Need {config.PLAYERS_PER_GAME}, but only have {len(self.models)}."
            )
            return False

        # Log game start
        self.logger.game_start(1, self.game_id, self.language)

        # Randomly select models for this game
        selected_models = random.sample(self.models, config.PLAYERS_PER_GAME)

        # Create players
        self.logger.header("PLAYER SETUP", Color.CYAN)
        for i, model_name in enumerate(selected_models):
            position = i  # Position 0 is the dealer/button
            player = PokerPlayer(
                model_name, position, config.STARTING_CHIPS, language=self.language
            )
            self.players.append(player)
            self.logger.print(f"Created player: {player}")

        return True

    def start_new_hand(self):
        """Start a new hand of poker."""
        self.hand_number += 1
        self.logger.header(f"STARTING HAND #{self.hand_number}", Color.GREEN)

        # Reset deck and shuffle
        self.deck.reset()
        self.deck.shuffle()

        # Reset game state
        self.community_cards = []
        self.pot = 0
        self.current_bet = 0
        self.min_raise = config.BIG_BLIND
        self.betting_round = "pre-flop"
        self.round_actions = []
        self.previous_rounds = []

        # Reset players for new hand
        for player in self.players:
            player.reset_for_new_hand()

        # Set active players (only players with chips)
        self.active_players = [p for p in self.players if p.chips > 0]

        # Rotate dealer position
        self.dealer_position = (self.dealer_position + 1) % len(self.players)

        # Deal hole cards
        self.deal_hole_cards()

        # Post blinds
        self.post_blinds()

        # Set first player to act (after big blind)
        self.current_player_index = (self.dealer_position + 3) % len(
            self.active_players
        )
        if len(self.active_players) <= 3:  # Adjust for fewer players
            self.current_player_index = (self.dealer_position + 1) % len(
                self.active_players
            )

    def deal_hole_cards(self):
        """Deal two hole cards to each active player."""
        for player in self.active_players:
            cards = self.deck.deal(2)
            player.receive_cards(cards)
            self.logger.print(f"{player.model_name} receives: {cards[0]}, {cards[1]}")

    def post_blinds(self):
        """Post the small and big blinds."""
        # Small blind is to the left of the dealer
        sb_position = (self.dealer_position + 1) % len(self.active_players)
        sb_player = self.active_players[sb_position]
        sb_amount = min(config.SMALL_BLIND, sb_player.chips)
        sb_player.chips -= sb_amount
        sb_player.current_bet = sb_amount
        self.pot += sb_amount
        self.logger.print(f"{sb_player.model_name} posts small blind: {sb_amount}")

        # Big blind is to the left of the small blind
        bb_position = (self.dealer_position + 2) % len(self.active_players)
        bb_player = self.active_players[bb_position]
        bb_amount = min(config.BIG_BLIND, bb_player.chips)
        bb_player.chips -= bb_amount
        bb_player.current_bet = bb_amount
        self.pot += bb_amount
        self.current_bet = bb_amount
        self.logger.print(f"{bb_player.model_name} posts big blind: {bb_amount}")

        # Add blind actions to round actions
        self.round_actions.append(
            f"{sb_player.model_name} posts small blind: {sb_amount}"
        )
        self.round_actions.append(
            f"{bb_player.model_name} posts big blind: {bb_amount}"
        )

    def execute_betting_round(self):
        """
        Execute a betting round.

        Returns:
            bool: True if the hand should continue, False if it's over.
        """
        self.logger.header(f"BETTING ROUND: {self.betting_round.upper()}", Color.YELLOW)

        # If only one player remains, end the hand
        if len([p for p in self.active_players if not p.folded and not p.all_in]) <= 1:
            return False

        # Reset for new betting round
        for player in self.active_players:
            player.current_bet = 0
        self.current_bet = 0

        # Start with the player after the dealer in post-flop rounds
        if self.betting_round != "pre-flop":
            self.current_player_index = (self.dealer_position + 1) % len(
                self.active_players
            )
            # Skip players who have folded or are all-in
            while (
                self.active_players[self.current_player_index].folded
                or self.active_players[self.current_player_index].all_in
            ):
                self.current_player_index = (self.current_player_index + 1) % len(
                    self.active_players
                )
                # If we've gone all the way around, everyone is folded or all-in
                if self.current_player_index == (self.dealer_position + 1) % len(
                    self.active_players
                ):
                    return False

        # Keep track of the last player to raise
        last_raiser = None

        # Continue until all players have had a chance to act after the last raise
        while True:
            current_player = self.active_players[self.current_player_index]

            # Skip players who have folded or are all-in
            if current_player.folded or current_player.all_in:
                self.current_player_index = (self.current_player_index + 1) % len(
                    self.active_players
                )
                continue

            # If we've gone around to the last raiser, betting round is over
            if last_raiser is not None and self.current_player_index == last_raiser:
                break

            # If everyone has acted and there's no bet, betting round is over
            if self.current_bet == 0 and all(
                p.current_bet == 0
                for p in self.active_players
                if not p.folded and not p.all_in
            ):
                # If we've gone all the way around, betting round is over
                if self.current_player_index == (self.dealer_position + 1) % len(
                    self.active_players
                ):
                    break

            # Get the amount the player needs to call
            amount_to_call = self.current_bet - current_player.current_bet

            # Get player action
            action, amount = self.get_player_action(current_player, amount_to_call)

            # Process the action
            if action == PokerAction.FOLD:
                current_player.folded = True
                self.logger.print(f"{current_player.model_name} folds")
                self.round_actions.append(f"{current_player.model_name} folds")

            elif action == PokerAction.CHECK:
                self.logger.print(f"{current_player.model_name} checks")
                self.round_actions.append(f"{current_player.model_name} checks")

            elif action == PokerAction.CALL:
                current_player.chips -= amount
                current_player.current_bet += amount
                self.pot += amount
                self.logger.print(f"{current_player.model_name} calls {amount}")
                self.round_actions.append(f"{current_player.model_name} calls {amount}")

            elif action == PokerAction.BET:
                current_player.chips -= amount
                current_player.current_bet += amount
                self.pot += amount
                self.current_bet = amount
                self.logger.print(f"{current_player.model_name} bets {amount}")
                self.round_actions.append(f"{current_player.model_name} bets {amount}")
                last_raiser = self.current_player_index

            elif action == PokerAction.RAISE:
                current_player.chips -= amount
                current_player.current_bet += amount
                self.pot += amount
                self.current_bet = current_player.current_bet
                self.logger.print(
                    f"{current_player.model_name} raises to {current_player.current_bet}"
                )
                self.round_actions.append(
                    f"{current_player.model_name} raises to {current_player.current_bet}"
                )
                last_raiser = self.current_player_index

            elif action == PokerAction.ALL_IN:
                self.pot += amount
                current_player.current_bet += amount
                current_player.chips = 0
                current_player.all_in = True

                # If this all-in is a raise, update the current bet
                if current_player.current_bet > self.current_bet:
                    self.current_bet = current_player.current_bet
                    last_raiser = self.current_player_index
                    self.logger.print(
                        f"{current_player.model_name} goes all-in for {amount} (raise)"
                    )
                    self.round_actions.append(
                        f"{current_player.model_name} goes all-in for {amount} (raise)"
                    )
                else:
                    self.logger.print(
                        f"{current_player.model_name} goes all-in for {amount} (call)"
                    )
                    self.round_actions.append(
                        f"{current_player.model_name} goes all-in for {amount} (call)"
                    )

            # Move to the next player
            self.current_player_index = (self.current_player_index + 1) % len(
                self.active_players
            )

            # If only one player remains, end the hand
            active_not_folded = [p for p in self.active_players if not p.folded]
            if len(active_not_folded) == 1:
                return False

        # Add this round's actions to previous rounds
        self.previous_rounds.append(
            f"{self.betting_round.upper()}: {'; '.join(self.round_actions)}"
        )
        self.round_actions = []

        return True

    def get_player_action(self, player, amount_to_call):
        """
        Get an action from a player.

        Args:
            player (PokerPlayer): The player to get an action from.
            amount_to_call (int): The amount the player needs to call.

        Returns:
            tuple: (action, amount) where action is a PokerAction and amount is an integer.
        """
        # Get player chips information
        player_chips = {p.model_name: p.chips for p in self.active_players}

        # Get active players (not folded)
        active_not_folded = [p for p in self.active_players if not p.folded]

        # Generate prompt for the player
        prompt = player.generate_prompt(
            self.community_cards,
            self.pot,
            amount_to_call,
            active_not_folded,
            player_chips,
            "; ".join(self.round_actions),
            "; ".join(self.previous_rounds),
        )

        # Get response from the player
        self.logger.print(f"Asking {player.model_name} for action...")
        response = player.get_response(prompt)
        self.logger.print(f"Response from {player.model_name}: {response}")

        # Parse the action
        action, amount = player.parse_action(response, amount_to_call, self.min_raise)

        return action, amount

    def deal_community_cards(self, num_cards):
        """
        Deal community cards.

        Args:
            num_cards (int): The number of cards to deal.
        """
        new_cards = self.deck.deal(num_cards)
        self.community_cards.extend(new_cards)
        self.logger.print(
            f"Community cards: {', '.join(str(card) for card in self.community_cards)}"
        )

    def determine_winners(self):
        """
        Determine the winner(s) of the hand.

        Returns:
            list: A list of winning players.
        """
        # If only one player remains, they win
        active_not_folded = [p for p in self.active_players if not p.folded]
        if len(active_not_folded) == 1:
            return active_not_folded

        # Evaluate hands for all players still in the hand
        player_hands = []
        for player in active_not_folded:
            hand_rank, hand_value, best_hand = HandEvaluator.evaluate_hand(
                player.hole_cards, self.community_cards
            )
            player_hands.append((player, hand_rank, hand_value, best_hand))
            self.logger.print(
                f"{player.model_name}'s hand: {hand_rank.value} ({', '.join(str(card) for card in best_hand)})"
            )

        # Sort by hand value (highest first)
        player_hands.sort(key=lambda x: x[2], reverse=True)

        # Find the winners (players with the highest hand value)
        winners = []
        highest_value = player_hands[0][2]
        for player, hand_rank, hand_value, best_hand in player_hands:
            if hand_value == highest_value:
                winners.append(player)

        return winners

    def award_pot(self, winners):
        """
        Award the pot to the winner(s).

        Args:
            winners (list): A list of winning players.
        """
        if not winners:
            return

        # Split the pot evenly among winners
        pot_per_winner = self.pot // len(winners)
        remainder = self.pot % len(winners)

        for i, player in enumerate(winners):
            # Add an extra chip to the first few winners if the pot doesn't divide evenly
            extra = 1 if i < remainder else 0
            player.chips += pot_per_winner + extra
            self.logger.print(
                f"{player.model_name} wins {pot_per_winner + extra} chips"
            )

    def run_hand(self):
        """
        Run a single hand of poker.

        Returns:
            list: A list of winning players.
        """
        # Start a new hand
        self.start_new_hand()

        # Pre-flop betting round
        if not self.execute_betting_round():
            winners = self.determine_winners()
            self.award_pot(winners)
            return winners

        # Deal the flop (3 cards)
        self.betting_round = "flop"
        self.deal_community_cards(3)

        # Flop betting round
        if not self.execute_betting_round():
            winners = self.determine_winners()
            self.award_pot(winners)
            return winners

        # Deal the turn (1 card)
        self.betting_round = "turn"
        self.deal_community_cards(1)

        # Turn betting round
        if not self.execute_betting_round():
            winners = self.determine_winners()
            self.award_pot(winners)
            return winners

        # Deal the river (1 card)
        self.betting_round = "river"
        self.deal_community_cards(1)

        # River betting round
        if not self.execute_betting_round():
            winners = self.determine_winners()
            self.award_pot(winners)
            return winners

        # Showdown
        winners = self.determine_winners()
        self.award_pot(winners)
        return winners

    def run_game(self):
        """
        Run a full poker game.

        Returns:
            dict: A dictionary with game results.
        """
        # Set up the game
        if not self.setup_game():
            return {"error": "Failed to set up game"}

        # Run hands until we reach the maximum number of hands or only one player has chips
        hand_results = []
        for _ in range(config.MAX_ROUNDS):
            # Check if only one player has chips
            players_with_chips = [p for p in self.players if p.chips > 0]
            if len(players_with_chips) <= 1:
                break

            # Run a hand
            winners = self.run_hand()

            # Record hand results
            hand_result = {
                "hand_number": self.hand_number,
                "winners": [w.model_name for w in winners],
                "pot": self.pot,
                "community_cards": [str(card) for card in self.community_cards],
                "player_chips": {p.model_name: p.chips for p in self.players},
            }
            hand_results.append(hand_result)

        # Determine the overall winner (player with the most chips)
        self.players.sort(key=lambda p: p.chips, reverse=True)
        overall_winner = self.players[0]

        # Log game results
        self.logger.header("GAME RESULTS", Color.GREEN)
        for player in self.players:
            self.logger.print(f"{player.model_name}: {player.chips} chips")
        self.logger.print(
            f"Overall winner: {overall_winner.model_name} with {overall_winner.chips} chips"
        )

        # Return game results
        return {
            "game_id": self.game_id,
            "overall_winner": overall_winner.model_name,
            "player_chips": {p.model_name: p.chips for p in self.players},
            "hand_results": hand_results,
        }
