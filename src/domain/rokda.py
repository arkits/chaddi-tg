def reward_rokda(r):
    if r is None or (r < 0):
        r = 0

    # Egalitarian policy - Poor users get more increment than richer users
    r += 100 / (r + 10) + 1
    r = round(r, 2)

    return r
