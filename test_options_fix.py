"""Test script to verify options are properly generated."""
import sys
sys.path.insert(0, 'f:/vocab-cat-test')

from irt_cat_engine.api.session_manager import session_manager
import random

# Wait for session manager to load
import time
print("Waiting for vocabulary data to load...")
max_wait = 30
waited = 0
while not session_manager.is_loaded and waited < max_wait:
    time.sleep(1)
    waited += 1

if not session_manager.is_loaded:
    print("ERROR: Vocabulary data failed to load!")
    sys.exit(1)

print(f"Loaded {len(session_manager._vocab)} vocabulary words")

# Test the fix
vocab_words = session_manager._vocab

# Filter for elementary words
elementary_levels = {"Elementary 3-4", "Elementary 5-6"}
elementary_words = [w for w in vocab_words if hasattr(w, 'kr_curriculum') and w.kr_curriculum in elementary_levels]

print(f"Found {len(elementary_words)} elementary words")

# Pick a random word
if elementary_words:
    word_data = random.choice(elementary_words)
    print(f"\nTesting with word: {word_data.word_display}")

    # Generate item
    item = session_manager._distractor_engine.generate_item(word_data, question_type=1)

    if item:
        print(f"Stem: {item.get('stem')}")
        print(f"Correct answer: {item.get('correct_answer')}")
        print(f"Distractors: {item.get('distractors')}")
        print(f"Options (before fix): {item.get('options')}")

        # Apply the fix
        if item and item.get("distractors"):
            options = [item["correct_answer"]] + item["distractors"]
            random.shuffle(options)
            print(f"Options (after fix): {options}")
        else:
            print("No distractors available!")
    else:
        print("Failed to generate item!")
