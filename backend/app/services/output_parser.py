def parse_pipe_delimited(text: str) -> dict:
    """Parse Claude's pipe-delimited output.

    Record types:
        ENTITY|name|type|description
        REL|source|relation|target|timestamp
        SPEAKER|id|name|confidence
        FRAME|timestamp|reason
        TOPIC|name

    Rules:
        - One record per line
        - Fields separated by |
        - First field = record type
        - Lines starting with # = comments (ignored)
        - Empty fields allowed: TYPE|value||value
    """
    result = {
        "entities": [],
        "relationships": [],
        "speakers": {},
        "frames": [],
        "topics": []
    }

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split('|')
        record_type = parts[0]

        if record_type == 'ENTITY':
            result["entities"].append({
                "name": parts[1],
                "type": parts[2],
                "description": parts[3] if len(parts) > 3 else ""
            })
        elif record_type == 'REL':
            result["relationships"].append({
                "source": parts[1],
                "relation": parts[2],
                "target": parts[3],
                "timestamp": float(parts[4]) if len(parts) > 4 and parts[4] else None
            })
        elif record_type == 'SPEAKER':
            result["speakers"][parts[1]] = {
                "name": parts[2],
                "confidence": float(parts[3]) if len(parts) > 3 else 1.0
            }
        elif record_type == 'FRAME':
            result["frames"].append({
                "timestamp": float(parts[1]),
                "reason": parts[2] if len(parts) > 2 else ""
            })
        elif record_type == 'TOPIC':
            result["topics"].append(parts[1])

    return result
