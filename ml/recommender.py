"""
CAFÉCRAFT ML RECOMMENDER SYSTEM

Responsibilities:
- Offline Apriori-based recommendation engine
- Learn ingredient combinations from transaction history
- Suggest add-ons for a given base ingredient
- Save/load association rules locally (JSON)
- No database queries

Uses Apriori algorithm for frequent itemset mining.
"""

import json
import os
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict
from itertools import combinations


class AprioriRecommender:
    """
    Apriori-based recommendation engine for ingredient combinations.
    
    Learns which ingredients are frequently purchased together
    and provides recommendations based on association rules.
    """

    def __init__(self, min_support: float = 0.05, min_confidence: float = 0.3):
        """
        Initialize recommender.

        Args:
            min_support: Minimum support threshold (0.0-1.0).
            min_confidence: Minimum confidence threshold (0.0-1.0).
        """
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.transactions = []  # List of lists (each transaction is a list of items)
        self.itemsets = {}  # {frozenset: support}
        self.rules = {}  # {(antecedent, consequent): confidence}
        self.rules_file = "ml_rules.json"

    def add_transaction(self, items: List[str]):
        """
        Add a transaction (order) to the training set.

        Args:
            items: List of ingredient/product names in the order.
        """
        if items:
            self.transactions.append(list(set(items)))  # Remove duplicates

    def add_transactions(self, transactions: List[List[str]]):
        """
        Add multiple transactions.

        Args:
            transactions: List of transactions (each is a list of items).
        """
        for items in transactions:
            self.add_transaction(items)

    def train(self):
        """Train the recommender on current transactions."""
        if not self.transactions:
            return

        # Find frequent itemsets using Apriori
        self.itemsets = self._find_frequent_itemsets()

        # Generate association rules
        self.rules = self._generate_rules()

    def _find_frequent_itemsets(self) -> Dict:
        """
        Find frequent itemsets using Apriori algorithm.

        Returns:
            Dict of {frozenset: support}
        """
        frequent_itemsets = {}
        total_transactions = len(self.transactions)

        # Count 1-itemsets
        item_counts = defaultdict(int)
        for transaction in self.transactions:
            for item in transaction:
                item_counts[item] += 1

        # Filter by min support
        frequent_1_itemsets = {
            frozenset([item]): count / total_transactions
            for item, count in item_counts.items()
            if count / total_transactions >= self.min_support
        }

        frequent_itemsets.update(frequent_1_itemsets)

        # Generate k-itemsets
        current_itemsets = frequent_1_itemsets
        k = 2

        while current_itemsets:
            # Generate candidate itemsets
            candidates = self._generate_candidates(list(current_itemsets.keys()), k)

            # Count support
            candidate_support = defaultdict(int)
            for transaction in self.transactions:
                trans_set = set(transaction)
                for candidate in candidates:
                    if candidate.issubset(trans_set):
                        candidate_support[candidate] += 1

            # Filter by min support
            frequent_k_itemsets = {
                itemset: count / total_transactions
                for itemset, count in candidate_support.items()
                if count / total_transactions >= self.min_support
            }

            if not frequent_k_itemsets:
                break

            frequent_itemsets.update(frequent_k_itemsets)
            current_itemsets = frequent_k_itemsets
            k += 1

        return frequent_itemsets

    def _generate_candidates(self, itemsets: List[frozenset], k: int) -> List[frozenset]:
        """
        Generate candidate k-itemsets from (k-1)-itemsets.

        Args:
            itemsets: List of (k-1)-itemsets.
            k: Size of candidates to generate.

        Returns:
            List of candidate k-itemsets.
        """
        candidates = []
        itemsets_list = [set(itemset) for itemset in itemsets if len(itemset) == k - 1]

        for i in range(len(itemsets_list)):
            for j in range(i + 1, len(itemsets_list)):
                union = itemsets_list[i] | itemsets_list[j]
                if len(union) == k:
                    candidates.append(frozenset(union))

        return candidates

    def _generate_rules(self) -> Dict[Tuple, float]:
        """
        Generate association rules from frequent itemsets.

        Returns:
            Dict of {(antecedent, consequent): confidence}
        """
        rules = {}

        for itemset, support in self.itemsets.items():
            if len(itemset) < 2:
                continue

            # Generate all possible rules from this itemset
            for antecedent_size in range(1, len(itemset)):
                for antecedent in combinations(itemset, antecedent_size):
                    antecedent_set = frozenset(antecedent)
                    consequent_set = itemset - antecedent_set

                    # Get support values
                    antecedent_support = self.itemsets.get(antecedent_set, 0)
                    itemset_support = support

                    if antecedent_support > 0:
                        confidence = itemset_support / antecedent_support
                        if confidence >= self.min_confidence:
                            rules[(antecedent_set, consequent_set)] = confidence

        return rules

    def get_recommendations(self, base_items: List[str], top_k: int = 5) -> List[Dict]:
        """
        Get recommended add-ons for given base items.

        Args:
            base_items: List of ingredient/product names.
            top_k: Number of recommendations to return.

        Returns:
            List of recommendation dicts with 'item', 'confidence', 'support'.
        """
        recommendations = defaultdict(float)
        base_set = frozenset(base_items)

        for (antecedent, consequent), confidence in self.rules.items():
            # Check if antecedent matches any base item
            if antecedent.issubset(base_set):
                # Add consequent items to recommendations
                for item in consequent:
                    if item not in base_items:
                        # Use confidence as score
                        recommendations[item] = max(
                            recommendations[item],
                            confidence
                        )

        # Sort by confidence and return top k
        sorted_recs = sorted(
            recommendations.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]

        return [
            {
                "item": item,
                "confidence": confidence,
                "support": self.itemsets.get(frozenset([item]), 0)
            }
            for item, confidence in sorted_recs
        ]

    def get_combinations(self, base_item: str, top_k: int = 10) -> List[Dict]:
        """
        Get frequently paired items with a base ingredient.

        Args:
            base_item: Single ingredient/product name.
            top_k: Number of combinations to return.

        Returns:
            List of combination dicts.
        """
        return self.get_recommendations([base_item], top_k=top_k)

    def save_rules(self, filepath: Optional[str] = None):
        """
        Save learned rules to JSON file.

        Args:
            filepath: Path to save file (default: ml_rules.json).
        """
        if filepath is None:
            filepath = self.rules_file

        # Convert frozensets to lists for JSON serialization
        rules_dict = {}
        for (antecedent, consequent), confidence in self.rules.items():
            key = f"{sorted(list(antecedent))} -> {sorted(list(consequent))}"
            rules_dict[key] = confidence

        itemsets_dict = {}
        for itemset, support in self.itemsets.items():
            key = ",".join(sorted(list(itemset)))
            itemsets_dict[key] = support

        data = {
            "min_support": self.min_support,
            "min_confidence": self.min_confidence,
            "itemsets": itemsets_dict,
            "rules": rules_dict,
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving rules: {e}")
            return False

    def load_rules(self, filepath: Optional[str] = None):
        """
        Load learned rules from JSON file.

        Args:
            filepath: Path to load file (default: ml_rules.json).

        Returns:
            True if successful, False otherwise.
        """
        if filepath is None:
            filepath = self.rules_file

        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.min_support = data.get("min_support", self.min_support)
            self.min_confidence = data.get("min_confidence", self.min_confidence)

            # Rebuild itemsets
            self.itemsets = {}
            for key, support in data.get("itemsets", {}).items():
                items = key.split(",")
                self.itemsets[frozenset(items)] = support

            # Rebuild rules
            self.rules = {}
            for rule_str, confidence in data.get("rules", {}).items():
                # Parse rule string: "[item1, item2] -> [item3, item4]"
                parts = rule_str.split(" -> ")
                if len(parts) == 2:
                    antecedent_str = parts[0].strip("[]").replace("'", "").split(", ")
                    consequent_str = parts[1].strip("[]").replace("'", "").split(", ")
                    antecedent = frozenset(antecedent_str)
                    consequent = frozenset(consequent_str)
                    self.rules[(antecedent, consequent)] = confidence

            return True
        except Exception as e:
            print(f"Error loading rules: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get statistics about the learned model."""
        return {
            "num_transactions": len(self.transactions),
            "num_itemsets": len(self.itemsets),
            "num_rules": len(self.rules),
            "min_support": self.min_support,
            "min_confidence": self.min_confidence,
        }

    def clear(self):
        """Clear all learned data."""
        self.transactions.clear()
        self.itemsets.clear()
        self.rules.clear()


class SimpleRecommender:
    """
    Lightweight recommender using co-occurrence frequencies.
    
    Faster than Apriori, good for real-time recommendations.
    """

    def __init__(self):
        """Initialize simple recommender."""
        self.cooccurrence = defaultdict(lambda: defaultdict(int))
        self.item_frequency = defaultdict(int)
        self.total_transactions = 0

    def add_transaction(self, items: List[str]):
        """Add a transaction."""
        if len(items) < 2:
            return

        self.total_transactions += 1
        unique_items = list(set(items))

        # Update frequencies
        for item in unique_items:
            self.item_frequency[item] += 1

        # Update co-occurrence
        for i, item1 in enumerate(unique_items):
            for item2 in unique_items[i + 1:]:
                self.cooccurrence[item1][item2] += 1
                self.cooccurrence[item2][item1] += 1

    def get_recommendations(self, base_item: str, top_k: int = 5) -> List[Dict]:
        """
        Get recommendations for a base item.

        Args:
            base_item: Item name.
            top_k: Number of recommendations.

        Returns:
            List of recommendation dicts.
        """
        if base_item not in self.cooccurrence:
            return []

        # Get co-occurrence counts
        cooccurs = self.cooccurrence[base_item]

        # Calculate confidence: P(item2 | base_item)
        base_frequency = self.item_frequency.get(base_item, 1)
        recommendations = [
            {
                "item": item,
                "confidence": count / base_frequency,
                "support": count / max(self.total_transactions, 1),
            }
            for item, count in cooccurs.items()
        ]

        # Sort by confidence
        recommendations.sort(key=lambda x: x["confidence"], reverse=True)
        return recommendations[:top_k]

    def save(self, filepath: str):
        """Save model to JSON."""
        data = {
            "cooccurrence": {
                item: dict(counts)
                for item, counts in self.cooccurrence.items()
            },
            "item_frequency": dict(self.item_frequency),
            "total_transactions": self.total_transactions,
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving model: {e}")
            return False

    def load(self, filepath: str) -> bool:
        """Load model from JSON."""
        if not os.path.exists(filepath):
            return False

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.cooccurrence = defaultdict(
                lambda: defaultdict(int),
                {
                    item: defaultdict(int, counts)
                    for item, counts in data.get("cooccurrence", {}).items()
                }
            )
            self.item_frequency = defaultdict(
                int,
                data.get("item_frequency", {})
            )
            self.total_transactions = data.get("total_transactions", 0)
            return True
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
