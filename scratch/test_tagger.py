from ai.tag_reviews import tag_review, tag_reviews_batch

def test_tagger():
    test_texts = [
        "The lyrics are completely out of sync on my phone, please fix this!",
        "Smart shuffle is absolute trash, it plays songs that are completely unrelated to my playlist.",
        "The app crashed three times today while playing local files. Highly unstable.",
        "General feedback: The streaming quality is great and I love the sound quality."
    ]

    print("--- Single Review Tagging Test ---")
    for txt in test_texts:
        print(f"\nText: \"{txt}\"")
        tags = tag_review(txt)
        print("Tags:", tags)

    print("\n--- Batch Tagging Test ---")
    mock_reviews = [
        {"id": "1", "source": "Play Store", "title": "Lyrics", "text": "Lyrics are broken", "url": "", "date": "", "author": "User A"},
        {"id": "2", "source": "Reddit", "title": "Smart shuffle", "text": "Smart shuffle is so annoying", "url": "", "date": "", "author": "User B"}
    ]
    results = tag_reviews_batch(mock_reviews)
    for r in results:
        print(f"\nReview: {r['text']}")
        print(f"Pain Point: {r.get('pain_point')}")
        print(f"Emotion: {r.get('emotion')}")

if __name__ == "__main__":
    test_tagger()
