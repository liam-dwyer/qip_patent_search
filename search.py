from flask import Flask, request, render_template, redirect, url_for, make_response, Response, send_from_directory, abort, send_file #importing flask dependencies
import os.path, os, shutil, requests, csv, re, json 
import numpy as np
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__) #initializing flask app

@app.route('/', methods=["POST", "GET"]) #declaring home page url and template
def home():
    return render_template("PATENT_FORM.html")


@app.route('/PATENT_FORM/', methods=["POST", "GET"]) #declaring url for patent form and methods used
def url():
    if request.method == "POST":
        data_entry = request.form["data_entry"]
        return redirect(url_for("assignor_search", data_entry=data_entry)) #if the method is posted, return the form data and pass to assignor search function
    else:
        print(app.config)
        return render_template("PATENT_FORM.html") #if the method is gotten, return the patent form template again

#####################################################################################
############# PARSING DATA FROM TEXT INPUT / CSV UPLOAD #############################
#####################################################################################


#####################################################################################
############################## SEARCH ENGINE ########################################
@app.route('/assignor_search/<data_entry>')                                         # setting the assignor search function url and <data_entry> filename to pass number information
def assignor_search(data_entry):                                                    #
                                                                                    #
    def input_parser(data_entry):  # returns US_nums and EU_nums                    #
        # nums is the array of split apart patent number entries
        nums = re.split(r'[:,\s]\s*', data_entry) #parses the number entries and separates via the delimiters
        US_nums = []
        EU_nums = []
        for i in range(len(nums)):
            if 'US' in nums[i]:
                US_nums.append(nums[i]) #creates array of US patent numbers
            elif 'EP' in nums[i]:
                EU_nums.append(nums[i]) #creates array of EU patent numbers
            else:
                pass # if neither US or EU patent, doesn't add to array
        return US_nums, EU_nums
    ########################## DEFINING NECESSARY SEARCHING FUNCTIONS ###############
    ############################# US PATENT OFFICE ##################################
    def find_all(a_str, sub):                                                       # function that finds start indexes for all "sub" strings in dataset
        start = 0
        while True:
            start = a_str.find(sub, start)
            if start == -1:
                return
            yield start
            start += len(sub)  # use start += 1 to find overlapping matches
                                                                                    #
    def url_search_us(US_nums):  # returns url_array and US_nums                    #
        url1 = "https://assignment-api.uspto.gov/patent/lookup?query="
        url2 = "&filter=PatentNumber"
        url_array = []
        str2 = ""
        for i in range(len(US_nums)):
            if i == 0:
                US_nums_fix = US_nums[i].replace("[","") #correcting number data to not include list syntax for search
                US_nums_fix = US_nums[i].replace("]","")
                US_nums[i] = US_nums_fix
                pat_no_US = US_nums[i].replace("US","") #removing the "US" tag from the patent numbers for search
                url = url1 + pat_no_US + url2
                url = url.replace("'","") #removing any incorrect syntax from the url
                url = url.replace("[","")
                url = url.replace("]","")
                url = url.replace("[","")
                string = str2.join(url) 
                url_array.append(string) #creating array of US urls
            else:
                pat_no_US = US_nums[i].replace("US","")
                url = url1 + pat_no_US + url2
                url = url.replace("'","")
                url = url.replace("[","")
                url = url.replace("]","")
                url = url.replace("[","")
                string = str2.join(url)
                url_array.append(string)
        return url_array, US_nums #returns US patent numbers and urls
                                                                                    #
    def SearchFunc(data, search_start, search_end, f_shift, b_shift, f_shift2, b_shift2, search_par):  # search function for US patent numbers in USPTO database

        # determining the start index values of all the strings searched for
        idx_start = list(find_all(data, search_start)) #the index to begin searching database at
        # determining the end index values of all the strings searched for
        idx_end = list(find_all(data, search_end)) #the index to stop searching database at
        VAL = []  # final values array
        VAL_return = []  # working values array
        i_range = 0
        if len(idx_start) > len(idx_end):
            i_range = len(idx_end)
        if len(idx_end) >= len(idx_start):
            i_range = len(idx_start)
        for i in range(i_range):
            A = idx_start[i]
            B = idx_end[i]
            VAL.append(data[(A+f_shift):(B-b_shift)])
            VAL_str = str(VAL[i])
            str1 = ""
            if (VAL_str.find(search_par) != -1):
                indx = list(find_all(VAL_str, search_par))
                for k in range(len(indx)):
                    if k == 0:
                        VAL_return = VAL_str[0:indx[k]-b_shift2]
                        VAL_return = VAL_return + str('; ')
                        VAL_return = VAL_return + \
                            VAL_str[(indx[k]+f_shift2):(indx[k+1]-b_shift2)]
                        VAL_return = VAL_return + str('; ')
                    if k == (len(indx)-1):
                        VAL_return = VAL_return + \
                            VAL_str[(indx[k]+f_shift2):len(VAL_str)]
                        break
                    elif (0 < k < (len(indx)-1)):
                        VAL_return = VAL_return + \
                            VAL_str[(indx[k]+f_shift2):(indx[k+1]-b_shift2)]
                String = str1.join(VAL_return)
                VAL[i] = String
        return VAL
                                                                                    #
    def SearchFuncDate(data, search_start, f_shift):  # returns VAL                 #

        # determining the start index values of all the strings searched for
        idx_start = list(find_all(data, search_start))
        VAL = []  # final values array
        VAL_return = []  # working values array
        for i in range(len(idx_start)):
            A = idx_start[i]
            VAL.append(data[(A+f_shift):(A+f_shift+10)])
        return VAL
                                                                                    #
    def patentAssignmentsUS(US_nums):  # returns data, num, and patent_tuple        #
        URLS, num = url_search_us(US_nums)
        patent_tuple = []
        for i in range(len(URLS)):
            response = requests.get(URLS[i]) #api to return assignor patent legal information
            data = response.text
            Assignors = SearchFunc(
                data, '"patAssignorName"', '<arr name="patAssignorExDate"', 30, 22, 17, 1, '/str') #search criteria for assignors
            Assignees = SearchFunc(
                data, '"patAssigneeName"', '<arr name="patAssigneeAddress1"', 30, 22, 17, 1, '/str') #search criteria for assignees
            Recorded = SearchFuncDate(data, '<date name="recordedDate">', 26) #search criteria for date
            patent_tuple.append((Assignors, Assignees, Recorded))
        data = []
        for i in range(len(num)):  #creating data array with returned data formatted correctly
            patent_stack = np.vstack(patent_tuple[i])
            for k in range(len(patent_stack[1])):
                if k == 0:
                    num[i] = num[i].replace("'","")
                    num[i] = num[i].replace("[","")
                    num[i] = num[i].replace("]","")
                    data.append((num[i], patent_stack[2, k],
                                patent_stack[0, k], patent_stack[1, k]))
                else:
                    data.append(
                        (None, patent_stack[2, k], patent_stack[0, k], patent_stack[1, k]))
        return patent_tuple, num, data
                                                                                    #
    ############################ EU PATENT OFFICE ###################################
                                                                                    #
    def url_search_eu(EU_nums):#returns url_array and EU_nums                       # creating urls for EU patent numbers
        url1 = "http://ops.epo.org/3.2/rest-services/family/publication/docdb/"
        url2 = "/legal"
        url_array = []
        str2 = ""
        for i in range(len(EU_nums)):
            EU_nums_fix = EU_nums[i].replace("[","")
            EU_nums_fix = EU_nums[i].replace("]","")
            EU_nums[i] = EU_nums_fix
            url = url1 + EU_nums[i] + url2
            url = url.replace("'","")
            string = str2.join(url)
            url_array.append(string)
        return url_array, EU_nums
    def authentification_eu(): #authentification for use of EPO database
        token_url = "https://ops.epo.org/3.2/auth/accesstoken"
        headers = {"Authorization": "Basic NHhFNmdCaElURFFiYVhHSGwzRlFHTDZsOGUzZVNBRTQ6elg5YkZyeW9ZallPQ2xDbg==",
               "Content-Type": "application/x-www-form-urlencoded"}
        payload = {'grant_type': 'client_credentials'}

        auth = requests.post(token_url, data=payload, headers=headers)
        auth = auth.text

        access_token = str(auth[329:357])
        bearer = "Bearer " + access_token
        headers_data = {"Authorization": bearer}
        return headers_data                                                                                # returning the needed html headers to access database
    def patentAssignmentsEU(EU_nums,headers_data): #returns patent_tuple, num, and data
        URLS, num = url_search_eu(EU_nums)


        #declaring the necessary arrays
        Assignor = []
        Assignee = []
        Date = []
        patent_tuple = []
        for i in range(len(URLS)):
            url = str(URLS[i])
            response = requests.get(url=url,headers=headers_data)
            data = response.text
            ass_indx = list(find_all(data,'"CHANGE OF APPLICANT/PATENTEE"'))
            if (data.find('"CHANGE OF APPLICANT/PATENTEE"',0)==-1): #if no assignor data found for the patent, return the current owner
                #data = 'This patent has no assignment changes'

                current_owner_start_idx = data.find('"OWNER">',0)
                current_owner_start = current_owner_start_idx + 8
                current_owner_end = data.find('</ops:',current_owner_start_idx)
                date_start = data.find('"DATE last exchanged"',(current_owner_start_idx - 200)) + 22
                date_end = date_start + 10
                patent_tuple.append((data[current_owner_start:current_owner_end],"",data[date_start:date_end]))

                continue
            for i in range(len(ass_indx)): #if there is change of assingor information
                owner_start = data.find('"OWNER"',ass_indx[i]) + 8
                owner_end = data.find('</ops:',owner_start)

                former_owner_start = data.find('"Free Format Text"',ass_indx[i]) + 33
                former_owner_end = data.find('</ops:',former_owner_start)

                date_start = data.find('"Effective DATE"',ass_indx[i]) + 17
                Date_formatted = data[date_start:(date_start+4)] + '-' + data[(date_start+4):(date_start+6)] + '-' + data[(date_sta>
                if Date_formatted in Date:
                    continue
                Assignor.append(data[former_owner_start:former_owner_end])
                Assignee.append(data[owner_start:owner_end])
                Date.append(Date_formatted)
            patent_tuple.append((Assignor,Assignee,Date)) #creating patent tuple for returned information
        data = []
        for i in range(len(num)):
            patent_stack = np.vstack(patent_tuple[i])
            for k in range(len(patent_stack[1])):
                if k == 0:
                    num[i] = num[i].replace("'","")
                    data.append((num[i],patent_stack[2,k],patent_stack[0,k],patent_stack[1,k]))
                else:
                    data.append((None,patent_stack[2,k],patent_stack[0,k],patent_stack[1,k]))
        return patent_tuple, num, data #returning data array with properly arranged returned data
    class NpEncoder(json.JSONEncoder):                                              #
        def default(self, obj):
            if isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return super(NpEncoder, self).default(obj)
    ############################ APPLYING DEFINED FUNCTIONS##########################
    US_nums, EU_nums = input_parser(data_entry)
    headers_data = authentification_eu()
    #headers_data = eu_authentification()                                           #
    patent_tuple_US, US_num, data_US = patentAssignmentsUS(US_nums)                 #
    patent_tuple_EU, EU_num, data_EU = patentAssignmentsEU(EU_nums,headers_data)    #
    ################## COMBINING TUPLES AND NUMBER ARRAYS FOR CSV ###################
    patent_tuple = patent_tuple_US + patent_tuple_EU                                #
    num = US_num + EU_num                                                           #
    data = data_US + data_EU                                                        #
    ######################### CREATING PATH DIRECTORY ###############################
    dir_path = 'client/csv'                                                         #
    if not os.path.isdir(dir_path):                                                 #
        os.makedirs(dir_path)                                                       #
    ############################ WRITING CSV FILE ###################################
    name_of_file = 'assignor_data'
    with open('{file_path}.csv'.format(file_path=os.path.join(dir_path, name_of_file)),'w') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Patent Number","Date","Assignor","Assignee"])
            for i in range(len(data)):
                writer.writerow(data[i])
            csv_file.close()
    data_json = json.dumps(data, cls=NpEncoder)
    return render_template("table_display.html",data=data_json,patent_tuple=patent_tuple)
#####################################################################################
#####################################################################################


#####################################################################################
########################### CSV UPLOAD AND DOWNLOAD #################################
app.config["CSV_UPLOADS"] = "/root/APP/client/csv" #the csv folder route created serverside for CSV file uploads
app.config["ALLOWED_DATA_EXTENSIONS"] = ["CSV","XLXS","TXT"]                        #
@app.route('/csv_upload',methods=["GET","POST"])                                    #
def csv_upload():                                                                   #
    def allowed_data(filename):
        if not "." in filename:
            return False

        ext = filename.rsplit(".",1)[1]

        if ext.upper() in app.config["ALLOWED_DATA_EXTENSIONS"]:
            return True
        else:
            return False
    if request.method =="POST":
        if request.files:

            csv = request.files["csv"]
            if csv.filename =="":
                print("CSV must have a filename")
                return redirect(request.url)
            if not allowed_data(csv.filename):
                print("That file extension is not allowed")
                return redirect(request.url)
            else:
                filename = secure_filename(csv.filename)
            csv.save(os.path.join(app.config["CSV_UPLOADS"],filename))
            print("CSV saved")
        path = app.config["CSV_UPLOADS"] + '/' + filename
        num_dat = pd.read_csv(path, header=None)
        data_entry = num_dat.values[:, 0]
    print(data_entry)
    return redirect(url_for("assignor_search", data_entry=data_entry))

@app.route('/download/<path:filename>',methods=["GET","POST"])

def download_csv(filename):
    downloads = app.config["CSV_UPLOADS"]
    #downloads = os.path.join(app.root_path,app.config['CSV_FOLDER'])
    return send_from_directory(directory=downloads,path=filename,as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')

