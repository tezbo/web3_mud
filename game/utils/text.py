"""
Text Utilities
"""

def number_to_words(n: int) -> str:
    """
    Convert a number to its word form (for small numbers).
    
    Args:
        n: Integer to convert
        
    Returns:
        str: Word representation (e.g., "one", "two") or string of number for larger values.
    """
    words = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
        11: "eleven",
        12: "twelve"
    }
    
    return words.get(n, str(n))

def format_item_list(items: list) -> str:
    """
    Format a list of items into a natural language string.
    Example: "Two lumps of ore, three meat pies and a small purse"
    """
    if not items:
        return ""
        
    # Import here to avoid circular dependency if Item is needed for type hinting
    # But we just need .name and .oid
    
    # Group items by name
    counts = {}
    for item in items:
        name = item.name
        counts[name] = counts.get(name, 0) + 1
        
    # Create list of strings
    parts = []
    from game.systems.inventory import pluralize_item_name
    
    for name, count in counts.items():
        if count > 1:
            plural = pluralize_item_name(name, count)
            count_str = number_to_words(count)
            parts.append(f"{count_str} {plural}")
        else:
            # Singular with article
            if name.lower().startswith(('a', 'e', 'i', 'o', 'u')):
                parts.append(f"an {name}")
            else:
                parts.append(f"a {name}")
                
    # Join with commas and 'and'
    if len(parts) == 1:
        return parts[0]
    elif len(parts) == 2:
        return f"{parts[0]} and {parts[1]}"
    else:
        return ", ".join(parts[:-1]) + f" and {parts[-1]}"
