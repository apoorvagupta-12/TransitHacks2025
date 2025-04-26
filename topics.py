import random

def normalize_topics(topics):
    """Lowercase and strip whitespace from topics."""
    return [topic.strip().lower() for topic in topics]

def jaccard_similarity(list1, list2):
    """Calculates Jaccard similarity between two lists."""
    set1 = set(normalize_topics(list1))
    set2 = set(normalize_topics(list2))
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    if not union:
        return 0
    return len(intersection) / len(union)

def find_best_match(new_user_topics, existing_users_topics):
    """Finds the best match for a new user based on topic similarity."""
    best_matches = []
    best_score = -1

    for user_id, topics in existing_users_topics.items():
        score = jaccard_similarity(new_user_topics, topics)
        if score > best_score:
            best_score = score
            best_matches = [user_id]
        elif score == best_score:
            best_matches.append(user_id)

    if best_matches:
        return random.choice(best_matches)
    else:
        return None