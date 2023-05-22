
# NUBIP Schedule

This repository contains the source code for NUBIP Schedule, an application designed to help students and teachers access and manage their class schedules at the National University of Life and Environmental Sciences of Ukraine (NUBIP). The application simplifies the process of checking class schedules by creating personal schedule events in user Google Calendar. To get all necessary information, app is using moodle database.

## Features

- **Schedule file parsing**: Retrieve faculty schedule for specific semester from excel file.
- **Administration**: Database data manipulations.
- **Google Calendar integration**: Update user Google Calendar with schedule events.

## Installation

To use NUBIP Schedule locally, follow these steps:

1. Create database:

If you don't have moodle database, install it foolowing [this](https://docs.moodle.org/401/en/Installation_quick_guide) guide.
Create "schedule" database near moodle401 and create a user with write and read access to schedule db and read access to moodle401 db.

2. Clone the repository and navigate to the project directory:

```bash
git clone https://github.com/volchey/NUBIP_schedule.git
cd NUBIP_schedule
```

3. Create virtual environment and install packages:

```bash
virtualenv env
source env/bin/activate
pip install -r requirements.txt
```

4. Create .env file with secret information like this:

```bash
DEBUG=off
SECRET_KEY=django-insecure-...

SCHEDULE_DB_HOST=127.0.0.1
SCHEDULE_DB_USER=root
SCHEDULE_DB_PASSWORD=root
SCHEDULE_DB_PORT=8889

MOODLE_DB_HOST=127.0.0.1
MOODLE_DB_USER=moodle
MOODLE_DB_PASSWORD=moodle
MOODLE_DB_PORT=8889
```

5. Make migrations and start django server:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

6. Create superuser to access administration page

```bash
python manage.py createsuperuser
```

7. Create and register Google project at [Google Cloud Console](https://console.cloud.google.com/)

- To create a project follow [this](https://developers.google.com/workspace/guides/create-project) guide.
- Go to administration page as a superuser and add a Site for your domain, matching settings.SITE_ID (django.contrib.sites app).
- For each OAuth based provider, add a SocialApp (socialaccount app) containing the required client credentials from Google Cloud Console.

## Contributing

Contributions are welcome! If you would like to contribute to this project, please follow these guidelines:

1. Fork the repository.
2. Create a new branch for your feature/bug fix.
3. Commit your changes and push the branch to your forked repository.
4. Submit a pull request detailing your changes.

Please ensure your code adheres to the project's coding standards and is well-documented.

## Acknowledgements

We would like to express our gratitude to the following resources and libraries that made this project possible:

- [Django](https://www.djangoproject.com/)
- [openpyxl](https://openpyxl.readthedocs.io/)
- [django-allauth](https://django-allauth.readthedocs.io/)
- [django-environ](https://django-environ.readthedocs.io/)
- [Google API Client](https://pypi.org/project/google-api-python-client/)
- [Moodle](https://docs.moodle.org/)

## Contact

For any questions or inquiries, please contact the project maintainer at [volchey07@gmail.com](mailto:volchey07@gmail.com).

Feel free to explore the repository and make any necessary modifications based on your specific project requirements.
