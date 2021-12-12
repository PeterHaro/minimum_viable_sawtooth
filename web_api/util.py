def __id_generator():
    uid = 0

    def getter():
        nonlocal uid
        uid += 1
        return uid

    return getter


id_generator = __id_generator()
