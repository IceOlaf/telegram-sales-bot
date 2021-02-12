async def set_state_active(state):
    async with state.proxy() as data:
        data["state_active"] = await state.get_state()


def checkID(mes):
    try:
        return int(mes.split(' ')[1])
    except:
        return -1


def check_first_tag(mes):
    try:
        return mes.split(' ')[1].split('@')[1]
    except:
        return "None"


def check_all_tag(mes):
    try:
        out = []
        tags = mes.split(' ')
        del tags[0]
        for tag in tags:
            if "@" == tag[0]:
                out.append(tag.split('@')[1])
            else:
                break
        return out
    except:
        return []


def check_text(mes):
    try:
        return mes.split("\"")[1]
    except:
        return ""


def check_number(mes):
    try:
        substrings = mes.split(" ")
        for word in substrings:
            if word.isdigit():
                return int(word)
        return None
    except:
        return None