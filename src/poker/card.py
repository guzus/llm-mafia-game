"""
Card and Deck classes for the LLM Poker Game.
"""

import random
from src.poker.poker_templates import SUITS, VALUES


class Card:
    """Represents a playing card."""

    def __init__(self, value, suit):
        """
        Initialize a card.

        Args:
            value (str): The value of the card (2-10, J, Q, K, A).
            suit (str): The suit of the card (♠, ♥, ♦, ♣).
        """
        self.value = value
        self.suit = suit
        self.value_index = VALUES.index(value)

    def __str__(self):
        """Return a string representation of the card."""
        return f"{self.value}{self.suit}"

    def __repr__(self):
        """Return a string representation of the card."""
        return self.__str__()

    def __eq__(self, other):
        """Check if two cards are equal."""
        if not isinstance(other, Card):
            return False
        return self.value == other.value and self.suit == other.suit

    def __lt__(self, other):
        """Compare cards by value."""
        if not isinstance(other, Card):
            return NotImplemented
        return self.value_index < other.value_index


class Deck:
    """Represents a deck of cards."""

    def __init__(self):
        """Initialize a deck of cards."""
        self.cards = []
        self.reset()

    def reset(self):
        """Reset the deck to a full set of cards."""
        self.cards = []
        for suit in SUITS:
            for value in VALUES:
                self.cards.append(Card(value, suit))

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def deal(self, num_cards=1):
        """
        Deal cards from the deck.

        Args:
            num_cards (int): The number of cards to deal.

        Returns:
            list: A list of Card objects.
        """
        if num_cards > len(self.cards):
            raise ValueError(
                f"Cannot deal {num_cards} cards, only {len(self.cards)} remaining."
            )

        dealt_cards = []
        for _ in range(num_cards):
            dealt_cards.append(self.cards.pop())

        return dealt_cards


