from don.fuzzy import best_match


def test_best_match_basic():
	choice, score = best_match("Ali", ["Ali", "Ahmad", "Alia"], 0.8)
	assert choice == "Ali"
	assert 0.99 <= score <= 1.0


def test_best_match_threshold_reject():
	choice, score = best_match("Ali", ["Bilal", "Zara"], 0.85)
	assert choice == ""
	assert score == 0.0
