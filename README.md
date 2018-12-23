# Catalog
This project contains a web application for a catalog of categories with associated items

## Running the Catalog App
Type http://54.206.103.213.xip.io in web browser

Some json endpoints are also provided with this project.  The main one is **catalog.json**, which can be found at the root.  This file returns the list of Categories and their related Items in the following format:
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
  
## Accessing the server  
Can ssh in with **ssh grader@54.206.103.213 -p 2200 -i ~/.ssh/graderKey** where graderKey is a file containing the following private key text included as the "Notes to Reviewer" in project submission

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
1. In "/Users/<username>" directory, create a folder called ".ssh"  
2. In the new ".ssh" folder, create an empty file called "graderKey"  
3.  ssh-keygen - starts command to generate key pair.  Save to "/Users/<username>/.ssh/graderKey"  
4.  generate without pass phrase for Project Submission  
5.  ssh grader@<box ip address> -p <ssh port> - ssh in with grader user     
  
On the server:
1. mkdir .ssh - creates .ssh folder in grader user's home directory  
2. touch .ssh/authorized_keys - In the new ".ssh" folder, create an empty file called "authorized_keys"  
3. nano .ssh/authorized_keys - edit this file and paste in contents of graderKey.pub which was created from step 12  
4. chmod 700 .ssh - restricts access to .ssh folder  
5. chmod 644 .ssh/authorized_keys - sets permissions to key file  
6. logout - exit server  
   
In Local Machine:  
1. ssh grader@<box ip address> -p <ssh port> -i ~/.ssh/graderKey - ssh in with grader user using generated keypair.  
  
On the server:  
1.   sudo nano /etc/ssh/sshd_config - edit the ssh config file to turn off password authentications for all users.  Do this by setting the "Password Authentication" option to "no"  
2.   sudo service ssh restart - restart ssh service so all users are now forced to have a keypair.  
  
### Set up firewall  
  
On the server:  
1. sudo nano /etc/ssh/sshd_config - edit to uncomment out "Port 22", and change to "Port 2200"  
2. sudo service ssh restart - restart ssh service so new ssh port takes effect  
3. sudo ufw status - tell you if firewall is active or not.  If it is active, deactivate it first so can make changes without accidently restricting access with sudo ufw disable  
4. sudo ufw default deny incoming  
5. sudo ufw default allow outgoing  
6. sudo ufw allow ssh  
7. sudo ufw allow 2200/tcp  
8. sudo ufw allow www  
9. sudo ufw allow ntp  
10. sudo ufw enable    
  
In lightsail:  
1. configure Custom port to be 2200  
2. Delete SSH Port (Port 22)  
  
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
11. sudo pip3 install psycopg2-binary  
12. sudo pip3 install sqlalchemy  
13. sudo pip3 install flask  
14. sudo pip3 install httplib2  
15. sudo pip3 install requests  
16. sudo pip3 install oauth2client - double check to ensure have installed this  
17. If Step 16 does not work:  
    1.  git clone https://github.com/google/oauth2client auth  
    2.  sudo python3 auth/setup.py install  
18. cd /var/www  
19. sudo git clone https://github.com/ArksEdu/Catalog  
  
### Configure Postgres SQL  
1. sudo su - postgres  
2. createuser admin --pwprompt - create a user for postgres db called "admin", with password: "adminDB2018" - this should be a superuser with role to create db, and add more roles  
3. createdb -O admin catalog - where admin is the user who will be owner of the db, and catalog refers to the name of the database to create  
4. exit - to return to grader user login.  
5. cd Catalog  
6. python3 postgres-db-setup.py - creates tables in catalog database with admin user connection details  
7. sudo su - postgres  
8. createuser catalog --pwprompt - create a user for postgres db called "catalog", with password: "catalogDB1", who is NOT a superuser, and answer no to other questions.  
9.  psql catalog - since we are currently signed in as postgres, this should run under postgres user  
10. GRANT CONNECT ON DATABASE catalog TO catalog;   
11. GRANT SELECT, UPDATE, INSERT, DELETE ON person TO catalog;  
12. GRANT SELECT, UPDATE, INSERT, DELETE ON category TO catalog;  
13. GRANT SELECT, UPDATE, INSERT, DELETE ON item TO catalog;   
14. GRANT USAGE, SELECT ON SEQUENCE person_id_seq TO catalog;  
15. GRANT USAGE, SELECT ON SEQUENCE category_id_seq TO catalog;  
16. GRANT USAGE, SELECT ON SEQUENCE item_id_seq TO catalog;  
  
### Configure Apache  
1. Update /etc/hosts file - add line for "54.206.103.213 ArksCatalog"  
2. cd /etc/apache2/sites-available  
3. sudo touch ArksCatalog.conf  
4. sudo nano ArksCatalog.conf  
5. Copy in following text and save the file:  
   ~~~~
   <virtualhost *:80>  
        ServerName ArksCatalog  
    
        WSGIDaemonProcess catalog user=www-data group=www-data threads=5 home=/var/www/Catalog/  
        WSGIScriptAlias / /var/www/Catalog/catalog.wsgi  
    
        <directory /var/www/Catalog>  
            WSGIProcessGroup catalog  
            WSGIApplicationGroup %{GLOBAL}  
            WSGIScriptReloading On  
            Order deny,allow  
            Allow from all  
        </directory>  

    </virtualhost>
    ~~~~
6. sudo a2dissite 000-default.conf - disables the default conf file from being the one used for apache  
7. sudo a2ensite ArksCatalog.conf - enables the ArksCatalog conf file as the default one for apache  
8. sudo apache2ctl restart - start apache  
9.  sudo service apache2 restart - restart serice also.  