import pycountry

MALE = "M"
FEMALE = "F"
NON_BINARY = "B"
OTHER = "O"
NON_SPECIFIED = "N"

GENDER_CHOICES = [
    (MALE, "Male"),
    (FEMALE, "Female"),
    (NON_BINARY, "Non-binary"),
    (OTHER, "Other"),
    (NON_SPECIFIED, "Non-specified"),
]

# https://pypi.org/project/pycountry/


# https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
def get_locations() -> list[tuple[str, str]]:
    return [(location.alpha_2, location.name) for location in pycountry.countries]


# https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes
LANGUAGE_CHOICES = [("en", "English")]
