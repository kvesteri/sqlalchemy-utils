def assert_contains(clause, query):
    # Test that query executes
    query.all()
    assert clause in str(query), f"[{clause}] is not in [{query}]"
