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


# https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
LOCATION_CHOICES = [("US", "United States")]
# https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes
LANGUAGE_CHOICES = [("en", "English")]
