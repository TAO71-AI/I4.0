zero: str = "zero"
one: str = "one"
two: str = "two"
three: str = "three"
four: str = "four"
five: str = "five"
six: str = "six"
seven: str = "seven"
eight: str = "eight"
nine: str = "nine"
dot: str = "dot"
separator_s: str = "["
separator_e: str = "]"
operators: dict = {
    "+": "plus",
    "-": "minus",
    "*": "multiplied",
    "/": "divided"
}
extra_numbers: dict = {}

def number_to_str(msg: str) -> str:
    global zero, one, two, three, four, five, six, seven, eight, nine, dot, operators, extra_numbers

    n: dict = {
        "0": zero,
        "1": one,
        "2": two,
        "3": three,
        "4": four,
        "5": five,
        "6": six,
        "7": seven,
        "8": eight,
        "9": nine,
        ".": dot,
        ",": dot,
    }

    for en in extra_numbers:
        n[str(en)] = str(extra_numbers[en])

    for op in operators:
        n[str(op)] = str(operators[op])

    for n2 in n:
        msg = msg.replace(n2, separator_s + n[n2] + separator_e)
    
    return msg