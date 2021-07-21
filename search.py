from flask import Flask, request, render_template, redirect, url_for, make_response, Response, send_from_directory, abort, send_file
import os.path, os, shutil, requests, csv, re, json
import numpy as np
import pandas as pd
from werkzeug.utils import secure_filename

app = Flask(__name__)

@app.route('/index')
def index():
    return render_template("index.html")

@app.route('/', methods=["POST", "GET"])
def home():
    return render_template("PATENT_FORM.html")


@app.route('/PATENT_FORM/', methods=["POST", "GET"])
def url():
    if request.method == "POST":
        data_entry = request.form["data_entry"]
        return redirect(url_for("assignor_search", data_entry=data_entry))
    else:
        print(app.config)
        return render_template("PATENT_FORM.html")

#####################################################################################
############################## SEARCH ENGINE ########################################
@app.route('/assignor_search/<data_entry>')                                         #
def assignor_search(data_entry):                                                    #
                                                                                    #
    def input_parser(data_entry):  # returns US_nums and EU_nums                    #
        # nums is the array of split apart patent number entries
        nums = re.split(r'[:,\s]\s*', data_entry)
        Pat_nums = []
        for i in range(len(nums)):
            Pat_nums.append(nums[i])
        nums = Pat_nums
        return nums
    ########################## DEFINING NECESSARY SEARCHING FUNCTIONS ###############
    def find_all(a_str, sub):                                                       #
        start = 0
        while True:
            start = a_str.find(sub, start)
            if start == -1:
                return
            yield start
            start += len(sub)  # use start += 1 to find overlapping matches
    def url_search(nums):#returns url_array and EU_nums                       #
        url1 = "http://ops.epo.org/3.2/rest-services/family/publication/docdb/"
        url2 = "/legal"
        url_array = []
        str2 = ""
        for i in range(len(nums)):
            nums_fix = nums[i].replace("[","")
            nums_fix = nums[i].replace("]","")
            nums_fix = nums[i].upper()
            nums[i] = nums_fix
            nums[i] = nums[i].replace("[","")
            nums[i] = nums[i].replace("]","")
            url = url1 + nums[i] + url2
            url = url.replace("'","")
            url = url.replace("[","")
            url = url.replace("]","")
            string = str2.join(url)
            url_array.append(string)
        return url_array, nums

    def authentification():
        token_url = "https://ops.epo.org/3.2/auth/accesstoken"
        headers = {"Authorization": "Basic NHhFNmdCaElURFFiYVhHSGwzRlFHTDZsOGUzZVNBRTQ6elg5YkZyeW9ZallPQ2xDbg==",
               "Content-Type": "application/x-www-form-urlencoded"}
        payload = {'grant_type': 'client_credentials'}
        auth = requests.post(token_url, data=payload, headers=headers)
        auth = auth.text
        access_token = str(auth[329:357])
        bearer = "Bearer " + access_token
        headers_data = {"Authorization": bearer}
        return headers_data
                                                                                        #
    def patentAssignments(nums, headers_data): #returns patent_tuple, num, and data
        URLS, num = url_search(nums)
        #declaring the necessary arrays
        Assignor = []
        Assignee = []
        Date = []
        patent_tuple = []
        for i in range(len(URLS)):
            url = str(URLS[i])
            print(url)
            response = requests.get(url=url,headers=headers_data)
            data = response.text
            ass_indx = list(find_all(data,'desc="ASSIGNMENT"'))
            if (data.find('<code>SERVER.EntityNotFound</code>',0) != -1):
                patent_tuple.append(("This patent number returns no results.","",""))
                continue
            if (data.find('desc="ASSIGNMENT"',0)==-1):
                current_owner_start_idx = data.find('"OWNER">',0)
                current_owner_start = current_owner_start_idx + 8
                current_owner_end = data.find('</ops:',current_owner_start_idx)
                date_start = data.find('"DATE last exchanged"',(current_owner_start_idx - 200)) + 22
                date_end = date_start + 10
                patent_tuple.append((data[current_owner_start:current_owner_end],"",data[date_start:date_end]))
                continue
            for k in range(len(ass_indx)):
                owner_start = data.find('ASSIGNMENT OWNER',ass_indx[k]) + 17
                owner_end = data.find('</ops:',owner_start)
                owner = data[owner_start:owner_end]
                owner = owner.replace(";","; ")

                former_owner_start_1 = data.find('ASSIGNMENT Free Format Text',owner_end)
                former_owner_start = data.find(':',former_owner_start_1)+1
                former_owner_end = data.find(';REEL/FRAME',former_owner_start)
                former_owner = data[former_owner_start:former_owner_end]

                if 'SIGNING DATES' in former_owner:
                    sig_date_idx = former_owner.find('SIGNING DATES')
                    former_owner = former_owner[:(sig_date_idx-1)]
                former_owner = former_owner.replace(";","; ")

                date_start = data.find('ASSIGNMENT Effective DATE',former_owner_end) + 26
                Date_formatted = data[date_start:(date_start+4)] + '-' + data[(date_start+4):(date_start+6)] + '-' + data[(date_start+6):(date_start+8)]
                if (data.find('ASSIGNMENT Effective DATE',former_owner_end) == -1):
                    indx_start = data.find('desc="PARTY DATA CHANGED')
                    date_start = data.find('"Gazette DATE"',indx_start) + 15
                    Date_formatted= data[date_start:(date_start+10)]

                if (Date_formatted in Date) or (owner in Assignee) or (former_owner in Assignor):
                    continue
                for character in Date_formatted:
                    is_letter = character.isalpha()
                    if is_letter == 1:
                        continue

                Assignor.append(former_owner)
                Assignee.append(owner)
                Date.append(Date_formatted)
            patent_tuple.append((Assignor,Assignee,Date))
        data = []
        for i in range(len(num)):
            patent_stack = np.vstack(patent_tuple[i])
            for k in range(len(patent_stack[1])):
                if k == 0:
                    num[i] = num[i].replace("'","")
                    data.append((num[i],patent_stack[2,k],patent_stack[0,k],patent_stack[1,k]))
                else:
                    data.append((None,patent_stack[2,k],patent_stack[0,k],patent_stack[1,k]))
        return patent_tuple, num, data
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
    nums = input_parser(data_entry)
    headers_data = authentification()
    patent_tuple, num, data = patentAssignments(nums, headers_data)   #
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
########################### CSV UPLOAD AND DOWNLOAD #################################
app.config["CSV_UPLOADS"] = "/home/search/APP/client/csv/"
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
    return send_from_directory(directory=downloads,path=filename,as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')

