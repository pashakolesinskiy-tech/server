import random
import string


def generate_code():

    return "HODOS" + "".join(

        random.choices(
            string.ascii_uppercase +
            string.digits,
            k=6
        )

    )