class HandEvaluator:
    """Evaluates poker hands."""

    @staticmethod
    def evaluate_hand(hole_cards, community_cards):
        """
        Evaluate the best 5-card poker hand from hole cards and community cards.

        Args:
            hole_cards (list): A list of 2 Card objects (player's hole cards).
            community_cards (list): A list of up to 5 Card objects (community cards).

        Returns:
            tuple: (hand_rank, hand_value, best_hand) where hand_rank is a PokerHand enum,
                  hand_value is a numerical value for comparing hands of the same rank,
                  and best_hand is a list of the 5 cards that make up the best hand.
        """
        from src.poker.poker_templates import PokerHand

        # Combine hole cards and community cards
        all_cards = hole_cards + community_cards

        # Check for each hand type, from highest to lowest
        # Royal Flush
        royal_flush = HandEvaluator._check_royal_flush(all_cards)
        if royal_flush:
            return (PokerHand.ROYAL_FLUSH, 9, royal_flush)

        # Straight Flush
        straight_flush = HandEvaluator._check_straight_flush(all_cards)
        if straight_flush:
            return (
                PokerHand.STRAIGHT_FLUSH,
                8 + straight_flush[0].value_index / 14,
                straight_flush,
            )

        # Four of a Kind
        four_of_a_kind = HandEvaluator._check_four_of_a_kind(all_cards)
        if four_of_a_kind:
            return (
                PokerHand.FOUR_OF_A_KIND,
                7 + four_of_a_kind[0].value_index / 14,
                four_of_a_kind,
            )

        # Full House
        full_house = HandEvaluator._check_full_house(all_cards)
        if full_house:
            return (
                PokerHand.FULL_HOUSE,
                6 + full_house[0].value_index / 14,
                full_house,
            )

        # Flush
        flush = HandEvaluator._check_flush(all_cards)
        if flush:
            return (PokerHand.FLUSH, 5 + flush[0].value_index / 14, flush)

        # Straight
        straight = HandEvaluator._check_straight(all_cards)
        if straight:
            return (PokerHand.STRAIGHT, 4 + straight[0].value_index / 14, straight)

        # Three of a Kind
        three_of_a_kind = HandEvaluator._check_three_of_a_kind(all_cards)
        if three_of_a_kind:
            return (
                PokerHand.THREE_OF_A_KIND,
                3 + three_of_a_kind[0].value_index / 14,
                three_of_a_kind,
            )

        # Two Pair
        two_pair = HandEvaluator._check_two_pair(all_cards)
        if two_pair:
            return (PokerHand.TWO_PAIR, 2 + two_pair[0].value_index / 14, two_pair)

        # Pair
        pair = HandEvaluator._check_pair(all_cards)
        if pair:
            return (PokerHand.PAIR, 1 + pair[0].value_index / 14, pair)

        # High Card
        high_card = HandEvaluator._check_high_card(all_cards)
        return (PokerHand.HIGH_CARD, high_card[0].value_index / 14, high_card)

    @staticmethod
    def _check_royal_flush(cards):
        """Check for a royal flush."""
        for suit in SUITS:
            royal_values = ["10", "J", "Q", "K", "A"]
            royal_cards = [Card(value, suit) for value in royal_values]
            if all(card in cards for card in royal_cards):
                return royal_cards
        return None

    @staticmethod
    def _check_straight_flush(cards):
        """Check for a straight flush."""
        for suit in SUITS:
            suited_cards = [card for card in cards if card.suit == suit]
            if len(suited_cards) >= 5:
                suited_cards.sort(reverse=True)
                for i in range(len(suited_cards) - 4):
                    if all(
                        suited_cards[i + j].value_index
                        == suited_cards[i].value_index - j
                        for j in range(5)
                    ):
                        return suited_cards[i : i + 5]

                # Check for A-5 straight flush (special case)
                if any(card.value == "A" for card in suited_cards):
                    ace = next(card for card in suited_cards if card.value == "A")
                    low_straight = [
                        card
                        for card in suited_cards
                        if card.value in ["A", "2", "3", "4", "5"]
                    ]
                    if len(low_straight) >= 5:
                        low_straight.sort(
                            key=lambda x: (0 if x.value == "A" else x.value_index + 1)
                        )
                        return low_straight[:5]
        return None

    @staticmethod
    def _check_four_of_a_kind(cards):
        """Check for four of a kind."""
        value_groups = {}
        for card in cards:
            if card.value not in value_groups:
                value_groups[card.value] = []
            value_groups[card.value].append(card)

        for value, group in value_groups.items():
            if len(group) == 4:
                # Find the highest card that's not part of the four of a kind
                kickers = [card for card in cards if card.value != value]
                kickers.sort(reverse=True)
                return group + [kickers[0]]

        return None

    @staticmethod
    def _check_full_house(cards):
        """Check for a full house."""
        value_groups = {}
        for card in cards:
            if card.value not in value_groups:
                value_groups[card.value] = []
            value_groups[card.value].append(card)

        three_of_a_kind = None
        pair = None

        # Find the highest three of a kind
        for value, group in sorted(
            value_groups.items(), key=lambda x: VALUES.index(x[0]), reverse=True
        ):
            if len(group) >= 3 and three_of_a_kind is None:
                three_of_a_kind = group[:3]
            elif len(group) >= 2 and pair is None:
                pair = group[:2]

            if three_of_a_kind and pair:
                return three_of_a_kind + pair

        return None

    @staticmethod
    def _check_flush(cards):
        """Check for a flush."""
        suit_groups = {}
        for card in cards:
            if card.suit not in suit_groups:
                suit_groups[card.suit] = []
            suit_groups[card.suit].append(card)

        for suit, group in suit_groups.items():
            if len(group) >= 5:
                group.sort(reverse=True)
                return group[:5]

        return None

    @staticmethod
    def _check_straight(cards):
        """Check for a straight."""
        # Remove duplicates by value
        unique_values = {}
        for card in cards:
            if (
                card.value not in unique_values
                or card.value_index > unique_values[card.value].value_index
            ):
                unique_values[card.value] = card

        unique_cards = list(unique_values.values())
        unique_cards.sort(reverse=True)

        # Check for regular straight
        for i in range(len(unique_cards) - 4):
            if all(
                unique_cards[i + j].value_index == unique_cards[i].value_index - j
                for j in range(5)
            ):
                return [unique_cards[i + j] for j in range(5)]

        # Check for A-5 straight (special case)
        if any(card.value == "A" for card in unique_cards):
            ace = next(card for card in unique_cards if card.value == "A")
            low_values = ["A", "2", "3", "4", "5"]
            low_straight = [card for card in unique_cards if card.value in low_values]
            if len(low_straight) >= 5:
                low_straight.sort(
                    key=lambda x: (0 if x.value == "A" else x.value_index + 1)
                )
                return low_straight[:5]

        return None

    @staticmethod
    def _check_three_of_a_kind(cards):
        """Check for three of a kind."""
        value_groups = {}
        for card in cards:
            if card.value not in value_groups:
                value_groups[card.value] = []
            value_groups[card.value].append(card)

        for value, group in value_groups.items():
            if len(group) == 3:
                # Find the two highest cards that are not part of the three of a kind
                kickers = [card for card in cards if card.value != value]
                kickers.sort(reverse=True)
                return group + kickers[:2]

        return None

    @staticmethod
    def _check_two_pair(cards):
        """Check for two pair."""
        value_groups = {}
        for card in cards:
            if card.value not in value_groups:
                value_groups[card.value] = []
            value_groups[card.value].append(card)

        pairs = []
        for value, group in value_groups.items():
            if len(group) >= 2:
                pairs.append((VALUES.index(value), group[:2]))

        if len(pairs) >= 2:
            # Sort pairs by value (highest first)
            pairs.sort(reverse=True)
            # Take the two highest pairs
            best_two_pairs = pairs[0][1] + pairs[1][1]
            # Find the highest card that's not part of the two pairs
            kickers = [
                card
                for card in cards
                if card.value != pairs[0][1][0].value
                and card.value != pairs[1][1][0].value
            ]
            kickers.sort(reverse=True)
            return best_two_pairs + [kickers[0]]

        return None

    @staticmethod
    def _check_pair(cards):
        """Check for a pair."""
        value_groups = {}
        for card in cards:
            if card.value not in value_groups:
                value_groups[card.value] = []
            value_groups[card.value].append(card)

        for value, group in value_groups.items():
            if len(group) == 2:
                # Find the three highest cards that are not part of the pair
                kickers = [card for card in cards if card.value != value]
                kickers.sort(reverse=True)
                return group + kickers[:3]

        return None

    @staticmethod
    def _check_high_card(cards):
        """Get the five highest cards."""
        sorted_cards = sorted(cards, reverse=True)
        return sorted_cards[:5]
