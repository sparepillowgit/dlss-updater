from collections import Counter


def format_version_summary(versions: list[str]) -> str:
    counts = Counter(versions)
    parts = []

    for version in sorted(counts.keys()):
        count = counts[version]

        if count == 1:
            parts.append(version)
        else:
            parts.append(f"{version} x{count}")

    return ", ".join(parts)