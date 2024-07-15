# Reddit
Reddit clone for educational purposes. Developed by PyMasters

- [Joining the project](#joining-the-project)
- [Rules of engagement](#rules-of-engagement)
   - [Rules](#rules)
   - [Code](#code)
   - [Testing](#testing)
      - [Writing own tests](#writing-own-tests)
- [How to Set up](#how-to-set-up)
   - [Connecting gmail to the application](#connecting-gmail-to-the-application)
- [Ruff formatting and linting](#ruff-formatting-and-linting)
- [Usage with Docker 🐳](#usage-with-docker-🐳)
- [In case of problems with starting the project](#in-case-of-problems-with-starting-the-project)


## Joining the project

Want to join and work on it? https://pymasters.pl/spolecznosc and fill the form from this message: https://discord.com/channels/1035267230901997628/1221772410701873293/1247199896834936842 

## Rules of engagement
Good reading on working with code changes and pull request is https://google.github.io/eng-practices/. It contains both views - change author and reviewer.

### Rules

1. We use ClickUp to manage tasks: https://app.clickup.com/9012000285/v/l/8cjgdgx-412
    - Kanban Board is used for ongoing work
    - Kanban Backlog is used to store ideas in form of tasks, for reviewing and moving to Kanban Board. 
    - Tasks must follow precise life cycle
        - when task is created in Kanban Backlog the status is "BACKLOG"
        - when task is created in Kanban Board, or moved to Kanban Board from Kanban Backlog, status is set to "TO DO". 
        - when work is started, task is moved into "IN PROGRESS", and stays in this state until **pull request is merged to dev**
        - after pull request is merged, status of the task is changed to "READY FOR QA"
        - after QA is done, the person who is performing QA is setting the task as "DONE". 
            - if issues are found the task is moved back to "TO DO" with comments or new task is created to address those issues.
2. Do not commit directly to `master` or `dev`. Both branches are protected.
3. Check your code with `ruff check` prior to creating pull requests. The code is checked against PEP8 using `ruff`. Violations will not allow merging.
    - fix can be applied by ruff automatically for some issues, check `ruff check --fix`.
4. Follow Git Flow approach while developing. 
   - video explaing git flow is available for Pymasters members at: https://discord.com/channels/1035267230901997628/1135149223306858536/1136744608555089990
       - you can join Pymasters at https://pymasters.pl/spolecznosc
   - Make changes and commit them. There should be only one reason to make a commit, eg. "Adding new fields to user model" should only contain changes related to those fields, nothing else. If there are other things - new commit is required.
   - Use pull request to add your work. Make pull request to `dev` branch.
   - After creating pull request use "reviewers" option on far right of the screen to request review from "pymasters/reddit" team, or you can request review from certain team member directly by mentioning their name.
      ![alt text](readme-image.png)
   - One of the team members (or multiple) will perform code review and approve the pull request or request changes.
      - If changes are requested, all comments have to be in constructive and friendly manner, as shown in https://google.github.io/eng-practices/review/reviewer/comments.html
   - It's a good thing to comment on the good parts of code with "Nice work" or something similar.
5. As this is a learning project, pair programming is most welcome. Jump on Zoom or google meet and work together: https://www.youtube.com/watch?v=wu6BOT-eMgc&t=105s&ab_channel=devmentor.pl
6. Code quality and automated tests will be run and required to pass before pull request can be merged. 
7. At least one approval by other team member is required before pull request can be merged.
8. After pull request is approved and code quality + tests are passed, pull request is merged by the author.
9. It is author responsibility to watch over pull request, bump if there is no code review done, fix issues and merge pull request.

### Code

- Use excellent Bootstrap framework for handling HTML pages https://getbootstrap.com/
- Use class based views instead of function based views. A lot of examples and reading can be found on Jacek Blog: https://akademiait.com.pl/ and youtube: https://www.youtube.com/watch?v=2S9-pvFBlBc&ab_channel=AkademiaIT
- for testing use pytest. Tests using Django Unit Testing will not be accepted. A lot of tests are in our previous project: https://github.com/pymasterspl/Dshop. Also please watch https://www.youtube.com/watch?v=xn3wSM82fnA&ab_channel=AkademiaIT
- If you have questions, just ask on discord, reddit channel.


### Testing

The project is using Pytest for automated testing. https://docs.pytest.org/

To run the tests first start project environment with:

```bash
poetry shell
```

Run tests in project directory with:

```bash
pytest
```

Make sure all tests pass before creating PR. Automated tests are run on every PR and if tests fail, merge will not be possible.

#### Writing own tests

This is most welcome. Test should be located in `tests` directory of a module (remember to add `__init__.py` file!). 
Test filename should follow pattern `test_{name}.py` where name is either functionality or, eg. "models", so `test_models.py`.
Each test in the file must start with `test_` prefix, otherwise Pytest will not find it. 

Test driven development is most welcome, check https://www.youtube.com/watch?v=xn3wSM82fnA. It is understandable that TDD itself 
is cumbersome, so writing the tests after the code is also OK. Practice, practice, practice. Review other tests, experiment, and if questions, ask. 


## How to Set up

Clone repository to specific folder (ex. reddit):
```
git clone https://github.com/pymasterspl/reddit.git
```
You need to have installed Poetry package. If you don't have, please install using this command:
```
pip install poetry
```
Navigate to reddit folder by command:
```
cd reddit
```
Set poetry global option, to use project folder as place to hold Virtual environment (recommended):
```
poetry config virtualenvs.in-project true
```
Install virtual environment, using current dependencies:
```
poetry install
```
Copy file env-template to .env file using command:
```
# linux/mac
cp env-template .env

# windows
copy env-template .env
```
Start poetry virtual environment
```
poetry shell
```

Update local .env file as needed

Create admin account to access admin site:

```
# linux/mac
# to apply db changes
./manage.py migrate 
./manage.py createsuperuser

# windows
# to apply db changes
python manage.py migrate
python manage.py createsuperuser
```


Run project:
```
# linux/mac
# to apply db changes
./manage.py migrate 
# to start project
./manage.py runserver

# windows
# to apply db changes
python manage.py migrate
# to start project
python manage.py runserver
```

Load data from fixtures:
```
python manage.py loaddata {fixture_name}.json
```

Open web browser and navigate to localhost address:  http://127.0.0.1:8000/ 

#### Connecting gmail to the application

To enable registration on the site, you must provide your e-mail data. There are two ways.

In the env file you need to set these fields
   ```
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.gmail.com'
   EMAIL_PORT = 587
   EMAIL_HOST_USER = 'your_name_email@gmail.com'
   EMAIL_USE_TLS = True
   ```

1. First possibility.

   You enter your account password.

   ```
     EMAIL_HOST_PASSWORD = 'your_password'
   ```
2.  Second possibility.

      You can generate a token for your account instead of entering your password.
   

   ```
  * The first thing you need to do is go to https://myaccount.google.com/security
  * Activate two-step verification via this link https://myaccount.google.com/signinoptions/twosv
  * Then we return to the website https://myaccount.google.com in the input we enter app passwords or in Polish version "hasła do aplikacji" ( it depends on the language setting on your account )
  * after entering a given view, you must enter the password from your Gmail, then enter the name of this code.
  * Gmail returns you a code that you enter into the env file (EMAIL_HOST_PASSWORD).
   ```

### Ruff formatting and linting

This is how we use linter:
```bash
ruff check                  # Lint all files in the current directory.
ruff check --fix            # Lint all files in the current directory, and fix any fixable errors.
ruff check --watch          # Lint all files in the current directory, and re-lint on change.
ruff check path/to/code/    # Lint all files in `path/to/code` (and any subdirectories).
```


This is how to use formatter:
```bash
ruff format                   # Format all files in the current directory.
ruff format path/to/code/     # Format all files in `path/to/code` (and any subdirectories).
ruff format path/to/file.py   # Format a single file.
ruff format --check           # Checks if formatting is proper and reports violations. Does not change files.
```

More at:
https://docs.astral.sh/ruff/linter/
https://docs.astral.sh/ruff/formatter/

### Usage with Docker 🐳
For setup and running with Docker, refer to the [Docker configuration instructions](DOCKER.md).

### In case of problems with starting the project:
1. Check the env-template file and update the local .env file if necessary
2. Run `poetry install`

