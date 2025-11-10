import random

eggs = {
    "NaCMan": ":rainbow[NaCMan] :dvd:",
    "nAcmAN": ":rainbow[nAcmAN] :dvd:",
    "nACMan": "n:blue[A]:yellow[C]:red[M]an :balloon:",
    "NacmAN": "N:blue[a]:yellow[c]:red[m]AN :balloon:",
}


def random_uppercase(text: str, probability: float = 0.5) -> str:
    return ''.join(char.upper() if random.random() < probability
                   else char for char in text)


def fancy_title(title: str) -> str:
    return "".join(
        f":{random.choice(["orange", "red", "blue", "green"])}[{char}]"
        if char.isupper() else char for char in title
    )


def emoji_number(num: int) -> str:
    digits = 'zero one two three four five six seven eight nine'.split()
    return ''.join(f":{digits[int(digit)]}:" for digit in str(num))
