## Installation
1. Cloning the repository.
   ```
   git clone https://github.com/oatwarat/ku-polls.git
   ```
2. Access to the project directory.
   ```
   cd ku-polls
   ```
3. Create a Virtual Environment.
   ```
   python -m venv venv
   ```
4. Install dependencies.
   ```
   pip install -r requirements.txt
   ```
6. Set Up the Database.
   ```
   python manage.py migrate
   ```
7. Download data.
   ```
   python manage.py loaddata data/users.json
   python manage.py loaddata data/polls.json
   ```
8. Run the server.
   ```
   python manage.py runserver
   ```
