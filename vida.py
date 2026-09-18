import sys

def main():
    path = sys.argv[1]
    generations = int(sys.argv[2])

    with open(path, newline='') as f:
        data = f.read()

    if generations == 0:
        sys.stdout.write(data)
        return

    lines = data.splitlines()
    height = len(lines)
    width = len(lines[0]) if height else 0

    live = {
        (r, c)
        for r, line in enumerate(lines)
        for c, ch in enumerate(line)
        if ch == '#'
    }

    for _ in range(generations):
        counts = {}

        for r, c in live:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr = r + dr
                    nc = c + dc
                    if 0 <= nr < height and 0 <= nc < width:
                        key = (nr, nc)
                        counts[key] = counts.get(key, 0) + 1

        next_live = set()

        for cell in live:
            cnt = counts.get(cell, 0)
            if cnt == 2 or cnt == 3:
                next_live.add(cell)

        for cell, cnt in counts.items():
            if cnt == 3 and cell not in live:
                next_live.add(cell)

        if next_live == live:
            break

        live = next_live

    out_lines = [
        ''.join('#' if (r, c) in live else '.' for c in range(width))
        for r in range(height)
    ]

    out = '\n'.join(out_lines)
    if data.endswith('\n'):
        out += '\n'

    sys.stdout.write(out)

if __name__ == '__main__':
    main()
