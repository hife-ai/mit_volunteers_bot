def serialize(state: dict):
    values = [str(x) for x in state.values()]
    return ";".join(values)


def deserialize(state: str):
    return dict(zip(['cmd', 'username', 'role', 'subrole', 'date'], state.split(';')))