from . import store


def update(stats):
    if type(stats) is str:
        if stats[:-4] == "xlsx":
            return store.update_xlsx(stats)
        if stats[:-4] == "csv":
            return store.update(csv = stats)
    if type(stats) is dict:
        return store.update(players=stats['players'], teams=stats['teams'])


def clear():
    return store.clear()


def dump():
    return store.dump()
