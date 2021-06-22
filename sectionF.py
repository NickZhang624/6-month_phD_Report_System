@app.route("/section_F",methods = ["GET","POST"]) 
def section_F():
    # starting with False to make the switch
    token = False
    if request.method == "POST":
        print(request.form)
        # getting into the loop/ post loop
        token = True
        spvrname = request.form["spvrname"]
        sendto = request.form["sendto"]
        comment = request.form["comment"]
        conn = getConnection()
        cur = conn.cursor()
        cur.execute('select * from AssessmentByStudent')
        return render_template('sectionF.html', spvrname = spvrname, sendto = sendto, comment = comment)
    else:
        return render_template('sectionF.html')
    

    