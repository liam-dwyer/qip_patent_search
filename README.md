# qip_patent_search
Patent Legal Assignor Information to search USPTO and EPO databases

qip_patent_search uses flask website application and USPTO and EPO API's to search databases

##### EPO ##########
In order to access the EPO databases, the app has to be declared on the EPO website and have the application authenticated. When using the authentification_eu() function the unique APP id given by the EPO wesbite is inputted after "Basic".

The authentification_eu() function is called on each loop of the program to reauthenticate the request. 
#################### UPDATE ###############################
EPO database now searches with lowercase prefix and suffixes.

######## USPTO ##########

USPTO database does not search with the "US" prefix and therefore code to remove the prefix before assignining it to the URL was created. The USPTO search also does not support version suffix numbers (i.e., B1, A2, etc.) and therefore have to be removed before being typed into the website. 
#################### UPDATE ###############################
USPTO databse now does search with version suffix numbers as well as lowercase prefix / suffix


####### FLASK #######

Flask dependencies have to be installed in order for the python search engine to be client facing. In the app.config["CSV_UPLOADS"] line the path directory of where the csv files will be uploaded / saved has to be declared. This can be found by using the "pwd" command while in the desired folder in terminal. Paste this path directory in quotes after the app.config["CSV_UPLOADS"] line.
