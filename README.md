# ManagementApp - Flask

This is management system for administrator and client.

## Installation

Install python 3.6 https://www.python.org/downloads/release/python-365/.

- Install Database(Mysql or sqlite).

  Edit manage/__init__.py file 

- Mysql configuration : 

      app.config['SQLALCHEMY_DATABASE_URI'] ='mysql://root:''@localhost:3306/management'

- Sqlite configuration:

      app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///site.db'


- run server

```bash
venv/Scripts/activate
export FLASK_APP=hello.py
flask run --host=0.0.0.0 --port=80
```

- database migration

```bash
flak db init
flask db migrate
flask db upgrade
```

<<<<<<< HEAD
## Installation


```bash
venv/Scripts/activate
export FLASK_APP=hello.py
flask run --host=0.0.0.0 --port=80
```

=======
>>>>>>> 656e0791e4f00ab499cc3a0d86b64c5fa5b91caa
## User Levels

- Admin Portal

   Dashboard

   Client Management
  
   Service Management
  
   Admin Management

   History Page

   Default admin user -    email : admin@admin.com, password: admin 
<<<<<<< HEAD
=======
   
    ![image](https://user-images.githubusercontent.com/40516126/64921991-4938bf00-d797-11e9-8fb5-0803cca0bf90.png)

>>>>>>> 656e0791e4f00ab499cc3a0d86b64c5fa5b91caa


- Client Portal

  Dashboard

  Client Detail
   
  Reports

<<<<<<< HEAD
=======
   ![image](https://user-images.githubusercontent.com/40516126/64921880-35408d80-d796-11e9-8084-d57e4037617a.png)
>>>>>>> 656e0791e4f00ab499cc3a0d86b64c5fa5b91caa

## Other Configurations

Reference Documentation :

https://flask.palletsprojects.com/en/1.1.x/

