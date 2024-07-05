def nickname_from_email(user_model, user):
    potential_nickname = user.email.split('@')[0]
    potential_suffix = 1
    while user_model.objects.filter(profile__nickname=potential_nickname).exists():
        potential_nickname = f"{potential_nickname}_{potential_suffix}"
        potential_suffix += 1
    print(f"{potential_nickname=}")
    return potential_nickname