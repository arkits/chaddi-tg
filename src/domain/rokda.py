def reward_rokda(r: int):

    if (r < 0) or r is None:
        r = 0

    # Egalitarian policy - Poor users get more increment than richer users
    r += 100 / (r + 10) + 1
    r = round(r, 2)

    return r
