# Catalog
This project contains a web application for a catalog of categories with associated items

## Setting up server
### Set up new user with ssh logon permissions
On the server:
1. sudo apt-get update - goes through all repositories to get sources list
2. sudo apt-get upgrade - updates software from sources list
3. sudo apt-get autoremove - clean up unused packages
4. sudo apt-get install finger - a software that enables view of permissions/users
5. sudo adduser grader 
6. Setup grader with password "P@ssword1" and sudo access
7. sudo touch /etc/sudoers.d/grader - creates sudoers file for new user
8. sudo nano /etc/sudoers.d/grader - edit the new file to type in: "grader ALL=(ALL) NOPASSWD:ALL"
9. log out of box
In Local Machine:
10. In "/Users/<username>" directory, create a folder called ".ssh"
11. In the new ".ssh" folder, create an empty file called "graderKey"
12. ssh-keygen - starts command to generate key pair.  Save to "/Users/<username>/.ssh/graderKey"
13. generate without pass phrase for Project Submission
14. ssh grader@<box ip address> -p <ssh port> - ssh in with grader user
On the server:
15. mkdir .ssh - creates .ssh folder in grader user's home directory
11. touch .ssh/authorized_keys - In the new ".ssh" folder, create an empty file called "authorized_keys"
12. nano .ssh/authorized_keys - edit this file and paste in contents of graderKey.pub which was created from step 12
13. chmod 700 .ssh - restricts access to .ssh folder
14. chmod 644 .ssh/authorized_keys - sets permissions to key file
15. logout - exit server
In Local Machine:
16. ssh grader@<box ip address> -p <ssh port> -i ~/.ssh/graderKey - ssh in with grader user using generated keypair.
On the server:
17. sudo nano /etc/ssh/sshd_config - edit the ssh config file to turn off password authentications for all users.  Do this by setting the "Password Authentication" option to "no"
18. sudo service ssh restart - restart ssh service so all users are now forced to have a keypair.

### Set up firewall
On the server:
1. sudo ufw status - tell you if firewall is active or not.  If it is active, deactivate it first so can make changes without accidently restricting access with **sudo ufw disable**
2. sudo ufw default deny incoming
3. sudo ufw default allow outgoing
4. sudo ufw allow ssh
5. sudo ufw allow 2200/tcp
6. sudo ufw allow www
7. sudo ufw allow ntp
8. sudo ufw enable
In lightsale:
1.  configure ssh port to be 2200 instead of 22

### Install required software on Server
1. sudo apt-get install python3.6
2. sudo apt-get install python3-pip
3. sudo apt-get install apache2
4. sudo apt-get install libapache2-mod-wsgi-py3
5. sudo apt-get install postgresql
6. sudo apt-get install libpq-dev
7. sudo apt-get install git
8. git config --global user.name "Arks Edu"
9. git config --global user.email "arks.edu@gmail.com"
10. sudo pip3 install psycopg2
11. sudo pip3 install sqlalchemy
12. sudo pip3 install flask
13. sudo pip3 install httplib2
15. git clone https://github.com/google/oauth2client auth
16. sudo python3 auth/setup.py install
17. sudo pip3 install requests
18. sudo pip3 install oauth2client - double check to ensure have installed this
14. cd /var/www
19. git clone https://github.com/ArksEdu/Catalog

### Configure Postgres SQL
3. sudo su - postgres
4. **createuser --pwprompt** - create a user for postgres db called "admin", with password: "adminDB2018" - this should be a superuser with role to create db, and add more roles
5. **createdb -O admin catalog** - where admin is the user who will be owner of the db, and catalog refers to the name of the database to create
6. cd Catalog
7. python3 postgres-db-setup.py - creates tables in catalog database with admin user connection details
8. **createuser --pwprompt** - create a user for postgres db called "catalog", with password: "catalogDB1", who is NOT a superuser, and answer no to other questions.
9. **psql** - since we are currently signed in as postgres, this should run under postgres user
10. **GRANT CONNECT ON DATABASE catalog TO catalog;** 
11. **GRANT SELECT, UPDATE, INSERT, DELETE ON person TO catalog;** 
12. **GRANT SELECT, UPDATE, INSERT, DELETE ON category TO catalog;** 
13. **GRANT SELECT, UPDATE, INSERT, DELETE ON item TO catalog;** 

## Running the Catalog App
First, to set up vagrant, use the  vagrant file from Udacity fullstack-vm. This file will need to be put into the vagrant directory o your computer.

Download the project zip file into the vagrant directory. The zip should contain a single folder: "catalog". This folder will have all the files associated with the project. Unzip the project zip file in the vagrant directory. 

Startup the vagrant virtual machine with **vagrant up**

Once it is up and running, type **vagrant ssh**. This will log your terminal into the virtual machine, and you'll get a Linux shell prompt. When you want to log out, type **exit** at the shell prompt.  To turn the virtual machine off (without deleting anything), type **vagrant halt**. If you do this, you'll need to run **vagrant up** again before you can log into it.

Now that you have Vagrant up and running type **vagrant ssh** to log into your VM.  change to the /vagrant/catalog directory by typing **cd /vagrant/catalog**. This will take you to the shared folder between your virtual machine and host machine.

Type **ls** to ensure that you are inside the directory that contains application.py, database_setup.py, catalog.db, client_secrets.json and two directories named 'templates' and 'static'

Now type **python3 postgres_db_setup.py** to initialize the database.

Type **python3 catalog.py** to run the Flask web server. In your browser visit **http://localhost:5000** to view the catalog app.  You should be able to view, add, edit, and delete items and categories.

Some json endpoints are also provided with this project.  The main one is catalog.json, which can be found at the root.  This file returns the list of Categories and their related Items in the following format:
    1. Level 1 - Category
    2. Within Category the following attributes:
        - Item - which is a list of the related Items for the Category
        - id - the primary identifier of the Category
        - name - the name of the Category
    3. For each Item within a Category, the following details are provided:
        - cat_id - the identifier of the parent category
        - description - a description of the Item in the Category
        - id - the primary identifier of the Item
        - title - the title of the Item as shown in the Category Item list page

Other available endpoints are:
- category<cat_id>.json
- item<item_id>.json
These show the details of the selected category/item based on the Id of the record.