# Catalog
This project contains a web application for a catalog of categories with associated items

## Running the Catalog App
First, to set up vagrant, use the  vagrant file from Udacity fullstack-vm. This file will need to be put into the vagrant directory o your computer.

Download the project zip file into the vagrant directory. The zip should contain a single folder: "catalog". This folder will have all the files associated with the project. Unzip the project zip file in the vagrant directory. 

Startup the vagrant virtual machine with **vagrant up**

Once it is up and running, type **vagrant ssh**. This will log your terminal into the virtual machine, and you'll get a Linux shell prompt. When you want to log out, type **exit** at the shell prompt.  To turn the virtual machine off (without deleting anything), type **vagrant halt**. If you do this, you'll need to run **vagrant up** again before you can log into it.

Now that you have Vagrant up and running type **vagrant ssh** to log into your VM.  change to the /vagrant/catalog directory by typing **cd /vagrant/catalog**. This will take you to the shared folder between your virtual machine and host machine.

Type **ls** to ensure that you are inside the directory that contains application.py, database_setup.py, catalog.db, client_secrets.json and two directories named 'templates' and 'static'

Now type **python database_setup.py** to initialize the database.

Type **python application.py** to run the Flask web server. In your browser visit **http://localhost:5000** to view the catalog app.  You should be able to view, add, edit, and delete items and categories.

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