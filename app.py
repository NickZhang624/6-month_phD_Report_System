##########################################################################################
##########################################################################################
################################## COMP639 Project 2 #####################################
##########################  Lincoln Uni PG Reporting Portal  #############################
################################## Alex Xi: 1148465 ######################################
################################ John Yin ID: 1148333 ####################################
########################## Kaewkor Sucharitchan ID: 1148639 ##############################
########################## Maria Lucia del Campo ID: 1136441 #############################
############################### Nick Zhang ID: 1146778 ###################################
############################## Virgin Dabhi ID: 1148637 ##################################
##########################################################################################
##########################################################################################

from logging import debug, error
from flask import Flask, render_template, url_for, session, request, flash, redirect
import psycopg2, db_details
from werkzeug.datastructures import WWWAuthenticate
import uuid
from datetime import datetime, date, timedelta, time
import re
from types import MethodDescriptorType
from flask import Flask, render_template, request, redirect, url_for, session
import connect
import psycopg2
from functools import wraps
from section_d import SecD
# import yagmail
# import keyring
from types import MethodDescriptorType

##########################################################################################
##########################################################################################
################################## Global Functions ######################################
##########################################################################################
##########################################################################################

dbconn_2 = None
def getConnection():
    global dbconn_2
    if dbconn_2 == None:
        dbconn_2 = psycopg2.connect(dbname=db_details.dbname, user=db_details.dbuser,password=db_details.dbpass, host=db_details.dbhost, port=db_details.dbport)
        dbconn_2.autocommit = True
        return dbconn_2
    else:
        return dbconn_2

# Global variables
dbconn = None
app = Flask(__name__)

# Generate unique ids
def genID():
    return uuid.uuid4().fields[1]

# Get User Name
def user_name():
    cur = getCursor()
    if session['role'] == 'Student':
        cur.execute(f"SELECT CONCAT(firstname, ' ', lastname) FROM students WHERE userid = {session['id']}")
    else:
        cur.execute(f"SELECT CONCAT(firstname, ' ', lastname) FROM staff WHERE userid = {session['id']}")
    user_name = cur.fetchone()
    return user_name[0]

# Used for connecting to db
def getCursor():
    global dbconn
    if dbconn == None:
        conn = psycopg2.connect(dbname=connect.dbname, user=connect.dbuser, password=connect.dbpass, host=connect.dbhost, port=connect.dbport)
        conn.autocommit = True
        dbconn = conn.cursor()
        return dbconn
    else:
        return dbconn

app.secret_key = 'lincoln'


# Log in as a user
@app.route("/", methods=["POST", "GET"])
def login():
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cur = getCursor()
        cur.execute('SELECT userid, username, role \
            FROM login\
            WHERE UserName=%s AND Password=%s', 
            (username, password))
        account = cur.fetchone() #WILL NOT WORK IF THERE ARE DUPLICATE USERNAMES!
        print(account)
        if account:
            session['loggedin'] = True
            session['id'] = account[0]
            session['username'] = account[1]
            session['role'] = account[2]
            # Direct user to a landing page after logging in
            return login_triage()
        else:   
            msg = 'You have entered incorrect username/password!'
            return render_template('message.html', msg=msg)
    else:
        if 'loggedin' in session:
            return login_triage()
        else:
            return render_template('home.html')

# Divert users to landing page based on role
def login_triage():
    cur = getCursor()
    if session['role'] == 'Student':
        return redirect('/student')
        #return redirect('/section_a/edit?report=1&student=19')
    else:
        cur.execute(f"SELECT position FROM staff\
            WHERE userid={session['id']} \
            AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate")
        result = cur.fetchone()
        session['role'] = result[0] #Assign position of staff as their session role
        if session['role'] == 'Professor':
            return redirect('/supervisor/pending&report?view=pending')
        elif session['role'] == 'Admin':
            return redirect('/admin')
        elif session['role'] == 'Convenor':
            return redirect('/convenor/pending&report?view=pending')
        elif session['role'] == 'Chair':
            return redirect('/chairman')
        else:
            username = user_name()
            msg = 'You do not have authority to access the reporting portal. Talk to IT support if you are a Lincoln student or staff.'
            return render_template('message.html', msg = msg, user_name = username, user_role = session['role'], user_action = 'na')

# Log out function
@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    session.pop('role', None)
    return redirect('/')

# Validate if a user if logged in when accessing restricted access pages
def login_required(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        if 'loggedin' in session:
            return test(*args, **kwargs)
        else:
            return redirect('/')
    return wrap



# Get User Name
def user_name():
    cur = getCursor()
    if session['role'] == 'Student':
        cur.execute(f"SELECT CONCAT(firstname, ' ', lastname) FROM students WHERE userid = {session['id']}")
    else:
        cur.execute(f"SELECT CONCAT(firstname, ' ', lastname) FROM staff WHERE userid = {session['id']}")
    user_name = cur.fetchone()
    return user_name[0]


def student_report(report_id):
    cur = getCursor()
    cur.execute(f"SELECT t.studentuserid FROM \
    report r\
    LEFT JOIN thesis t\
    ON r.thesisid = t.thesisid\
    AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
    WHERE reportid = {report_id}")
    student_id = cur.fetchone()
    return student_id[0]

def staff_report(report_id, staff_user_id):
    cur = getCursor()
    cur.execute(
        f"SELECT s.supervisoruserid\
        FROM report r\
        LEFT JOIN thesis t\
        ON r.thesisid = t.thesisid\
        AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
        LEFT JOIN supervisionteam s\
        ON t.studentuserid = s.studentuserid\
        AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
        AND s.supervisoruserid = {staff_user_id} \
        WHERE r.reportid = {report_id}"
    )
    staff_ids = cur.fetchone()
    return staff_ids

def last_update(report_id, status):
    cur = getCursor()
    cur.execute(f"UPDATE report SET lastupdatedate = CURRENT_TIMESTAMP,\
        reportstatus = '{status}'\
        WHERE reportid = {report_id};")
    return None

def update_question_status(report_id, question_id):
    cur = getCursor()
    return cur.execute(f"UPDATE questionstatus\
                    SET status = 'Complete'\
                    WHERE reportid = {report_id} AND questionid = {question_id}")


@app.route("/instructions")
def instructions():
    username = user_name()
    return render_template('instruction.html', user_name = username, user_role = session['role'], user_action = 'edit')


    # ---------------
    # section A part
    # ---------------
def print_sectionA(report_id):
    cur = getCursor()
    cur.execute("select th.studentuserid from report as re join thesis as th on th.thesisid=re.thesisid where re.reportid = %s"%report_id)
    studentLoginID = cur.fetchall()[0][0]
    cur.execute("select st.studentid,st.enrolmentdate,st.address,st.phone,st.studymode,st.department,th.thesistitle from Students st join thesis th on th.studentuserid=st.userid where st. userid = %s"%(studentLoginID))
    sectionA = cur.fetchall()[0]
    cur.execute("select sp.supervisorrole, st.firstname, st.lastname from supervisionteam sp join staff st on sp.supervisoruserid=st.userid where CURRENT_TIMESTAMP BETWEEN sp.validfromdate AND sp.validtodate AND sp.studentuserid =%s"%studentLoginID)
    supervisionTeam =cur.fetchall()
    cur.execute("select sc.scholarshipname,st.value,st.validtodate from scholarshipstudent st join scholarships sc on st.scholarshipid = sc.scholarshipid where CURRENT_TIMESTAMP BETWEEN st.validfromdate AND st.validtodate AND st.studentuserid = %s"%studentLoginID)
    scholarships = cur.fetchall()
    cur.execute("select st.jobtitle,st.worktype,sf.firstname,sf.lastname,st.weeklyhours from studentemployment st join staff sf on sf.staffid=st.supervisoruserid where CURRENT_TIMESTAMP BETWEEN st.validfromdate AND st.validtodate AND st.studentuserid = %s"%studentLoginID)
    employment= cur.fetchall()

    return (sectionA, supervisionTeam, scholarships, employment)
    # ---------------
    # section B part
    # ---------------
def print_sectionB(report_id):
    cur = getCursor()
    cur.execute("select InductionProgramme, InductionProgrammeDate,MutualExpectationAgreement,MutualExpectationAgreementDate,KMRM,KMRMDate ,IntellectualPropertyAgreement,IntellectualPropertyAgreementDate,ThesisProposalSeminar,ThesisProposalSeminarDate,\
        ProposalApproval,ProposalApprovalDate,PGConference,PGConferenceDate,ResultsSeminar,ResultsSeminarDate,HumanEthicsApproval,HealthSafetyApproval,AnimalEthicsApproval,BiologicalSafetyApproval,RadiationProtectionApproval from milestones where reportid=%s"%report_id)
    sectionB = cur.fetchall()[0]
    return sectionB
    # ---------------
    # section C part
    # ---------------
def print_sectionC(report_id):
    cur = getCursor()
    cur.execute("select AccessPrincipalSupervisor,AccessPrincipalSupervisorComment,AccesssAssociateSupervisor,AccesssAssociateSupervisorComment,ExpertisePrincipalSupervisor,ExpertisePrincipalSupervisorComment,ExpertiseAssociateSupervisor,ExpertiseAssociateSupervisorComment,FeedbackQualityPrincipalSupervisor,FeedbackQualityPrincipalSupervisorComment,FeedbackQualityAssociateSupervisor,FeedbackQualityAssociateSupervisorComment,TimelinessPrincipalSupervisor,TimelinessPrincipalSupervisorComment,\
        TimelinessAssociateSupervisor,TimelinessAssociateSupervisorComment,CourseAvailability,CourseAvailabilityComment,Workspace,WorkspaceComment,ComputerFacility,ComputerFacilityComment,ITSupport,ITSupportComment,ResearchSoftware,ResearchSoftwareComment,Library,LibraryComment,LearningSupport,LearningSupportComment,StatSupport,StatSupportComment,ResearchEquipment,ResearchEquipmentComment,TechSupport,TechSupportComment,FinancialSupport,FinancialSupportComment,Other,OtherComment,SupervisorMeetingFreq,\
        FeedbackWaitPeriod,FeedbackMethod from evaluation where reportid=%s"%report_id)
    sectionC = cur.fetchall()[0]
    return sectionC
    # ---------------
    # section D part
    # ---------------
def print_sectionD(report_id):
    cur = getCursor()
    cur.execute("select objectivecomment, completionstatus,reasonforchange from currentobjective where reportid=%s order by uid"%report_id)
    sectionD1=cur.fetchall()
    cur.execute("select comment from covideffect where reportid=%s order by uid"%report_id)
    sectionD2=cur.fetchall()
    cur.execute("select comment from academicachievement where reportid= %s order by uid"%report_id)
    sectionD3=cur.fetchall()
    cur.execute("select title, duedate, comment from futureobjective where reportid=%s order by uid"%report_id)
    sectionD4=cur.fetchall()
    cur.execute("select title, amount, comment from expenditure where reportid=%s order by uid"%report_id) 
    sectionD5=cur.fetchall()
    sectionD=[sectionD1,sectionD2,sectionD3,sectionD4,sectionD5]
    return sectionD    
    # ---------------
    # section E part
    # ---------------
def print_sectionE(report_id):
    cur = getCursor()
    cur.execute(f"select a.uid, a.supervisoruserid, a.sixmonthprogress,a.phdprogress,a.academicqaulity,\
        a.technicalskills,a.likelytoachieveobjectives,a.recommendationcarriedout, a.comments, \
        s.firstname, s.lastname, t.supervisorrole\
        from assessmentbysupervisor a \
        LEFT JOIN staff s\
        ON a.supervisoruserid = s.userid\
            AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
        LEFT JOIN report r\
        ON r.reportid = a.reportid\
        LEFT JOIN thesis th\
        ON th.thesisid = r.thesisid\
        AND CURRENT_TIMESTAMP BETWEEN th.validfromdate AND th.validtodate\
        LEFT JOIN supervisionteam t\
        ON t.supervisoruserid = s.userid\
            AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
            AND t.studentuserid = th.studentuserid \
        WHERE a.reportid = {report_id}\
        ORDER BY CASE WHEN t.supervisorrole LIKE 'Supervisor' THEN 0\
            WHEN t.supervisorrole LIKE 'Associate' THEN 1\
            ELSE 2 END ASC")
    supervisor_feedback = cur.fetchall()
    cur.execute(f"SELECT a.uid, a.convenoruserid, a.areaofconsideration, a.rating, s.firstname, s.lastname\
            FROM assessmentbyconvenor a\
            LEFT JOIN staff s\
            ON a.convenoruserid = s.userid\
            AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
            WHERE a.reportid = {report_id}")
    convenor_feedback = cur.fetchone()
    return (supervisor_feedback, convenor_feedback)

    # ---------------
    # section F part
    # ---------------

def print_sectionF(report_id):
    cur=getCursor()
    cur.execute(f"SELECT abs.reportid, CONCAT(s.firstname, ' ', s.lastname) AS name, comments, s.userid, s.position, s.email\
        FROM assessmentbystudent abs\
        LEFT JOIN staff s\
        ON abs.talkinpersonuserid = s.userid\
        WHERE reportid = {report_id}")
    abs_result = cur.fetchone()
    return abs_result

##########################################################################################
##########################################################################################
##################################### Security ###########################################
##########################################################################################
##########################################################################################

#Restrict SectionA-D,F editing authority to students and admin 
def restricted_access_student(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        cur = getCursor()
        if request.method == 'GET':
            report_id = request.args.get('report')
        else:
            report_id = request.form.get('reportid')
        position = 'Student'
        cur.execute(f"SELECT position FROM staff\
            WHERE userid = {session['id']}\
            AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate;")
        result = cur.fetchone()
        if result != None:
            position = result[0]
        if position == 'Student':
            student_user_id = student_report(report_id)
            print(position, report_id, student_user_id, session['id'])
            if session['id'] == student_user_id:
                return test(*args, **kwargs)#student ID must match report's student ID
            else:
                username = user_name()
                msg = "You do not have authority to edit another student's report"
                return render_template('Message.html', msg = msg, user_name = username, user_role = session['role'], user_action = 'na')
        elif position == 'Admin':
            return test(*args, **kwargs)
        else:
            username = user_name()
            msg = 'You do not have authority to edit section of the form'
            return render_template('Message.html', msg = msg, user_name = username, user_role = session['role'], user_action = 'na')
    return wrap

#Restrict SectionE editing authority to students and admin 
def restricted_access_staff(test):
    @wraps(test)
    def wrap(*args, **kwargs):
        cur = getCursor()
        if request.method == 'GET':
            report_id = request.args.get('report')
            print(report_id, session['role'])
        else:
            report_id = request.form.get('reportid')
        position = session['role']
        if position == 'Professor':
            staff_user_id = staff_report(report_id, session['id'])
            print(staff_user_id)
            if staff_user_id[0] is not None:
                return test(*args, **kwargs)#staff ID must match report's staff ID
            else:
                username = user_name()
                msg = "You do not have access to this report because you are not a supervisor for this thesis"
                return render_template('Message.html', msg = msg, user_name = username, user_role = session['role'], user_action = 'na')
        elif position == 'Admin' or position == 'Convenor':
            return test(*args, **kwargs)
        else:
            username = user_name()
            msg = 'You do not have authority to edit section of the form'
            return render_template('Message.html', msg = msg, user_name = username, user_role = session['role'], user_action = 'na')
    return wrap



# Log out of the website
# @app.route('/logout')
# def logout():
#     session.pop('loggedin', None)
#     session.pop('id', None)
#     session.pop('username', None)
#     session.pop('role', None)
#     return redirect('/login')

##########################################################################################
##########################################################################################
############################# Student #################################################
##########################################################################################
##########################################################################################

@app.route('/student', methods=['GET', 'POST'])
@login_required
def student():    #landing page
    if request.method == 'GET':
        username = user_name()
        cur = getCursor()
        cur.execute(f"select * from report,thesis where report.thesisid = thesis.thesisid\
            and CURRENT_TIMESTAMP BETWEEN thesis.validfromdate AND thesis.validtodate\
            and thesis.studentuserid = {session['id']} group by report.reportid, thesis.thesisid;")
        select_result = cur.fetchall()
        print(select_result)
        return render_template('landing.html', select_result = select_result, user_name = username, user_role = session['role'], user_action = 'na')


@app.route('/student/view', methods = ['GET'])
@login_required
def studentview():
    username = user_name()
    Name = request.args.get('student')
    studentName = request.args.get('student')
    reportID = int(request.args.get('reportID'))

    print(reportID)
    cur = dbconn
    cur.execute("select th.studentuserid from report as re join thesis as th on th.thesisid=re.thesisid where re.reportid = %s"%reportID)
    studentLoginID = cur.fetchall()[0][0]
    # ---------------
    # section A part
    # ---------------
    cur.execute("select st.studentid,st.enrolmentdate,st.address,st.phone,st.studymode,st.department,th.thesistitle from Students st join thesis th on th.studentuserid=st.userid where st. userid = %s"%(studentLoginID))
    sectionA = cur.fetchall()[0]
    cur.execute("select sp.supervisorrole, st.firstname, st.lastname from supervisionteam sp join staff st on sp.supervisoruserid=st.userid where sp.studentuserid =%s"%studentLoginID)
    supervisionTeam =cur.fetchall()
    cur.execute("select sc.scholarshipname,st.value,st.validtodate from scholarshipstudent st join scholarships sc on st.scholarshipid = sc.scholarshipid where st.studentuserid = %s"%studentLoginID)
    scholarships = cur.fetchall()
    cur.execute("select st.jobtitle,st.worktype,sf.firstname,sf.lastname,st.weeklyhours from studentemployment st join staff sf on sf.staffid=st.supervisoruserid where st.studentuserid = %s"%studentLoginID)
    employment= cur.fetchall()
    print(scholarships)
    print(employment)
    # ---------------
    # section B part
    # ---------------
    cur.execute("select InductionProgramme, InductionProgrammeDate,MutualExpectationAgreement,MutualExpectationAgreementDate,KMRM,KMRMDate ,IntellectualPropertyAgreement,IntellectualPropertyAgreementDate,ThesisProposalSeminar,ThesisProposalSeminarDate,\
        ProposalApproval,ProposalApprovalDate,PGConference,PGConferenceDate,ResultsSeminar,ResultsSeminarDate,HumanEthicsApproval,HealthSafetyApproval,AnimalEthicsApproval,BiologicalSafetyApproval,RadiationProtectionApproval from milestones where reportid=%s"%reportID)
    sectionB = cur.fetchall()[0]
    # ---------------
    # section C part
    # ---------------
    cur.execute("select AccessPrincipalSupervisor,AccessPrincipalSupervisorComment,AccesssAssociateSupervisor,AccesssAssociateSupervisorComment,ExpertisePrincipalSupervisor,ExpertisePrincipalSupervisorComment,ExpertiseAssociateSupervisor,ExpertiseAssociateSupervisorComment,FeedbackQualityPrincipalSupervisor,FeedbackQualityPrincipalSupervisorComment,FeedbackQualityAssociateSupervisor,FeedbackQualityAssociateSupervisorComment,TimelinessPrincipalSupervisor,TimelinessPrincipalSupervisorComment,\
        TimelinessAssociateSupervisor,TimelinessAssociateSupervisorComment,CourseAvailability,CourseAvailabilityComment,Workspace,WorkspaceComment,ComputerFacility,ComputerFacilityComment,ITSupport,ITSupportComment,ResearchSoftware,ResearchSoftwareComment,Library,LibraryComment,LearningSupport,LearningSupportComment,StatSupport,StatSupportComment,ResearchEquipment,ResearchEquipmentComment,TechSupport,TechSupportComment,FinancialSupport,FinancialSupportComment,Other,OtherComment,SupervisorMeetingFreq,\
        FeedbackWaitPeriod,FeedbackMethod from evaluation where reportid=%s"%reportID)
    sectionC = cur.fetchall()[0]
    # ---------------
    # section D part
    # ---------------
    cur.execute("select objectivecomment, completionstatus,reasonforchange from currentobjective where reportid=%s order by uid"%reportID)
    sectionD1=cur.fetchall()
    cur.execute("select comment from covideffect where reportid=%s order by uid"%reportID)
    sectionD2=cur.fetchall()
    cur.execute("select comment from academicachievement where reportid= %s order by uid"%reportID)
    sectionD3=cur.fetchall()
    cur.execute("select title, duedate, comment from futureobjective where reportid=%s order by uid"%reportID)
    sectionD4=cur.fetchall()
    cur.execute("select title, amount, comment from expenditure where reportid=%s order by uid"%reportID) 
    sectionD5=cur.fetchall()
    sectionD=[sectionD1,sectionD2,sectionD3,sectionD4,sectionD5]
    # ---------------
    # section F part
    # ---------------
    cur.execute("SELECT abs.reportid, CONCAT(s.firstname, ' ', s.lastname) AS name, comments, s.userid, s.position, s.email\
        FROM assessmentbystudent abs\
        LEFT JOIN staff s\
        ON abs.talkinpersonuserid = s.userid\
        WHERE reportid = %s"%reportID)
    sectionF = cur.fetchone()
    print(sectionF)
    
    sectionE = print_sectionE(reportID)

    return render_template('student_view.html',reportID = reportID, 
    Name = studentName, sectionA=sectionA,sectionB=sectionB,sectionC=sectionC,sectionD=sectionD,
    supervisor_feedback = sectionE[0], convenor_feedback = sectionE[1],
    supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment,sectionF=sectionF,user_name = username, user_role = session['role'], user_action = 'na')


@app.route('/section_abcdf/edit/submit', methods = ['GET', 'POST'])
@login_required
@restricted_access_student
def submit_sectionABCDF():
    cur = getCursor()
    if request.method == 'GET':
        report_id = request.args.get('report')
        sectionA_data = print_sectionA(report_id)
        sectionA = sectionA_data[0]
        supervisionTeam = sectionA_data[1]
        scholarships = sectionA_data[2]
        employment = sectionA_data[3]
        sectionB = print_sectionB(report_id)
        sectionC = print_sectionC(report_id)
        sectionD = print_sectionD(report_id)
        sectionF = print_sectionF(report_id)
        username = user_name()
        return render_template('view_report.html',report_id = report_id, sectionA=sectionA,sectionB=sectionB,
        sectionC=sectionC,sectionD=sectionD, sectionF=sectionF, action='student_submit',
        supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment, user_name = username, user_role = session['role'], user_action = 'edit')


    else:
        report_id = request.form.get('reportid')
        cur.execute(f'UPDATE report SET sectionabcdsubmissiondate = CURRENT_TIMESTAMP WHERE reportid = {report_id}')
        return redirect('/student')




##########################################################################################
##########################################################################################
########################### Supervisor ###########################################
##########################################################################################
##########################################################################################

@app.route('/supervisor/view', methods = ['GET'])
def supervisorview():
    username = user_name()
    Name = request.args.get('student')
    studentName = request.args.get('student')
    reportID = int(request.args.get('reportID'))

    print(reportID)
    cur = dbconn
    cur.execute("select th.studentuserid from report as re join thesis as th on th.thesisid=re.thesisid where re.reportid = %s"%reportID)
    studentLoginID = cur.fetchall()[0][0]
    # ---------------
    # section A part
    # ---------------
    cur.execute("select st.studentid,st.enrolmentdate,st.address,st.phone,st.studymode,st.department,th.thesistitle from Students st join thesis th on th.studentuserid=st.userid where st. userid = %s"%(studentLoginID))
    sectionA = cur.fetchall()[0]
    cur.execute("select sp.supervisorrole, st.firstname, st.lastname from supervisionteam sp join staff st on sp.supervisoruserid=st.userid where sp.studentuserid =%s"%studentLoginID)
    supervisionTeam =cur.fetchall()
    cur.execute("select sc.scholarshipname,st.value,st.validtodate from scholarshipstudent st join scholarships sc on st.scholarshipid = sc.scholarshipid where st.studentuserid = %s"%studentLoginID)
    scholarships = cur.fetchall()
    cur.execute("select st.jobtitle,st.worktype,sf.firstname,sf.lastname,st.weeklyhours from studentemployment st join staff sf on sf.staffid=st.supervisoruserid where st.studentuserid = %s"%studentLoginID)
    employment= cur.fetchall()
    print(scholarships)
    print(employment)
    # ---------------
    # section B part
    # ---------------
    cur.execute("select InductionProgramme, InductionProgrammeDate,MutualExpectationAgreement,MutualExpectationAgreementDate,KMRM,KMRMDate ,IntellectualPropertyAgreement,IntellectualPropertyAgreementDate,ThesisProposalSeminar,ThesisProposalSeminarDate,\
        ProposalApproval,ProposalApprovalDate,PGConference,PGConferenceDate,ResultsSeminar,ResultsSeminarDate,HumanEthicsApproval,HealthSafetyApproval,AnimalEthicsApproval,BiologicalSafetyApproval,RadiationProtectionApproval from milestones where reportid=%s"%reportID)
    sectionB = cur.fetchall()[0]
    # ---------------
    # section C part
    # ---------------
    cur.execute("select AccessPrincipalSupervisor,AccessPrincipalSupervisorComment,AccesssAssociateSupervisor,AccesssAssociateSupervisorComment,ExpertisePrincipalSupervisor,ExpertisePrincipalSupervisorComment,ExpertiseAssociateSupervisor,ExpertiseAssociateSupervisorComment,FeedbackQualityPrincipalSupervisor,FeedbackQualityPrincipalSupervisorComment,FeedbackQualityAssociateSupervisor,FeedbackQualityAssociateSupervisorComment,TimelinessPrincipalSupervisor,TimelinessPrincipalSupervisorComment,\
        TimelinessAssociateSupervisor,TimelinessAssociateSupervisorComment,CourseAvailability,CourseAvailabilityComment,Workspace,WorkspaceComment,ComputerFacility,ComputerFacilityComment,ITSupport,ITSupportComment,ResearchSoftware,ResearchSoftwareComment,Library,LibraryComment,LearningSupport,LearningSupportComment,StatSupport,StatSupportComment,ResearchEquipment,ResearchEquipmentComment,TechSupport,TechSupportComment,FinancialSupport,FinancialSupportComment,Other,OtherComment,SupervisorMeetingFreq,\
        FeedbackWaitPeriod,FeedbackMethod from evaluation where reportid=%s"%reportID)
    sectionC = cur.fetchall()[0]
    # ---------------
    # section D part
    # ---------------
    cur.execute("select objectivecomment, completionstatus,reasonforchange from currentobjective where reportid=%s order by uid"%reportID)
    sectionD1=cur.fetchall()
    cur.execute("select comment from covideffect where reportid=%s order by uid"%reportID)
    sectionD2=cur.fetchall()
    cur.execute("select comment from academicachievement where reportid= %s order by uid"%reportID)
    sectionD3=cur.fetchall()
    cur.execute("select title, duedate, comment from futureobjective where reportid=%s order by uid"%reportID)
    sectionD4=cur.fetchall()
    cur.execute("select title, amount, comment from expenditure where reportid=%s order by uid"%reportID) 
    sectionD5=cur.fetchall()
    sectionD=[sectionD1,sectionD2,sectionD3,sectionD4,sectionD5]

    
    sectionE = print_sectionE(reportID)

    return render_template('student_view.html',reportID = reportID, 
    Name = studentName, sectionA=sectionA,sectionB=sectionB,sectionC=sectionC,sectionD=sectionD,
    supervisor_feedback = sectionE[0], convenor_feedback = sectionE[1],
    supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment,user_name = username, user_role = session['role'], user_action = 'edit')


@app.route('/supervisor/pending&report', methods = ['GET','POST'])
@login_required
def supervisor():
    username = user_name()
    supervisor_id = session['id']
    cur = getCursor()
    if request.method == 'GET':
        panel_view = request.args.get('view')
        cur.execute(f"select\
                th.thesistitle \
                ,re.reportid\
                ,re.reportorder\
                ,re.duedate\
                ,re.reportstatus\
                ,CONCAT(s.firstname, ' ', s.lastname) AS student_name\
                ,s.userid AS studentuserid\
                ,abs.supervisoruserid\
                ,CASE WHEN re.sectionabcdsubmissiondate IS NULL THEN 'Unavailable'\
                WHEN re.sectionabcdsubmissiondate IS NOT NULL AND abs.submissiondate IS NULL THEN 'Pending'\
                WHEN re.sectionabcdsubmissiondate IS NOT NULL AND abs.submissiondate IS NOT NULL \
                AND re.reportstatus LIKE 'Incomplete' THEN 'Complete'\
                WHEN re.reportstatus = 'Complete' THEN 'Approved'\
                ELSE 'N/A'\
                END AS report_status\
                ,re.sectionabcdsubmissiondate\
                ,abs.submissiondate\
                from report as re \
                left join thesis as th on th.thesisid=re.thesisid \
                left join students as s\
                ON s.userid = th.studentuserid\
                inner join assessmentbysupervisor as abs\
                ON abs.reportid = re.reportid AND abs.supervisoruserid = {supervisor_id}")
        all_reports = cur.fetchall()
        return render_template('Control_panel_supervisor.html',all_reports = all_reports, 
        user_name = username, user_role = session['role'], user_action = 'edit', panel_view = panel_view)


@app.route('/supervisor/studentlist', methods = ['GET','POST'])
@login_required
def studentList():
    supervisorID = session['id']
    cur = getCursor()
    cur.execute("select studentuserid from supervisionteam where supervisoruserid= %s"%(supervisorID))
    students = cur.fetchall()
    if students:
        DataUndersupervision = []
        for eachstudent in students:
            cur.execute("select firstname,lastname from students where userid = %s"%(eachstudent))
            professorName = cur.fetchall()
            professorName= professorName[0][0]+' '+professorName[0][1]
            name = [professorName]
            cur.execute("select re.reportid from report as re \
            join thesis as th on th.thesisid=re.thesisid \
            join login as lo on th.studentuserid = lo.userid \
            where lo.userid = %s "%(eachstudent))
            reportID = cur.fetchall()
            name = [eachstudent,name,reportID]
            DataUndersupervision.append(name)
    username = user_name()
    return render_template('supervisor_studentList.html',students=DataUndersupervision, user_name = username, user_role = session['role'], user_action = 'na')


@app.route('/supervisor/undersupervision', methods = ['GET'])
@login_required
def studentUnderSupervision():
    Name = request.args.get('student')
    studentName = request.args.get('student')
    reportID = int(request.args.get('reportID'))
    admin = request.args.get('admin')

    print(reportID)
    cur = dbconn
    cur.execute("select th.studentuserid from report as re join thesis as th on th.thesisid=re.thesisid where re.reportid = %s"%reportID)
    studentLoginID = cur.fetchall()[0][0]
    # ---------------
    # section A part
    # ---------------
    cur.execute("select st.studentid,st.enrolmentdate,st.address,st.phone,st.studymode,st.department,th.thesistitle from Students st join thesis th on th.studentuserid=st.userid where st. userid = %s"%(studentLoginID))
    sectionA = cur.fetchall()[0]
    cur.execute("select sp.supervisorrole, st.firstname, st.lastname from supervisionteam sp join staff st on sp.supervisoruserid=st.userid where sp.studentuserid =%s"%studentLoginID)
    supervisionTeam =cur.fetchall()
    cur.execute("select sc.scholarshipname,st.value,st.validtodate from scholarshipstudent st join scholarships sc on st.scholarshipid = sc.scholarshipid where st.studentuserid = %s"%studentLoginID)
    scholarships = cur.fetchall()
    cur.execute("select st.jobtitle,st.worktype,sf.firstname,sf.lastname,st.weeklyhours from studentemployment st join staff sf on sf.staffid=st.supervisoruserid where st.studentuserid = %s"%studentLoginID)
    employment= cur.fetchall()
    print(scholarships)
    print(employment)
    # ---------------
    # section B part
    # ---------------
    cur.execute("select InductionProgramme, InductionProgrammeDate,MutualExpectationAgreement,MutualExpectationAgreementDate,KMRM,KMRMDate ,IntellectualPropertyAgreement,IntellectualPropertyAgreementDate,ThesisProposalSeminar,ThesisProposalSeminarDate,\
        ProposalApproval,ProposalApprovalDate,PGConference,PGConferenceDate,ResultsSeminar,ResultsSeminarDate,HumanEthicsApproval,HealthSafetyApproval,AnimalEthicsApproval,BiologicalSafetyApproval,RadiationProtectionApproval from milestones where reportid=%s"%reportID)
    sectionB = cur.fetchall()[0]
    # ---------------
    # section C part
    # ---------------
    cur.execute("select AccessPrincipalSupervisor,AccessPrincipalSupervisorComment,AccesssAssociateSupervisor,AccesssAssociateSupervisorComment,ExpertisePrincipalSupervisor,ExpertisePrincipalSupervisorComment,ExpertiseAssociateSupervisor,ExpertiseAssociateSupervisorComment,FeedbackQualityPrincipalSupervisor,FeedbackQualityPrincipalSupervisorComment,FeedbackQualityAssociateSupervisor,FeedbackQualityAssociateSupervisorComment,TimelinessPrincipalSupervisor,TimelinessPrincipalSupervisorComment,\
        TimelinessAssociateSupervisor,TimelinessAssociateSupervisorComment,CourseAvailability,CourseAvailabilityComment,Workspace,WorkspaceComment,ComputerFacility,ComputerFacilityComment,ITSupport,ITSupportComment,ResearchSoftware,ResearchSoftwareComment,Library,LibraryComment,LearningSupport,LearningSupportComment,StatSupport,StatSupportComment,ResearchEquipment,ResearchEquipmentComment,TechSupport,TechSupportComment,FinancialSupport,FinancialSupportComment,Other,OtherComment,SupervisorMeetingFreq,\
        FeedbackWaitPeriod,FeedbackMethod from evaluation where reportid=%s"%reportID)
    sectionC = cur.fetchall()[0]
    # ---------------
    # section D part
    # ---------------
    cur.execute("select objectivecomment, completionstatus,reasonforchange from currentobjective where reportid=%s order by uid"%reportID)
    sectionD1=cur.fetchall()
    cur.execute("select comment from covideffect where reportid=%s order by uid"%reportID)
    sectionD2=cur.fetchall()
    cur.execute("select comment from academicachievement where reportid= %s order by uid"%reportID)
    sectionD3=cur.fetchall()
    cur.execute("select title, duedate, comment from futureobjective where reportid=%s order by uid"%reportID)
    sectionD4=cur.fetchall()
    cur.execute("select title, amount, comment from expenditure where reportid=%s order by uid"%reportID) 
    sectionD5=cur.fetchall()
    sectionD=[sectionD1,sectionD2,sectionD3,sectionD4,sectionD5]
    # ---------------
    # section F part
    # ---------------
    cur.execute("SELECT abs.reportid, CONCAT(s.firstname, ' ', s.lastname) AS name, comments, s.userid, s.position, s.email\
        FROM assessmentbystudent abs\
        LEFT JOIN staff s\
        ON abs.talkinpersonuserid = s.userid\
        WHERE reportid = %s"%reportID)
    sectionF = cur.fetchone()
    print(sectionF)
    # ---------------
    # section E part
    # ---------------
    cur.execute("select a.uid, a.supervisoruserid, a.sixmonthprogress,a.phdprogress,a.academicqaulity,\
        a.technicalskills,a.likelytoachieveobjectives,a.recommendationcarriedout, a.comments, \
        s.firstname, s.lastname, t.supervisorrole\
        from assessmentbysupervisor a \
        LEFT JOIN staff s\
        ON a.supervisoruserid = s.userid\
            AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
        LEFT JOIN report r\
        ON r.reportid = a.reportid\
        LEFT JOIN thesis th\
        ON th.thesisid = r.thesisid\
        AND CURRENT_TIMESTAMP BETWEEN th.validfromdate AND th.validtodate\
        LEFT JOIN supervisionteam t\
        ON t.supervisoruserid = s.userid\
            AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
            AND t.studentuserid = th.studentuserid \
        WHERE a.reportid = %s \
        ORDER BY CASE WHEN t.supervisorrole LIKE 'Supervisor' THEN 0\
            WHEN t.supervisorrole LIKE 'Associate' THEN 1\
            ELSE 2 END ASC"%reportID)
    supervisor_feedback = cur.fetchall()
    cur.execute(f"SELECT a.uid, a.convenoruserid, a.areaofconsideration, a.rating, s.firstname, s.lastname\
            FROM assessmentbyconvenor a\
            LEFT JOIN staff s\
            ON a.convenoruserid = s.userid\
            AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
            WHERE a.reportid =%s"%reportID)
    convenor_feedback = cur.fetchone()
    

    return render_template('supervisor_studentUnderSupervision.html',reportID = reportID, 
    Name = studentName, sectionA=sectionA,sectionB=sectionB,sectionC=sectionC,sectionD=sectionD,
    supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment,
    admin=admin,sectionF=sectionF,supervisor_feedback =supervisor_feedback, convenor_feedback =convenor_feedback)

@app.route('/supervisor/sectionE/index', methods = ['GET'])   # list of supervisors for the selected pending report
@login_required
def sectionE_supervisorList():
    reportID = int(request.args.get('reportID'))
    print(reportID)
    cur = dbconn
    cur.execute("select firstname, lastname from students st join thesis th on st.userid=th.studentuserid join report re on th.thesisid=re.thesisid where re.reportid=%s"%reportID)
    studentname = cur.fetchall()[0]
    cur.execute("select sp.supervisoruserid,st.firstname,st.lastname from assessmentbysupervisor sp\
        join staff st on st.userid =sp.supervisoruserid \
        where sp.reportid=%s"%reportID)
    select_result = cur.fetchall()
    cur.execute("select th.studentuserid from report re join thesis th on th.thesisid=re.thesisid where re.reportid=%s"%reportID)
    studentID = cur.fetchall()[0][0]
    role=[]
    for each in select_result:
        cur.execute("select supervisorrole from supervisionteam where supervisoruserid=%s and studentuserid=%s"%(each[0],studentID))
        role = role+[cur.fetchall()]
    print(select_result)
    EData=[]
    for aa in range(len(select_result)):
        EData.append([select_result[aa]]+role[aa])
    print(EData)
    return render_template('sectionE_index.html',EData=EData,reportID=reportID,studentname=studentname,loginID=session['id'],role=role)

##########################################################################################
##########################################################################################
################################ Convenor ####################################################################
##########################################################################################
##########################################################################################

@app.route('/convenor/pending&report', methods = ['GET','POST'])
@login_required
def convenor():
    # username = user_name()
    # cur = getCursor()
    # cur.execute("select reportid from assessmentbyconvenor where submissiondate = null")
    # cur.execute("select st.firstname, st.lastname,re.duedate,re.reportid from students st\
    #     join thesis th on st.userid= th.studentuserid\
    #     join report re on th.thesisid = re.thesisid\
    #     join assessmentbyconvenor ass on ass.reportid = re.reportid\
    #     where ass.submissiondate is NULL\
    #     order by ass.uid")
    # select_result = cur.fetchall()
    # print(select_result)
    # return render_template('Control_panel_convenor.html',students=select_result, user_name = username, user_role = session['role'], user_action = 'edit')

# @app.route('/supervisor/pending&report', methods = ['GET','POST'])
# def supervisor():
    username = user_name()
    cur = getCursor()
    if request.method == 'GET':
        panel_view = request.args.get('view')
        cur.execute(f"DROP TABLE IF EXISTS temp_1;\
                DROP TABLE IF EXISTS temp_2;\
                select *,\
                Row_Number() OVER (PARTITION BY reportid ORDER BY submissiondate DESC) AS RN\
                INTo TEMP TABLE temp_1\
                from assessmentbysupervisor\
                ORDER BY reportid;\
                SELECT *\
                INTO temp_2\
                FROM temp_1\
                WHERE RN = 1;\
                select\
                th.thesistitle\
                ,re.reportid\
                ,re.reportorder\
                ,re.duedate\
                ,re.reportstatus\
                ,CONCAT(s.firstname, ' ', s.lastname) AS student_name\
                ,s.userid AS studentuserid\
                ,abc.convenoruserid\
                ,CASE WHEN abs.submissiondate IS NULL THEN 'Unavailable'\
                WHEN abs.submissiondate IS NOT NULL AND abc.submissiondate IS NULL THEN 'Pending'\
                WHEN abs.submissiondate IS NOT NULL AND abc.submissiondate IS NOT NULL AND re.reportstatus LIKE 'Incomplete' THEN 'Complete'\
                WHEN re.reportstatus = 'Complete' THEN 'Approved'\
                ELSE 'N/A'\
                END AS report_status\
                ,re.sectionabcdsubmissiondate AS student_submit\
                ,abs.submissiondate As supervisor_submit\
                ,abc.submissiondate As convenor_submit\
                from report as re \
                left join thesis as th on th.thesisid=re.thesisid \
                left join students as s\
                ON s.userid = th.studentuserid\
                INNER join temp_2 as abs\
                ON abs.reportid = re.reportid\
                INNER join assessmentbyconvenor as abc\
                ON abc.reportid = re.reportid\
                AND abc.convenoruserid = {session['id']}")
        all_reports = cur.fetchall()
        return render_template('Control_panel_convenor.html',all_reports = all_reports, 
        user_name = username, user_role = session['role'], user_action = 'edit', panel_view = panel_view)










@app.route('/convenor/report', methods = ['GET','POST'])
@login_required
def convenor_report():
    username = user_name()
    cur = getCursor()
    reportID=request.args.get("ID")
    studentname = request.args.get("Name")
    print(studentname)
    report_id=reportID
    print(report_id)
    if request.method=="POST":
        cur.execute("update assessmentbyconvenor set areaofconsideration='%s',rating='%s' where reportid=%s"%(request.form['consideration'],request.form['trafficLight'],reportID))
        cur.execute("update report set lastupdatedate='%s' where reportid=%s"%(date.today(),reportID))
        if request.form.get('submit')=='Submit':
            cur.execute("update assessmentbyconvenor set submissiondate='%s' where reportid=%s"%(date.today(),reportID))
        return redirect('/convenor/pending&report?view=pending')
    cur = dbconn
    cur.execute("select areaofconsideration,rating from assessmentbyconvenor where reportid=%s"%reportID)
    select_result = cur.fetchall()
    print(select_result)
    ########################
    #     summary part     #
    ########################
    sectionA_data = print_sectionA(report_id)
    sectionA = sectionA_data[0]
    supervisionTeam = sectionA_data[1]
    scholarships = sectionA_data[2]
    employment = sectionA_data[3]
    sectionB = print_sectionB(report_id)
    sectionC = print_sectionC(report_id)
    sectionD = print_sectionD(report_id)
    supervisor_feedback, convenor_feedback= print_sectionE(report_id)
    sectionF = print_sectionF(report_id)
    print(supervisor_feedback)
    return render_template('convenor_report.html',comments=select_result,studentname=studentname,report_id = report_id, sectionA=sectionA,sectionB=sectionB,
    sectionC=sectionC,sectionD=sectionD, sectionF=sectionF, action='student_submit',supervisor_feedback = supervisor_feedback,
    supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment,user_name = username, user_role = session['role'], user_action = 'edit')



##########################################################################################
##########################################################################################
############################## Admin ############################################################
##########################################################################################
##########################################################################################

@app.route('/admin', methods = ['GET','POST'])
@login_required
def admin():
    if request.method == 'GET':
        username = user_name()
        return render_template('Control_panel_admin.html',user_name = username)
    else:
        username = user_name()
        today = date.today()
        search = request.form.get('search')
        cur = getConnection()
        cur = cur.cursor()
        cur.execute("DROP TABLE IF EXISTS temp_1;\
                DROP TABLE IF EXISTS temp_2;\
                select *,\
                Row_Number() OVER (PARTITION BY reportid ORDER BY submissiondate DESC) AS RN\
                INTo TEMP TABLE temp_1\
                from assessmentbysupervisor\
                ORDER BY reportid;\
                SELECT *\
                INTO temp_2\
                FROM temp_1\
                WHERE RN = 1;\
                select s.userid,concat(s.firstname, ' ', s.lastname) as name,\
                r.reportid, t.thesistitle, r.reportstatus,r.sectionabcdsubmissiondate, r.duedate, s.department,\
                abc.submissiondate as statusbyconvenor, abs.submissiondate as statusbysupervisor \
                from students as s inner join thesis as t on s.userid = t.studentuserid\
                inner join report as r on t.thesisid = r.thesisid\
                inner join questionstatus as q on r.reportid = q.reportid\
                inner join temp_2 as abs on abs.reportid = q.reportid\
                inner join assessmentbyconvenor as abc on abc.reportid = q.reportid\
                group by r.reportid, s.userid,t.thesistitle, r.sectionabcdsubmissiondate,s.firstname,\
                s.lastname, r.duedate, s.department,statusbyconvenor,statusbysupervisor,r.reportstatus \
                order by r.duedate asc;")
        select_result = cur.fetchall()
        cur.execute("select * from assessmentbyadmin;")
        lastupdatedate_admin = cur.fetchall()
        cur.execute(f"select abs.reportid, t.studentuserid, q.status, abs.supervisoruserid, concat(sta.firstname, ' ', sta.lastname) as name \
                        from ((((assessmentbysupervisor as abs inner join questionstatus as q on abs.reportid = q.reportid) \
                        inner join report as r on q.reportid = r.reportid) \
                        inner join thesis as t on r.thesisid = t.thesisid) \
                        inner join staff as sta on sta.userid = abs.supervisoruserid) \
                        where q.status = 'Incomplete' \
                        group by abs.reportid,t.studentuserid,q.status,abs.supervisoruserid, name \
                        order by abs.reportid;")
        un_supervisor_result = cur.fetchall()
        return render_template('Control_panel_admin.html', select_result = select_result, 
        un_supervisor_result=un_supervisor_result,search=search,today=today,
        lastupdatedate_admin=lastupdatedate_admin,user_name = username, user_role = session['role'], user_action = 'na')

@app.route('/notification', methods = ['GET','POST'])
@login_required
def Notification():
    if request.method == 'GET':
        if request.args.get('convenor') is None:
            username = user_name()
            student = request.args.get('student')
            reportid = request.args.get('reportid')
            cur = getConnection()
            cur = cur.cursor()
            cur.execute(f"select luemail, personalemail from students where userid = {student};")
            student_email = cur.fetchall()
            for i in student_email:
                student_email_list=i
#######################################################################
            cur.execute(f"select staff.email \
                        from ((students inner join supervisionteam on students.userid = supervisionteam.studentuserid) \
                        inner join staff on supervisionteam.supervisoruserid = staff.staffid) \
                        where students.userid = {student};")
            supervisor_email = cur.fetchall()
            supervisor_email_list=[]
            for i in supervisor_email:
                str =''.join(i)
                supervisor_email_list.append(str)
            supervisor_email_list = tuple(supervisor_email_list)
#######################################################################
            cur.execute(f"select thesistitle from thesis where studentuserid = {student};")
            thesis = cur.fetchall()
#######################################################################
            convenor_email = ('megan.clayton@lincoln.ac.nz')
            return render_template('Notification.html',student_email_list=student_email_list,supervisor_email_list=supervisor_email_list,
            thesis=thesis,reportid=reportid,convenor_email=convenor_email,user_name = username, user_role = session['role'], user_action = 'na')
        else:
            username = user_name()
            student = request.args.get('student')
            convenor = request.args.get('convenor')
            reportid = request.args.get('reportid')
            stustatus = request.args.get('stustatus')
            constatus = request.args.get('constatus')
            supstatus = request.args.get('supstatus')

            cur = getConnection()
            cur = cur.cursor()
            cur.execute(f"select luemail, personalemail from students where userid = {student};")
            student_email = cur.fetchall()
            for i in student_email:
                student_email_list=i
#######################################################################
            cur.execute(f"select thesistitle from thesis where studentuserid = {student};")
            thesis = cur.fetchall()
#######################################################################
            cur.execute(f"select staff.email from ((((staff inner join supervisionteam on staff.staffid = supervisionteam.supervisoruserid) \
                        inner join students on students.userid = supervisionteam.studentuserid) \
                        inner join thesis on thesis.studentuserid = students.userid) \
                        inner join report on report.thesisid = thesis.thesisid) \
                        where students.userid = {student} and report.reportid = {reportid};")
            supervisor_email_list = cur.fetchall()
#######################################################################
            convenor_email = ('megan.clayton@lincoln.ac.nz')
#######################################################################
            if stustatus == 'None':
                return render_template('Notification.html',student_email_list=student_email_list,thesis=thesis,reportid=reportid,
                user_name = username, user_role = session['role'], user_action = 'na')
            else:
                if supstatus == 'None':
                    return render_template('Notification.html',supervisor_email_list=supervisor_email_list,thesis=thesis,reportid=reportid,
                    user_name = username, user_role = session['role'], user_action = 'na')
                else:
                    return render_template('Notification.html',convenor_email=convenor_email,thesis=thesis,reportid=reportid,
                    user_name = username, user_role = session['role'], user_action = 'na')
    else:
        newreportid = genID()
        username = user_name()
        recipient = request.form.get('recipient')
        recipient1 = request.form.get('recipient1')
        recipient2 = request.form.get('recipient2')
        subject = request.form.get('subject')
        content = request.form.get('content')
        reportid = request.form.get('reportid')
        today = date.today()
        recipient3=recipient+recipient1+recipient2
        print(recipient3)
        print(subject)
        print(content)
        print(reportid)
        # yagmail.register('comp639group5@gmail.com','lincolnuni2021')
        # yag = yagmail.SMTP('comp639group5@gmail.com')
        # yag.send(to = recipient2, subject= subject, contents= content)
        cur = getConnection()
        cur = cur.cursor()

        cur.execute(f"SELECT thesisid FROM report WHERE reportid = {reportid}")
        thesisid = cur.fetchone()
        thesisid = thesisid[0]

        cur.execute(f"SELECT MAX(reportorder) + 1 FROM report WHERE reportid = {reportid}")
        reportorder = cur.fetchone()
        reportorder = reportorder[0]

        cur.execute(f"SELECT MAX(duedate) + INTERVAL '6 months' FROM report WHERE reportid = {reportid};")
        duedate = cur.fetchone()
        duedate = duedate[0]


        cur.execute(f"INSERT INTO report (reportid, thesisid, reportorder, reportstatus, duedate)\
        VALUES({newreportid}, {thesisid}, {reportorder}, 'Incomplete', '{duedate}')")
        
        cur.execute(f"SELECT reportid FROM report WHERE thesisid = {thesisid} ORDER BY reportorder DESC LIMIT 1")
        lastreportid = cur.fetchone()
        lastreportid = lastreportid[0]


        cur.execute(f"INSERT INTO questionstatus (reportid, questionid, status)\
        VALUES({lastreportid}, 1, 'Incomplete'),\
        ({lastreportid}, 2, 'Incomplete'),\
        ({lastreportid}, 3, 'Incomplete'),\
        ({lastreportid}, 4, 'Incomplete'),\
        ({lastreportid}, 5, 'Incomplete'),\
        ({lastreportid}, 6, 'Incomplete'),\
        ({lastreportid}, 7, 'Incomplete'),\
        ({lastreportid}, 8, 'Incomplete'),\
        ({lastreportid}, 9, 'Incomplete'),\
        ({lastreportid}, 10, 'Incomplete'),\
        ({lastreportid}, 11, 'Incomplete'),\
        ({lastreportid}, 12, 'Incomplete');\
        INSERT INTO milestones(reportid)\
        VALUES ({lastreportid});\
        INSERT INTO evaluation(reportid)\
        VALUES ({lastreportid});\
        SELECT s.supervisoruserid \
        FROM thesis t\
        LEFT JOIN supervisionteam s\
        ON t.studentuserid = s.studentuserid\
        AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
        WHERE CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
        AND thesisid = {thesisid}")
        
        supervisors = cur.fetchall()
        for s in supervisors:
            cur.execute(f"INSERT INTO assessmentbysupervisor(reportid, supervisoruserid)\
                    VALUES ({lastreportid}, {s[0]})")
        
        cur.execute(f"SELECT st.userid\
                    FROM report r\
                    LEFT JOIN thesis t\
                    ON CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
                    AND t.thesisid = r.thesisid\
                    LEFT JOIN students s\
                    ON CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
                    LEFT JOIN staff st\
                    ON CURRENT_TIMESTAMP BETWEEN st.validfromdate AND st.validtodate\
                    /*AND s.department = st.department*/\
                    AND st.position LIKE '%Convenor%'\
                    WHERE reportid = {reportid}\
                    LIMIT 1")
        convenor = cur.fetchone()
        cur.execute(f"INSERT INTO assessmentbyconvenor(reportid, convenoruserid)\
                    VALUES ({lastreportid}, {convenor[0]})")
        
        cur.execute(f"INSERT INTO assessmentbyadmin(UserID, ReportID,Adminid,LastUpdateDate,Action)\
            VALUES (16,{newreportid},16,'{today}',null)")



        cur.execute(f"UPDATE assessmentbyadmin set lastupdatedate = '{today}', action = 'done' where reportid = {reportid};")
        
        return render_template('Control_panel_admin.html',user_name = username, user_role = session['role'], user_action = 'edit')

@app.route('/admin/view', methods = ['GET'])
@login_required
def adminview():
    username = user_name()
    Name = request.args.get('student')
    studentName = request.args.get('student')
    reportID = int(request.args.get('reportID'))
    admin = request.args.get('admin')

    print(reportID)
    cur = dbconn
    cur.execute("select th.studentuserid from report as re join thesis as th on th.thesisid=re.thesisid where re.reportid = %s"%reportID)
    studentLoginID = cur.fetchall()[0][0]
    # ---------------
    # section A part
    # ---------------
    cur.execute("select st.studentid,st.enrolmentdate,st.address,st.phone,st.studymode,st.department,th.thesistitle from Students st join thesis th on th.studentuserid=st.userid where st. userid = %s"%(studentLoginID))
    sectionA = cur.fetchall()[0]
    cur.execute("select sp.supervisorrole, st.firstname, st.lastname from supervisionteam sp join staff st on sp.supervisoruserid=st.userid where sp.studentuserid =%s"%studentLoginID)
    supervisionTeam =cur.fetchall()
    cur.execute("select sc.scholarshipname,st.value,st.validtodate from scholarshipstudent st join scholarships sc on st.scholarshipid = sc.scholarshipid where st.studentuserid = %s"%studentLoginID)
    scholarships = cur.fetchall()
    cur.execute("select st.jobtitle,st.worktype,sf.firstname,sf.lastname,st.weeklyhours from studentemployment st join staff sf on sf.staffid=st.supervisoruserid where st.studentuserid = %s"%studentLoginID)
    employment= cur.fetchall()
    print(scholarships)
    print(employment)
    # ---------------
    # section B part
    # ---------------
    cur.execute("select InductionProgramme, InductionProgrammeDate,MutualExpectationAgreement,MutualExpectationAgreementDate,KMRM,KMRMDate ,IntellectualPropertyAgreement,IntellectualPropertyAgreementDate,ThesisProposalSeminar,ThesisProposalSeminarDate,\
        ProposalApproval,ProposalApprovalDate,PGConference,PGConferenceDate,ResultsSeminar,ResultsSeminarDate,HumanEthicsApproval,HealthSafetyApproval,AnimalEthicsApproval,BiologicalSafetyApproval,RadiationProtectionApproval from milestones where reportid=%s"%reportID)
    sectionB = cur.fetchall()[0]
    # ---------------
    # section C part
    # ---------------
    cur.execute("select AccessPrincipalSupervisor,AccessPrincipalSupervisorComment,AccesssAssociateSupervisor,AccesssAssociateSupervisorComment,ExpertisePrincipalSupervisor,ExpertisePrincipalSupervisorComment,ExpertiseAssociateSupervisor,ExpertiseAssociateSupervisorComment,FeedbackQualityPrincipalSupervisor,FeedbackQualityPrincipalSupervisorComment,FeedbackQualityAssociateSupervisor,FeedbackQualityAssociateSupervisorComment,TimelinessPrincipalSupervisor,TimelinessPrincipalSupervisorComment,\
        TimelinessAssociateSupervisor,TimelinessAssociateSupervisorComment,CourseAvailability,CourseAvailabilityComment,Workspace,WorkspaceComment,ComputerFacility,ComputerFacilityComment,ITSupport,ITSupportComment,ResearchSoftware,ResearchSoftwareComment,Library,LibraryComment,LearningSupport,LearningSupportComment,StatSupport,StatSupportComment,ResearchEquipment,ResearchEquipmentComment,TechSupport,TechSupportComment,FinancialSupport,FinancialSupportComment,Other,OtherComment,SupervisorMeetingFreq,\
        FeedbackWaitPeriod,FeedbackMethod from evaluation where reportid=%s"%reportID)
    sectionC = cur.fetchall()[0]
    # ---------------
    # section D part
    # ---------------
    cur.execute("select objectivecomment, completionstatus,reasonforchange from currentobjective where reportid=%s order by uid"%reportID)
    sectionD1=cur.fetchall()
    cur.execute("select comment from covideffect where reportid=%s order by uid"%reportID)
    sectionD2=cur.fetchall()
    cur.execute("select comment from academicachievement where reportid= %s order by uid"%reportID)
    sectionD3=cur.fetchall()
    cur.execute("select title, duedate, comment from futureobjective where reportid=%s order by uid"%reportID)
    sectionD4=cur.fetchall()
    cur.execute("select title, amount, comment from expenditure where reportid=%s order by uid"%reportID) 
    sectionD5=cur.fetchall()
    sectionD=[sectionD1,sectionD2,sectionD3,sectionD4,sectionD5]
    # ---------------
    # section F part
    # ---------------
    cur.execute("SELECT abs.reportid, CONCAT(s.firstname, ' ', s.lastname) AS name, comments, s.userid, s.position, s.email\
        FROM assessmentbystudent abs\
        LEFT JOIN staff s\
        ON abs.talkinpersonuserid = s.userid\
        WHERE reportid = %s"%reportID)
    sectionF = cur.fetchone()
    print(sectionF)
    # ---------------
    # section E part
    # ---------------
    cur.execute("select a.uid, a.supervisoruserid, a.sixmonthprogress,a.phdprogress,a.academicqaulity,\
        a.technicalskills,a.likelytoachieveobjectives,a.recommendationcarriedout, a.comments, \
        s.firstname, s.lastname, t.supervisorrole\
        from assessmentbysupervisor a \
        LEFT JOIN staff s\
        ON a.supervisoruserid = s.userid\
            AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
        LEFT JOIN report r\
        ON r.reportid = a.reportid\
        LEFT JOIN thesis th\
        ON th.thesisid = r.thesisid\
        AND CURRENT_TIMESTAMP BETWEEN th.validfromdate AND th.validtodate\
        LEFT JOIN supervisionteam t\
        ON t.supervisoruserid = s.userid\
            AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
            AND t.studentuserid = th.studentuserid \
        WHERE a.reportid = %s \
        ORDER BY CASE WHEN t.supervisorrole LIKE 'Supervisor' THEN 0\
            WHEN t.supervisorrole LIKE 'Associate' THEN 1\
            ELSE 2 END ASC"%reportID)
    supervisor_feedback = cur.fetchall()
    cur.execute(f"SELECT a.uid, a.convenoruserid, a.areaofconsideration, a.rating, s.firstname, s.lastname\
            FROM assessmentbyconvenor a\
            LEFT JOIN staff s\
            ON a.convenoruserid = s.userid\
            AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
            WHERE a.reportid =%s"%reportID)
    convenor_feedback = cur.fetchone()
    

    return render_template('admin_view.html',reportID = reportID, 
    Name = studentName, sectionA=sectionA,sectionB=sectionB,sectionC=sectionC,sectionD=sectionD,
    supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment,
    admin=admin,sectionF=sectionF,supervisor_feedback =supervisor_feedback, convenor_feedback =convenor_feedback,
    user_name = username, user_role = session['role'], user_action = 'edit')













##########################################################################################
##########################################################################################
############################ Section A #########################################################
##########################################################################################
##########################################################################################

@app.route('/section_a/edit', methods=['GET', 'POST'])
@login_required
@restricted_access_student
def sectionA():
    cur = getCursor()
    if request.method == 'POST':
        report_id = request.form.get['reportid']
        update_question_status(report_id, 1)
        return redirect(f'/section_a/edit?report={report_id}')

    else:
        username = user_name()
        report_id = request.args.get('report')
        #student_user_id = request.args.get('student')
        student_user_id = student_report(report_id)
        cur.execute(f"/* Get student details */\
            SELECT s.firstname\
            ,s.lastname\
            ,s.studentid\
            ,s.enrolmentdate\
            ,s.address\
            ,s.phone\
            ,s.studymode\
            ,t.thesistitle\
            ,s.luemail\
            ,s.personalemail\
            ,s.department\
            FROM students As s\
            LEFT JOIN thesis As t\
            ON s.userid = t.studentuserid\
            AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate \
            WHERE s.userid = {student_user_id} \
            AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate;"
            )

        student_details = cur.fetchone()
        student_name = student_details[0] + ' ' + student_details[1]
        student_id = student_details[2]
        enrolment_date = student_details[3]
        address = student_details[4]
        phone = student_details[5]
        study_mode = student_details[6]
        thesis_title = student_details[7]
        luemail = student_details[8]
        personalemail = student_details[9]
        department = student_details[10]


        cur.execute(f"/* Get supervisor team */\
            SELECT \
            sp.supervisorrole,\
            stf.firstname,\
            stf.lastname,\
            sp.supervisoruserid\
            FROM supervisionteam As sp\
            LEFT JOIN staff stf\
            ON sp.supervisoruserid = stf.userid\
            AND CURRENT_TIMESTAMP BETWEEN stf.validfromdate AND stf.validtodate\
            LEFT JOIN SortBy o\
            ON o.value = sp.supervisorrole\
            AND o.category = 'Supervisionteam'\
            WHERE sp.studentuserid = {student_user_id}\
            AND CURRENT_TIMESTAMP BETWEEN sp.validfromdate AND sp.validtodate\
            ORDER BY o.sequence, stf.firstname ASC;"
            )
        supervisors = cur.fetchall()

        cur.execute("SELECT userid, firstname, lastname\
            FROM staff WHERE position = 'Professor' \
                AND CURRENT_TIMESTAMP BETWEEN validfromdate and validtodate")
        job_supervisors = cur.fetchall()


    #Drop-down menu for adding chief supervisors - Anti join to exclude existing supervisor in the team
        cur.execute(f"WITH all_supervisors AS (SELECT b.userid, b.firstname, b.lastname\
            FROM students a\
            INNER JOIN staff b\
            ON a.department = b.department\
            AND CURRENT_TIMESTAMP BETWEEN b.validfromdate AND b.validtodate\
            WHERE a.userid = {student_user_id}\
            AND CURRENT_TIMESTAMP BETWEEN a.validfromdate AND a.validtodate\
            )\
            SELECT * \
            FROM all_supervisors c\
            WHERE NOT EXISTS\
            (\
            SELECT *\
            FROM students a\
            INNER JOIN supervisionteam t\
            ON a.userid = t.studentuserid\
            AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
            AND t.supervisorrole LIKE 'Supervisor'\
            WHERE a.userid = {student_user_id}\
            AND CURRENT_TIMESTAMP BETWEEN a.validfromdate AND a.validtodate\
            AND t.supervisoruserid = c.userid)")
        available_chief_supervisors = cur.fetchall()    

    #Drop-down menu for adding associate/other supervisors - Anti join to exclude existing supervisor in the team
        cur.execute(f"WITH all_supervisors AS (SELECT b.userid, b.firstname, b.lastname\
            FROM students a\
            INNER JOIN staff b\
            ON a.department = b.department\
            AND CURRENT_TIMESTAMP BETWEEN b.validfromdate AND b.validtodate\
            WHERE a.userid = {student_user_id}\
            AND CURRENT_TIMESTAMP BETWEEN a.validfromdate AND a.validtodate\
            )\
            SELECT * \
            FROM all_supervisors c\
            WHERE NOT EXISTS\
            (\
            SELECT *\
            FROM students a\
            INNER JOIN supervisionteam t\
            ON a.userid = t.studentuserid\
            AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
            AND t.supervisorrole NOT LIKE 'Supervisor'\
            WHERE a.userid = {student_user_id}\
            AND CURRENT_TIMESTAMP BETWEEN a.validfromdate AND a.validtodate\
            AND t.supervisoruserid = c.userid)")
        available_other_supervisors = cur.fetchall()

        cur.execute(f"/* Get scholarship details */\
            SELECT sc.scholarshipname\
            ,ss.value\
            ,ss.startdate\
            ,ss.enddate\
            ,FLOOR((CAST(ss.enddate AS date) - CAST(ss.startdate AS date))/365)+1 AS tenure\
            ,ss.uid\
            FROM scholarshipstudent AS ss\
            LEFT JOIN scholarships AS sc\
            ON ss.scholarshipid = sc.scholarshipid\
            WHERE CURRENT_TIMESTAMP BETWEEN ss.validfromdate AND ss.validtodate\
            AND ss.studentuserid = {student_user_id}"
            )
        scholarships = cur.fetchall()

        cur.execute("SELECT * FROM scholarships")
        available_scholarships = cur.fetchall()

        cur.execute(f"/* Get employment details */\
            SELECT \
            emp.jobtitle\
            ,emp.worktype\
            ,emp.weeklyhours\
            ,stf.firstname\
            ,stf.lastname\
            ,emp.uid\
            ,emp.supervisoruserid\
            FROM studentemployment AS emp\
            LEFT JOIN staff AS stf\
            ON emp.supervisoruserid = stf.userid\
            WHERE emp.studentuserid = {student_user_id}\
            AND CURRENT_TIMESTAMP BETWEEN emp.validfromdate AND emp.validtodate"
            )
        employment = cur.fetchall()

        return render_template('section_A.html', student_name = student_name, 
            student_id = student_id, enrolment_date = enrolment_date, address = address,
            phone = phone, department = department, luemail = luemail, 
            personalemail = personalemail, study_mode = study_mode, thesis_title = thesis_title, 
            supervisors = supervisors, scholarships = scholarships, employment = employment, 
            available_other_supervisors = available_other_supervisors, 
            available_chief_supervisors = available_chief_supervisors, 
            available_scholarships = available_scholarships, job_supervisors = job_supervisors,
            viewer_role = session['role'], report_id = report_id, student_user_id = student_user_id, user_name = username, user_role = session['role'], user_action = 'edit'
    )


@app.route('/section_a/edit/student', methods=['POST'])
@login_required
@restricted_access_student
def updateStudentInfo():
    cur = getCursor()
    if request.method == 'POST':
        student_name = request.form.get('studentName')
        split_student_name = student_name.split(' ', 1) #need to split full name by first space from the right
        first_name = split_student_name[0]
        last_name = split_student_name[1]
        student_id = request.form.get('studentId')
        enrolment_date = request.form.get('enrolDate')
        address = request.form.get('address')
        phone = request.form.get('ph')
        luemail = request.form.get('luemail')
        personalemail = request.form.get('personalemail')
        study_mode = request.form.get('studyMode')
        department = request.form.get('department')
        #student_user_id = request.form.get('student_user_id')
        report_id = request.form.get('reportid')
        print("test", report_id)
        student_user_id = student_report(report_id)

        cur.execute(f'''UPDATE students \
            SET validtodate = CURRENT_TIMESTAMP \
            WHERE userid = {student_user_id}\
            AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate;\
            INSERT INTO students (userid, studentid, firstname, lastname, enrolmentdate, department, address, phone,\
            luemail, personalemail, studymode)\
            VALUES ({student_user_id}, {student_id}, '{first_name}', '{last_name}', '{enrolment_date}', '{department}', \
            '{address}', {phone}, '{luemail}', '{personalemail}', '{study_mode}');'''
            )

        last_update(report_id, 'Incomplete')
        update_question_status(report_id, 1)

        #new_thesis_title = request.form.get('thesis')
        #new_chief_supervisor = request.form.get('chiefSup')
        #new_associate_super = request.form.get('ascSup')
        #new_other_supervisor = request.form.get('otherSup')
        #
        #
        #new_scholarship_name = request.form.get('scholarName')
        #new_value = request.form.get('value')
        #new_tenure = request.form.get('tenure')
        #new_end_date = request.form.get('endDate')
        #    
        #new_job_title = request.form.get('jobTitle')
        #new_work_type = request.form.get('workType')
        #new_supervisor_name = request.form.get('jobSup')
        #new_hours = request.form.get('hours')

        return redirect(f'/section_a/edit?report={report_id}')


@app.route('/section_a/edit/thesis', methods=['POST'])
@login_required
@restricted_access_student
def updateThesis():
    cur = getCursor()
    if request.method == 'POST':
        thesis_title = request.form.get('thesis')
        chief_supervisor = request.form.get('chiefSupervisor')
        associate_supervisors = request.form.getlist('associateSupervisor[]')
        other_supervisors = request.form.getlist('otherSupervisor[]')
        new_supervisors = request.form.getlist('newSupervisor[]')
        new_supervisor_roles = request.form.getlist('newSupervisorRole[]')
        delete = request.form.getlist('delete[]')
        print('delete now', delete)
        #student_user_id = request.form.get('student_user_id')
        report_id = request.form.get('reportid')
        student_user_id = student_report(report_id)
        print("Test if getting data",thesis_title, report_id, chief_supervisor, associate_supervisors, other_supervisors, new_supervisors,new_supervisor_roles, delete)

#dict showing all supervisors and roles to update
        all_supervisors = {}
        del_supervisors = {}
        list_supervisors = list()
        if chief_supervisor != None:
            all_supervisors[chief_supervisor] = 'Supervisor'
            for x in chief_supervisor:
                list_supervisors.append(x)
        if associate_supervisors != None:
            for i in associate_supervisors:
                all_supervisors[i] = 'Associate'
                list_supervisors.append(i)
        if other_supervisors != None:
            for k in other_supervisors:
                all_supervisors[k] = 'Other Supervisor'
                list_supervisors.append(k)
        if len(new_supervisors) > 0:
            all_supervisors.update(zip(new_supervisors, new_supervisor_roles))
            print(all_supervisors)
#create a dict showing whether a supervisor needs to be removed
            for y in new_supervisors:
                list_supervisors.append(y)
        #print(list_supervisors)
        del_supervisors.update(zip(list_supervisors, delete))
        print('delete', del_supervisors, list_supervisors, delete)
    #Get current supervisors
        cur.execute(f"SELECT supervisoruserid, supervisorrole\
            FROM supervisionteam\
            WHERE studentuserid = {student_user_id}\
            AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate;"
            )
        results = cur.fetchall()
        existing_supervisors = {}
        for i in results:
            existing_supervisors[i[0]] = i[1]
        print("all supervisors", all_supervisors, new_supervisors, del_supervisors)

#Check if supervisor already exists
        try:
            for p, r in all_supervisors.items():
                if int(p) not in existing_supervisors.keys() and del_supervisors[p] == 'N': #insert if supervisor doesn't exist
                    cur.execute(f"INSERT INTO supervisionteam (studentuserid, supervisoruserid, supervisorrole)\
                        VALUES ({student_user_id}, {p}, '{r}');\
                        INSERT INTO assessmentbysupervisor (reportid, supervisoruserid)\
                        VALUES ({report_id}, {p})")

                elif int(p) in existing_supervisors.keys() and del_supervisors[p] == 'Y': #  del if required
                    cur.execute(f"UPDATE supervisionteam\
                        SET validtodate = CURRENT_TIMESTAMP\
                        WHERE studentuserid = {student_user_id}\
                        AND supervisoruserid = {p}\
                        AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate;\
                        DELETE FROM assessmentbysupervisor WHERE reportid={report_id} AND supervisoruserid={p}")
                
                elif int(p) in existing_supervisors.keys() and r is not existing_supervisors[int(p)]: #update if role has changed
                    cur.execute(f"UPDATE supervisionteam\
                        SET validtodate = CURRENT_TIMESTAMP\
                        WHERE studentuserid = {student_user_id}\
                        AND supervisoruserid = {p}\
                        AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate;\
                        \
                        INSERT INTO supervisionteam (studentuserid, supervisoruserid, supervisorrole)\
                        VALUES ({student_user_id}, {p}, '{r}')")
        except Exception:
            username = user_name()
            msg = 'Oops..something went wrong. Try a different supervisor'
            return render_template('Message.html', msg = msg, 
            user_name=username,user_role=session['role'], user_action = 'edit')
    
        # Check if thesis title needs udpating
        cur.execute(f"SELECT t.thesistitle, t.thesisid FROM students AS s\
            INNER JOIN thesis AS t\
            ON s.userid = t.studentuserid\
            AND CURRENT_TIMESTAMP BETWEEN t.validfromdate and t.validtodate\
            WHERE s.userid = {student_user_id}\
                AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate")
        existing_thesis = cur.fetchone()
        if thesis_title != existing_thesis[0]:
            #cur.execute(f"SELECT thesisid FROM report WHERE reportid = {report_id}")
            #thesis_id = cur.fetchone()
            thesis_id = existing_thesis[1]

            cur.execute(f"UPDATE thesis\
            SET thesistitle = '{thesis_title}'\
            WHERE studentuserid = {student_user_id};")

            # cur.execute(f"SELECT thesisid FROM thesis WHERE studentuserid = {student_user_id} AND thesistitle = '{thesis_title}'")
            # thesis_id = cur.fetchone()
            # thesis_id = thesis_id[0]
            # cur.execute(f"UPDATE report SET thesisid = {thesis_id} WHERE reportid = {report_id}")
        
        last_update(report_id, 'Incomplete')
        update_question_status(report_id, 1)


        return redirect(f'/section_a/edit?report={report_id}')

#Update Scholarship
@app.route('/section_a/edit/scholarship', methods=['POST'])
@login_required
@restricted_access_student
def updateScholarhsip():
    cur = getCursor()
    scholarship_uid = request.form.getlist('scholarship_uid[]')
    value = request.form.getlist('existing_value[]')
    start_date = request.form.getlist('existing_startdate[]')
    end_date = request.form.getlist('existing_endDate[]')
    delete = request.form.getlist('delete[]')
    #student_user_id = request.form.get('student_user_id')
    report_id = request.form.get('reportid')
    student_user_id = student_report(report_id)
    print('existing scholars', scholarship_uid, value, start_date, end_date, delete)
    for u, v, s, e, d in zip(scholarship_uid, value, start_date, end_date, delete):
        if d == 'Y':
            cur.execute(f"UPDATE scholarshipstudent\
                SET validtodate = CURRENT_TIMESTAMP\
                WHERE uid = {int(u)}\
                    AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate;")
        else:
            cur.execute(f"UPDATE scholarshipstudent\
                SET value={int(float(v))}, startdate='{s}', enddate='{e}'\
                WHERE uid = {int(u)}\
                    AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate;")

    new_scholarship_id = request.form.getlist('new_scholarId[]')
    new_value = request.form.getlist('new_value[]')
    new_start_date = request.form.getlist('new_startdate[]')
    new_end_date = request.form.getlist('new_endDate[]')
    new_delete = request.form.getlist('new_delete[]')
    print('new scholars', new_scholarship_id, new_value, new_start_date, new_end_date, new_delete)
    for u, v, s, e, d in zip(new_scholarship_id, new_value, new_start_date, new_end_date, new_delete):
        if d == 'N':
            if e == '' or d == '':
                username = user_name()
                msg = 'ERROR: All fields but be filled out'
                return render_template('Message.html', msg = msg, 
                user_name=username,user_role=session['role'], user_action = 'edit')
            else:
                cur.execute(f"INSERT INTO scholarshipstudent(scholarshipid, studentuserid, value, startdate, enddate)\
                    VALUES({int(u)}, {student_user_id}, {float(v)}, '{s}', '{e}')")
    last_update(report_id, 'Incomplete')
    update_question_status(report_id, 1)

    return redirect(f'/section_a/edit?report={report_id}')

#Update employment
@app.route('/section_a/edit/job', methods=['POST'])
@login_required
@restricted_access_student
def updateJob():
    
    cur = getCursor()
    job_title = request.form.getlist('jobTitle[]')
    job_uid = request.form.getlist('jobid[]')
    work_type = request.form.getlist('workType[]')
    supervisor_id = request.form.getlist('jobSup[]')
    hours = request.form.getlist('hours[]')
    delete = request.form.getlist('delete[]')
    report_id = request.form.get('reportid')
    student_user_id = student_report(report_id)

    for j, u, w, s, h, d in zip(job_title, job_uid, work_type, supervisor_id, hours, delete):
        print('did run loop')
        if d == 'Y':
            print('wrong thing to do')
            cur.execute(f"UPDATE studentemployment\
                SET validtodate = CURRENT_TIMESTAMP\
                WHERE uid = {int(u)}\
                    AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate;")
        else:
            print('updating')
            cur.execute(f"UPDATE studentemployment\
                SET jobtitle='{j}', worktype='{w}', supervisoruserid={s}, weeklyhours={h}\
                WHERE uid = {int(u)}\
                    AND CURRENT_TIMESTAMP BETWEEN validfromdate AND validtodate;")

    new_job_title = request.form.getlist('new_jobTitle[]')
    new_work_type = request.form.getlist('new_workType[]')
    new_supervisor_id = request.form.getlist('new_jobSup[]')
    new_hours = request.form.getlist('new_hours[]')
    new_delete = request.form.getlist('new_delete[]')

    for j, w, s, h, d in zip(new_job_title, new_work_type, new_supervisor_id, new_hours, new_delete):
        uid = genID()
        if d == 'N':
            if s == 'Null':
                cur.execute(f"INSERT INTO studentemployment(uid, studentuserid, jobtitle, worktype, supervisoruserid, weeklyhours)\
                    VALUES({uid}, {session['id']}, '{j}', '{w}', NULL, {h})") #not working. null not allowed
            else:
                cur.execute(f"INSERT INTO studentemployment(uid, studentuserid, jobtitle, worktype, supervisoruserid, weeklyhours)\
                    VALUES({uid}, {session['id']}, '{j}', '{w}', {s}, {h})")
# Update report table with last update date. Update question status table as complete
    last_update(report_id, 'Incomplete')
    update_question_status(report_id, 1)

    return redirect(f'/section_a/edit?report={report_id}')


##########################################################################################
##########################################################################################
######################################## Section B ###################################
##########################################################################################
##########################################################################################

@app.route('/section_b1/edit', methods=['GET', 'POST'])
@login_required
@restricted_access_student
def studentSectionB1():
    if request.method == 'GET':
        username = user_name()
        cur = getCursor()
        report_id = request.args.get('report')
        cur.execute(f"select * from milestones where reportid = {report_id}")
        select_result = cur.fetchall()
        print(select_result)
        return render_template('section_B1.html', select_result = select_result, report_id = report_id, 
        user_name = username, user_role = session['role'], user_action = 'edit')

    else:
        uid = request.form.get('uid')
        reportid = request.form.get('reportid')
        questionid = request.form.get('questionid')
        submit_type = request.form.get('submit')
        InductionProgramme = request.form.get('InductionProgramme')
        if InductionProgramme == 'N' or InductionProgramme == 'null':
            InductionProgrammeDate = None
        else:
            InductionProgrammeDate = request.form.get('InductionProgrammeDate')
            if InductionProgrammeDate == '':
                InductionProgrammeDate = datetime.today()
        MutualExpectationAgreement = request.form.get('MutualExpectationAgreement')
        if MutualExpectationAgreement == 'N' or MutualExpectationAgreement == 'null':
            MutualExpectationAgreementDate = None
        else:
            MutualExpectationAgreementDate = request.form.get('MutualExpectationAgreementDate')
            if MutualExpectationAgreementDate == '':
                MutualExpectationAgreementDate = datetime.today()
        KMRM = request.form.get('KMRM')
        if KMRM == 'N' or KMRM == 'null':
            KMRMDate = None
        else:
            KMRMDate = request.form.get('KMRMDate')
            if KMRMDate == '':
                KMRMDate = datetime.today()
        IntellectualPropertyAgreement = request.form.get('IntellectualPropertyAgreement')
        if IntellectualPropertyAgreement == 'N' or IntellectualPropertyAgreement == 'null':
            IntellectualPropertyAgreementDate = None
        else:
            IntellectualPropertyAgreementDate = request.form.get('IntellectualPropertyAgreementDate')
            if IntellectualPropertyAgreementDate == '':
                IntellectualPropertyAgreementDate = datetime.today()
        ThesisProposalSeminar = request.form.get('ThesisProposalSeminar')
        if ThesisProposalSeminar == 'N' or ThesisProposalSeminar == 'null':
            ThesisProposalSeminarDate = None
        else:
            ThesisProposalSeminarDate = request.form.get('ThesisProposalSeminarDate')
            if ThesisProposalSeminarDate == '':
                ThesisProposalSeminarDate = datetime.today()
        ProposalApproval = request.form.get('ProposalApproval')
        if ProposalApproval == 'N' or ProposalApproval == 'null':
            ProposalApprovalDate = None
        else:
            ProposalApprovalDate = request.form.get('ProposalApprovalDate')
            if ProposalApprovalDate == '':
                ProposalApprovalDate = datetime.today()
        PGConference = request.form.get('PGConference')
        if PGConference == 'N' or PGConference == 'null':
            PGConferenceDate = None
        else:
            PGConferenceDate = request.form.get('PGConferenceDate')
            if PGConferenceDate == '':
                PGConferenceDate = datetime.today()
        ResultsSeminar = request.form.get('ResultsSeminar')
        if ResultsSeminar == 'N' or ResultsSeminar == 'null':
            ResultsSeminarDate = None
        else:
            ResultsSeminarDate = request.form.get('ResultsSeminarDate')
            if ResultsSeminarDate == '':
                ResultsSeminarDate = datetime.today()
        cur = getCursor()
        cur.execute ("update Milestones set \
        InductionProgramme=%s, InductionProgrammeDate=%s,\
            MutualExpectationAgreement=%s, MutualExpectationAgreementDate=%s,\
            KMRM=%s, KMRMDate=%s , IntellectualPropertyAgreement=%s, \
            IntellectualPropertyAgreementDate=%s, ThesisProposalSeminar=%s,\
            ThesisProposalSeminarDate=%s, ProposalApproval=%s, \
            ProposalApprovalDate=%s, PGConference=%s, PGConferenceDate=%s,\
            ResultsSeminar=%s, ResultsSeminarDate=%s where uid =%s",(InductionProgramme, 
            InductionProgrammeDate,MutualExpectationAgreement,MutualExpectationAgreementDate,KMRM,KMRMDate,
            IntellectualPropertyAgreement,IntellectualPropertyAgreementDate,ThesisProposalSeminar,ThesisProposalSeminarDate,
            ProposalApproval,ProposalApprovalDate,PGConference,PGConferenceDate,ResultsSeminar,ResultsSeminarDate,str(uid)))
        
        if submit_type == 'Next':
            return redirect(f'/section_b2/edit?report={reportid}')
        elif submit_type == 'Save & Exit':
            return redirect(f'/student') ###########################Needs to add student id once ready
        elif submit_type == 'Previous': 
            return redirect(f"/section_a/edit?report={reportid}")


@app.route('/section_b2/edit', methods=['GET', 'POST'])
@login_required
@restricted_access_student
def studentSectionB2():
    cur = getCursor()
    username = user_name()
    if request.method == 'GET':
        report_id = request.args.get('report')
        cur.execute(f"select * from milestones where reportid = {report_id}")
        select_result = cur.fetchall()
        print(select_result)
        return render_template(f'section_B2.html', select_result = select_result, report_id=report_id, 
        user_name = username, user_role = session['role'], user_action = 'edit')
    else:
        report_id = request.form.get('reportid')
        submit_type = request.form.get('submit')
        uid = request.form.get('uid')
        HumanEthicsApproval = request.form.get('HumanEthicsApproval')
        HealthSafetyApproval = request.form.get('HealthSafetyApproval')
        AnimalEthicsApproval = request.form.get('AnimalEthicsApproval')
        BiologicalSafetyApproval = request.form.get('BiologicalSafetyApproval')
        RadiationProtectionApproval = request.form.get('RadiationProtectionApproval')
        cur.execute (f"update Milestones set \
        HumanEthicsApproval='{HumanEthicsApproval}', HealthSafetyApproval='{HealthSafetyApproval}',\
            AnimalEthicsApproval='{AnimalEthicsApproval}', BiologicalSafetyApproval='{BiologicalSafetyApproval}',\
            RadiationProtectionApproval='{RadiationProtectionApproval}' \
            where uid = {uid}")
        if submit_type == 'Previous':
            return redirect(f'/section_b1/edit?report={report_id}')
        elif submit_type == 'Save & Exit':
            return redirect(f'/student') ###########################Needs to add student id once ready
        else: 
            return redirect(f'/section_c/edit?report={report_id}')



##########################################################################################
##########################################################################################
######################################## Section C ###################################
##########################################################################################
##########################################################################################

#Section C Evaluation
@app.route('/section_c/edit', methods=['GET', 'POST'])
@login_required
@restricted_access_student
def evaluate_supervisor():
    cur = getCursor()
    if request.method == 'GET':
        username = user_name()
        report_id = request.args.get('report')
        #student_user_id = request.args.get('student')
        cur.execute(f"SELECT * FROM evaluation\
            WHERE reportid = {report_id}")
        result = cur.fetchone()
        evaluation_form = result[3:-3]
        question_id = result[2]
        # Pass in ratings and comments as lists
        ratings = []
        comments = []
        rating_options = []
        for i in range(len(evaluation_form)):
            if i%2 == 0:
                ratings.append(evaluation_form[i])
                options = ['VeryGood', 'Good', 'Neutral', 'Unsatisfactory', 'VeryUnsatisfactory', 'N/A']


                try:
                    options.remove(evaluation_form[i])
                    rating_options.append(options)
                except ValueError:
                    rating_options.append(options)
            else:
                comments.append(evaluation_form[i])
        
        rating_names = ['AccessPrincipalSupervisor',
        'AccesssAssociateSupervisor',
        'ExpertisePrincipalSupervisor',
        'ExpertiseAssociateSupervisor',
        'FeedbackQualityPrincipalSupervisor',
        'FeedbackQualityAssociateSupervisor',
        'TimelinessPrincipalSupervisor',
        'TimelinessAssociateSupervisor',
        'CourseAvailability',
        'Workspace',
        'ComputerFacility',
        'ITSupport',
        'ResearchSoftware',
        'Library',
        'LearningSupport',
        'StatSupport',
        'ResearchEquipment',
        'TechSupport',
        'FinancialSupport',
        'Other']

        comment_names = [
       'accessprincipalsupervisorcomment',
       'accesssassociatesupervisorcomment',
       'expertiseprincipalsupervisorcomment',
       'expertiseassociatesupervisorcomment',
       'feedbackqualityprincipalsupervisorcomment',
       'feedbackqualityassociatesupervisorcomment',
       'timelinessprincipalsupervisorcomment',
       'timelinessassociatesupervisorcomment',
       'courseavailabilitycomment',
       'workspacecomment',
       'computerfacilitycomment',
       'itsupportcomment',
       'researchsoftwarecomment',
       'librarycomment',
       'learningsupportcomment',
       'statsupportcomment',
       'researchequipmentcomment',
       'techsupportcomment',
       'financialsupportcomment',
       'othercomment']

        #Meeting frequency
        meeting_freq = result[-3]
        print(meeting_freq)
        meeting_freq_options = ['Weekly', 'Fornightly', 'Monthly', '3 Monthly', '6 Monthly', 'Never']
        try:
            meeting_freq_options.remove(meeting_freq) #Prioritise selected value in the dropdown
        except Exception:
            pass

        #Waiting period for feedback
        waitperiod = result[-2]
        waitperiod_options = ['1 Week', '2 Weeks', '1 Month', '3 Months']
        try:
            waitperiod_options.remove(waitperiod)
        except Exception:
            pass

        #Feedback method
        feedback_method = result[-1]
        feedback_options = ['Softcopy', 'Comments on submitted material', 'Verbally', 'On a separate letter']
        try:
            feedback_options.remove(feedback_method)
        except Exception:
            pass

        return render_template('section_C.html', data_pack = zip(ratings, rating_options, rating_names, 
        comments, comment_names), report_id = report_id, meeting_freq = meeting_freq, meeting_freq_options = meeting_freq_options,
        feedback_method = feedback_method, feedback_options = feedback_options,
        waitperiod = waitperiod, waitperiod_options = waitperiod_options, question_id = question_id,
        viewer_id = session['id'], viewer_role = session['role'], action = 'edit', user_name = username, user_role = session['role'], user_action = 'edit')


    else:
        # Process POST request and write to database
        values = request.form.items()
        report_id = request.form.get('reportid')
        question_id = request.form.get('questionid')
        submit_type = request.form.get('submit')
        for k,v in values:
            if k not in ['reportid', 'questionid', 'submit'] :
                cur.execute(f"UPDATE evaluation\
                    SET {k} = '{v}' \
                    WHERE reportid = {report_id};\
                    UPDATE questionstatus\
                    SET status = 'Complete'\
                    WHERE reportid = {report_id} AND questionid = {question_id}")

        last_update(report_id, 'Incomplete')
        update_question_status(report_id, 1)

        if submit_type == 'Previous':
            return redirect(f'/section_b1/edit?report={report_id}')
        elif submit_type == 'Save & Exit':
            return redirect(f'/student') ###########################Needs to add student id once ready
        else: 
            return redirect(f'/section_d1/edit?report={report_id}')
        #return redirect(f"/create/c?report={report_id}&student={session['id']}")


##########################################################################################
##########################################################################################
######################################## Section D ###################################
##########################################################################################
##########################################################################################

@app.route("/section_d1/edit",methods = ["GET","POST"]) 
@login_required
@restricted_access_student
def section_D1():
    cur = getCursor()
    #if session['role'] != 'Student':
    #    return redirect('/')
    if request.method == "GET": 
        #try:
        report_id = request.args.get('report')
        #global SectionD --disabled as this will not work if a student starts from section d2 (e.g. when they return to draft)
        SectionD = SecD(report_id)
        SectionD.form1()
        username = user_name()
        return render_template('section_D1.html',D1Data = SectionD.databaseForm, 
        rowName=SectionD.rowName,rowNumber=SectionD.totalRow, report_id = report_id, user_name = username, user_role = session['role'], user_action = 'edit')

        #except Exception as err:
        #    return redirect('/')

    else:
        report_id = request.form.get("reportid")   
        submit_type = request.form.get('submit') 
        SectionD = SecD(report_id)
        SectionD.form1()
        #print(SectionD.totalRow)   
        for eachRow in range(SectionD.totalRow):
            print('row', SectionD.reportID,SectionD.uid[eachRow][0])
            cur.execute(f"update currentobjective set completionstatus='{SectionD.formInfo[eachRow*2]}',\
                    reasonforchange='{SectionD.formInfo[eachRow*2+1]}' where reportid ={report_id} \
                    and uid ={SectionD.uid[eachRow][0]};\
                    UPDATE questionstatus SET status = 'Complete' WHERE reportid={report_id} AND questionid ={SectionD.questionid};\
                    UPDATE report SET lastupdatedate = CURRENT_TIMESTAMP WHERE reportid = {report_id}")
        #flash("Saved")
        if submit_type == 'Previous':
            return redirect(f'/section_c/edit?report={report_id}')
        elif submit_type == 'Save & Exit':
            return redirect(f'/student') ###########################Needs to add student id once ready
        else: 
            return redirect(f'/section_d2/edit?report={report_id}')



@app.route("/section_d2/edit",methods = ["GET","POST"])
@login_required
@restricted_access_student
def section_D2():
    cur = getCursor()
    #if session['role'] != 'Student':
    #    return redirect('/')
    if request.method == 'GET':
        #try:
        report_id = request.args.get('report')
        SectionD = SecD(report_id)
        SectionD.form2()
        username = user_name()
        #except Exception as err:
         #   return redirect('/')    
        return render_template('section_D2.html', D2data = zip(SectionD.uid, SectionD.databaseForm),
        rowName=SectionD.rowName,rowNumber=SectionD.totalRow, report_id=report_id, user_name = username, user_role = session['role'], user_action = 'edit')

    else:

        report_id = request.form.get("reportid")   
        submit_type = request.form.get('submit') 
        covideffect = request.form.getlist('covideffect[]')
        comment_ids = request.form.getlist('id[]')

        SectionD = SecD(report_id)
        SectionD.form2()

        #if 'prev' in request.form:
        #    return redirect(url_for(".section_D1"))
        #if 'next' in request.form:
        #    return redirect(url_for(".section_D3"))
        for a,b in zip(covideffect, comment_ids):
            cur.execute(f"update covideffect set comment ='{a}' where uid = {b}")
        #flash("Saved")

        if submit_type == 'Previous':
            return redirect(f'/section_d1/edit?report={report_id}')
        elif submit_type == 'Save & Exit':
            return redirect(f'/student') ###########################Needs to add student id once ready
        elif submit_type == 'Next': 
            return redirect(f'/section_d3/edit?report={report_id}')
        elif submit_type == 'add':
            cur.execute("insert into covideffect (uid,reportid) values(default, %s)"%(SectionD.reportID))
            return redirect(f'/section_d2/edit?report={report_id}')
        else:
            cur.execute(f"DELETE FROM covideffect WHERE uid={submit_type}")
            return redirect(f'/section_d2/edit?report={report_id}')




@app.route("/section_d3/edit",methods = ["GET","POST"]) 
@login_required
@restricted_access_student

def section_D3():
    #cur = dbconn
    #if session['role'] != 'Student':
    #    return redirect('/')
    #try:
    #except Exception as err:
    #        return redirect('/')
    cur = getCursor()

    if request.method == "POST":
        report_id = request.form.get("reportid")   
        submit_type = request.form.get('submit') 
        achievement = request.form.getlist('achievements[]')
        comment_ids = request.form.getlist('id[]')

        SectionD = SecD(report_id)
        SectionD.form3()

        #if 'prev' in request.form:
        #    return redirect(url_for(".section_D1"))
        #if 'next' in request.form:
        #    return redirect(url_for(".section_D3"))
        for a,b in zip(achievement, comment_ids):
            cur.execute(f"update academicachievement set comment ='{a}' where uid = {b}")
        #flash("Saved")

        if submit_type == 'Previous':
            return redirect(f'/section_d2/edit?report={report_id}')
        elif submit_type == 'Save & Exit':
            return redirect(f'/student') ###########################Needs to add student id once ready
        elif submit_type == 'Next': 
            return redirect(f'/section_d4/edit?report={report_id}')
        elif submit_type == 'add':
            cur.execute(f"insert into academicachievement (uid,reportid) values(default, {report_id})")
            return redirect(f'/section_d3/edit?report={report_id}')
        else:
            cur.execute(f"DELETE FROM academicachievement WHERE uid={submit_type}")
            return redirect(f'/section_d3/edit?report={report_id}')

    else:
        report_id = request.args.get('report')
        SectionD = SecD(report_id)
        SectionD.form3()
        username = user_name()
        return render_template('section_D3.html', report_id = report_id,
         D3data = zip(SectionD.uid, SectionD.databaseForm),rowName=SectionD.rowName,rowNumber=SectionD.totalRow, user_name = username, user_role = session['role'], user_action = 'edit')


@app.route("/section_d4/edit",methods = ["GET","POST"]) 
@login_required
@restricted_access_student

def section_D4():
    cur = getCursor()

    #cur = dbconn
    #print(session['role'])
    #if session['role'] != 'Student':
    #    return redirect('/')
    #try:
    #    SectionD.form4()
    #except Exception as err:
    #        return redirect('/')
    if request.method == "POST":
        report_id = request.form.get("reportid")   
        submit_type = request.form.get('submit') 
        titles = request.form.getlist('title[]')
        duedates = request.form.getlist('duedate[]')
        comments = request.form.getlist('comment[]')
        comment_ids = request.form.getlist('id[]')
        SectionD = SecD(report_id)
        SectionD.form4()

        for t, d, c, i in zip(titles, duedates, comments, comment_ids):
            if d=="":
                cur.execute(f"update futureobjective set title = '{t}',duedate=null, comment='{c}'where reportid = {report_id} and uid = {i}")
            else:
                cur.execute(f"update futureobjective set title = '{t}',duedate='{d}',comment='{c}'where reportid = {report_id} and uid = {i}")


        if submit_type == 'Previous':
            return redirect(f'/section_d3/edit?report={report_id}')
        elif submit_type == 'Save & Exit':
            return redirect(f'/student') ###########################Needs to add student id once ready
        elif submit_type == 'Next': 
            return redirect(f'/section_d5/edit?report={report_id}')
        elif submit_type == 'add':
            cur.execute(f"insert into futureobjective (uid,reportid) values(default, {report_id})")
            return redirect(f'/section_d4/edit?report={report_id}')
        else:
            cur.execute(f"DELETE FROM futureobjective WHERE uid={submit_type}")
            return redirect(f'/section_d4/edit?report={report_id}')

    else:
        report_id = request.args.get('report')
        SectionD = SecD(report_id)
        SectionD.form4()
        username = user_name()
        return render_template('section_D4.html', report_id = report_id,
         D4data = zip(SectionD.uid, SectionD.databaseForm),rowName=SectionD.rowName,rowNumber=SectionD.totalRow, user_name = username, user_role = session['role'], user_action = 'edit')

        #if 'prev' in request.form:
        #    return redirect(url_for(".section_D3"))
        #if 'next' in request.form:
        #    return redirect(url_for(".section_D5"))
        #if 'add' in request.form:
        #    cur.execute("insert into futureobjective (uid,reportid) values(default, %s)"%(SectionD.reportID))
        #    return redirect(url_for(".section_D4"))
        #if 'del' in request.form:
        #    row = request.form['del']
        #    cur.execute("DELETE FROM futureobjective WHERE uid=%s"%(SectionD.uid[int(row)][0]))
        #    return redirect(url_for(".section_D4"))       
        #for aa in range(SectionD.totalRow):
        #    if SectionD.formInfo[aa*3+1]=="":
        #        cur.execute("update futureobjective set title = '%s',duedate=null, comment='%s'where reportid = %s and uid = %s"%(SectionD.formInfo[aa*3],SectionD.formInfo[aa*3+2],SectionD.reportID,SectionD.uid[aa][0]))
        #    else:
        #        cur.execute("update futureobjective set title = '%s',duedate='%s',comment='%s'where reportid = %s and uid = %s"%(SectionD.formInfo[aa*3],SectionD.formInfo[aa*3+1],SectionD.formInfo[aa*3+2],SectionD.reportID,SectionD.uid[aa][0]))
        #flash("Saved")
        #return redirect(url_for(".section_D4"))
    #else:
    #    return render_template('section_D4.html',D4Data = SectionD.databaseForm, rowName=SectionD.rowName,rowNumber=SectionD.totalRow)


@app.route("/section_d5/edit",methods = ["GET","POST"]) 
@login_required
@restricted_access_student
def section_D5():
    cur = getCursor()
#    cur = dbconn
#    if session['role'] != 'Student':
#        return redirect('/')
#    try:
#        SectionD.form5()
#    except Exception as err:
#            return redirect('/')

    if request.method == "POST":
        report_id = request.form.get("reportid")   
        submit_type = request.form.get('submit') 
        titles = request.form.getlist('title[]')
        amounts = request.form.getlist('amount[]')
        comments = request.form.getlist('comment[]')
        comment_ids = request.form.getlist('id[]')
        SectionD = SecD(report_id)
        SectionD.form5()

        for t, a, c, i in zip(titles, amounts, comments, comment_ids):
            if a=="":
                cur.execute(f"update expenditure set title = '{t}',amount=null, comment='{c}'where reportid = {report_id} and uid = {i}")
            else:
                cur.execute(f"update expenditure set title = '{t}',amount='{a}',comment='{c}'where reportid = {report_id} and uid = {i}")


        if submit_type == 'Previous':
            return redirect(f'/section_d4/edit?report={report_id}')
        elif submit_type == 'Save & Exit':
            return redirect(f'/student') ###########################Needs to add student id once ready
        elif submit_type == 'Next': 
            if session['role'] == 'Admin':
                return redirect(f'/section_e/edit?report={report_id}')
            else:
                return redirect(f'/section_f/edit?report={report_id}')
        elif submit_type == 'add':
            cur.execute(f"insert into expenditure (uid,reportid) values(default, {report_id})")
            return redirect(f'/section_d5/edit?report={report_id}')
        else:
            cur.execute(f"DELETE FROM expenditure WHERE uid={submit_type}")
            return redirect(f'/section_d5/edit?report={report_id}')


        #if 'prev' in request.form:
        #    return redirect(url_for(".section_D4"))
        #if 'add' in request.form:
        #    cur.execute("insert into expenditure (uid,reportid) values(default, %s)"%(SectionD.reportID))
        #    return redirect(url_for(".section_D5"))
        #if 'del' in request.form:
        #    row = request.form['del']
        #    cur.execute("DELETE FROM expenditure WHERE uid=%s"%(SectionD.uid[int(row)][0]))
        #    return redirect(url_for(".section_D5"))
        #for aa in range(SectionD.totalRow):
        #    if SectionD.formInfo[aa*3+1]:
        #        cur.execute("update expenditure set title='%s',amount='%s', comment='%s'where reportid = %s and uid = %s"%(SectionD.formInfo[aa*3],SectionD.formInfo[aa*3+1],SectionD.formInfo[aa*3+2],SectionD.reportID,SectionD.uid[aa][0]))
        #    else:
        #        cur.execute("update expenditure set title='%s', amount=null,comment='%s'where reportid = %s and uid = %s"%(SectionD.formInfo[aa*3],SectionD.formInfo[aa*3+2],SectionD.reportID,SectionD.uid[aa][0]))
#
        #flash("Saved")
        #return redirect(url_for(".section_D5"))
    else:
        report_id = request.args.get('report')
        SectionD = SecD(report_id)
        SectionD.form5()
        username = user_name()
        total = 0
        for each in SectionD.databaseForm:
            if each[1]:
                total =total +float(each[1])
        print(total)
        
        return render_template('section_D5.html',report_id = report_id, total = total,
        D5data = zip(SectionD.uid, SectionD.databaseForm), rowName=SectionD.rowName,rowNumber=SectionD.totalRow, user_name = username, user_role = session['role'])




##########################################################################################
##########################################################################################
######################################## Section E ###################################
##########################################################################################
##########################################################################################

@app.route('/section_e/edit', methods = ['GET','POST'])
@login_required
@restricted_access_staff

def section_E():
    editor_id  = session['id']
    editor_role = session['role']
    cur = getCursor()
    if request.method == "POST":
        form_data = request.form
        print('form', form_data)
        submit_type = request.form.get('submit')
        report_id = request.form.get('reportid') 
        print("reportid",report_id)
        # for k in form_data:
        #     if form_data[k] == '':
        #         form_data[k] == None
        print('form', form_data)
        print("                                  debugging")
        try:
            if form_data['uid']:
                cur.execute(f"UPDATE assessmentbysupervisor\
                    SET sixmonthprogress = {form_data['answer1']},\
                    phdprogress = {form_data['answer2']},\
                    academicqaulity = {form_data['answer3']},\
                    technicalskills = {form_data['answer4']},\
                    likelytoachieveobjectives = {form_data['answer5']},\
                    recommendationcarriedout = {form_data['answer6']},\
                    comments = '{form_data['answer7']}'\
                    WHERE uid = {form_data['uid']}")
                uid = form_data['uid']
        except Exception:
            print('working')
            cur.execute(f"UPDATE assessmentbyconvenor\
                SET areaofconsideration = '{form_data['convenor_comment']}',\
                rating = '{form_data['convenor_rating']}',\
                submissiondate = CURRENT_TIMESTAMP\
                WHERE uid = {form_data['convenor_uid']}")
            uid = form_data['convenor_uid']

        
        if submit_type == 'Finish':
            return redirect(f'/section_e/edit/submit?report={report_id}&uid={uid}')
        elif submit_type == 'Save & Exit':
            if session['role'] == 'Convenor':
                return redirect(f'/convenor/pending&report?view=pending') ###########################Needs to add student id once ready
            elif session['role'] == 'Professor':
                return redirect(f'/supervisor/pending&report?view=pending') ###########################Needs to add student id once ready
            else:
                return redirect(f'/admin') ###########################Needs to add student id once ready
        elif submit_type == 'Confirm':#confirm change when admin makes changes. Refreshes the page
            return redirect(f'/section_e/edit?report={report_id}') 
        else:
            return redirect(f'/section_f/edit?report={report_id}')


    else:
        report_id = request.args.get('report')
        editor_role = request.args.get('editor')
        cur.execute(f"select a.uid, a.supervisoruserid, a.sixmonthprogress,a.phdprogress,a.academicqaulity,\
            a.technicalskills,a.likelytoachieveobjectives,a.recommendationcarriedout, a.comments, \
            s.firstname, s.lastname, t.supervisorrole\
            from assessmentbysupervisor a \
            LEFT JOIN staff s\
            ON a.supervisoruserid = s.userid\
                AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
            LEFT JOIN report r\
            ON r.reportid = a.reportid\
            LEFT JOIN thesis th\
            ON th.thesisid = r.thesisid\
            AND CURRENT_TIMESTAMP BETWEEN th.validfromdate AND th.validtodate\
            LEFT JOIN supervisionteam t\
            ON t.supervisoruserid = s.userid\
                AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
                AND t.studentuserid = th.studentuserid \
            WHERE a.reportid = {report_id}\
            ORDER BY CASE WHEN t.supervisorrole LIKE 'Supervisor' THEN 0\
                WHEN t.supervisorrole LIKE 'Associate' THEN 1\
                ELSE 2 END ASC")
        supervisor_feedback = cur.fetchall()
        cur.execute(f"SELECT a.uid, a.convenoruserid, a.areaofconsideration, a.rating, s.firstname, s.lastname\
                FROM assessmentbyconvenor a\
                LEFT JOIN staff s\
                ON a.convenoruserid = s.userid\
                AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
                WHERE a.reportid = {report_id}")
        convenor_feedback = cur.fetchone()
        print("TEST",supervisor_feedback, editor_id, editor_role)
        username = user_name()
        if editor_role == 'supervisor':
            sectionA_data = print_sectionA(report_id)
            sectionA = sectionA_data[0]
            supervisionTeam = sectionA_data[1]
            scholarships = sectionA_data[2]
            employment = sectionA_data[3]
            sectionB = print_sectionB(report_id)
            sectionC = print_sectionC(report_id)
            sectionD = print_sectionD(report_id)
            # supervisor_feedback, 
            # convenor_feedback= print_sectionE(report_id)
            sectionF = print_sectionF(report_id)
            print(supervisor_feedback)
            return render_template('supervisor_report.html',supervisor_feedback = supervisor_feedback,
            convenor_feedback = convenor_feedback, report_id=report_id, editor_id = editor_id, editor_role = editor_role,
            sectionA=sectionA,sectionB=sectionB,
            sectionC=sectionC,sectionD=sectionD, sectionF=sectionF,
            # supervisor_feedback = supervisor_feedback,
            supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment,
            user_name = username, user_role = session['role'], user_action = 'edit')
        else:
            return render_template('section_E.html',supervisor_feedback = supervisor_feedback,
            convenor_feedback = convenor_feedback, report_id=report_id, editor_id = editor_id, editor_role = editor_role,
            user_name = username, user_role = session['role'], user_action = 'edit')



@app.route('/section_e/edit/submit', methods = ['GET', 'POST'])
@login_required
@restricted_access_staff
def submit_sectionE():
    cur = getCursor()
    if request.method == 'GET':
        report_id = request.args.get('report')
        uid = request.args.get('uid')
        sectionE = print_sectionE(report_id)
        username = user_name()
        print(session['role'])

        if session['role'] == 'Professor':
            supervisor_feedback = sectionE[0]
            print(supervisor_feedback, uid)
            return render_template('view_report.html',report_id = report_id, uid = uid, 
            supervisor_feedback = supervisor_feedback, action='edit', user_name = username, user_role = session['role'], user_action = 'edit')
        elif session['role'] == 'Convenor':
            convenor_feedback = sectionE[1]
            return render_template('view_report.html',report_id = report_id, uid = uid,convenor_feedback=convenor_feedback, action='edit',user_name=username,user_role=session['role'], user_action = 'edit')
    else:
        report_id = request.form.get('reportid')
        uid = request.form.get('uid')
        if session['role'] == 'Professor':
            cur.execute(f'UPDATE assessmentbysupervisor SET submissiondate = CURRENT_TIMESTAMP WHERE uid = {uid}')
            return redirect('/supervisor/pending&report?view=pending')
        elif session['role'] == 'Convenor':
            cur.execute(f'UPDATE assessmentbyconvenor SET submissiondate = CURRENT_TIMESTAMP WHERE uid = {uid}')
            return redirect('/convenor/pending&report?view=pending')



##########################################################################################
##########################################################################################
######################################## Section F ###################################
##########################################################################################
##########################################################################################

@app.route("/section_f/edit", methods = ["GET","POST"])
@login_required
@restricted_access_student
def section_f():
    cur = getCursor()
    if request.method == 'GET':
        report_id = request.args.get('report')
        cur.execute(f"SELECT abs.reportid, CONCAT(s.firstname, ' ', s.lastname) AS name, comments, s.userid, s.position, s.email\
            FROM assessmentbystudent abs\
            LEFT JOIN staff s\
            ON abs.talkinpersonuserid = s.userid\
            WHERE reportid = {report_id}")
        abs_result = cur.fetchone()
        print("F", abs_result)
        cur.execute(f"SELECT st.userid, CONCAT(st.firstname, ' ', st.lastname) AS name, st.position, st.email \
            FROM report r\
            LEFT JOIN thesis t\
            ON r.thesisid = t.thesisid\
            LEFT JOIN students s\
            ON t.studentuserid = s.userid\
            INNER JOIN staff st\
            ON st.department = s.department\
            AND st.position LIKE '%Chair%' OR st.position LIKE '%Convenor%'\
            WHERE r.reportid = {report_id}")
        talk_to_staff = cur.fetchall()
        print('F-talk to', talk_to_staff)
        username = user_name()
        return render_template('section_F.html', abs_result = abs_result, talk_to_staff = talk_to_staff, report_id = report_id,
        user_name = username, user_role = session['role'], user_action = 'edit')

    else:
        comment = request.form.get('comments')
        talkinpersonuserid = request.form.get('talkinpersonuserid')
        report_id = request.form.get('reportid')
        submit_type = request.form.get('submit')

        cur.execute(f"SELECT st.userid, st.email\
            FROM report r\
            LEFT JOIN thesis t\
            ON r.thesisid = t.thesisid\
            LEFT JOIN students s\
            ON t.studentuserid = s.userid\
            INNER JOIN staff st\
            ON st.department = s.department\
            AND st.position LIKE '%Admin%'\
            WHERE r.reportid = {report_id}")
        sentto = cur.fetchone()
        sentto = 1 #sentto[0]


        cur.execute(f"SELECT * FROM assessmentbystudent WHERE reportid = {report_id}")
        result = cur.fetchone()
        if result:
            if talkinpersonuserid:
                cur.execute(f"UPDATE assessmentbystudent \
                    SET comments = '{comment}', \
                        talkinpersonuserid = {talkinpersonuserid}, \
                        senttouserid = {sentto}\
                    WHERE reportid = {report_id}")
            else:
                cur.execute(f"UPDATE assessmentbystudent \
                    SET comments = '{comment}', \
                        senttouserid = {sentto}\
                    WHERE reportid = {report_id}")

        else:
            if talkinpersonuserid == '':
                talkinpersonuserid = 'NULL'
            cur.execute(f"INSERT INTO assessmentbystudent (reportid, comments, talkinpersonuserid, senttouserid)\
                VALUES ({report_id}, '{comment}', {talkinpersonuserid}, {sentto})")
        print('subit_type', submit_type)
        if submit_type == 'Finish':
            cur.execute(f"UPDATE assessmentbystudent \
                SET submissiondate = CURRENT_TIMESTAMP \
                WHERE reportid = {report_id};")
            return redirect(f'/section_abcdf/edit/submit?report={report_id}')  
        elif submit_type == 'Previous':
            if session['role'] == 'Student':
                return redirect(f'/section_d5/edit?report={report_id}')
            else:
                return redirect(f'/section_e/edit?report={report_id}')
        elif submit_type == 'Save & Exit':
            return redirect('/student')
        else:
            return redirect(f'/section_abcdf/edit/submit?report={report_id}')


























































































































































































































































































































































##################################################################################################
        

# #ORIGINAL#################################################################################################
# @app.route('/section_b1/edit', methods=['GET', 'POST'])
# @login_required
# @restricted_access_student
# def studentSectionB1():
#     if request.method == 'GET':
#         cur = getCursor()
#         report_id = request.args.get('report')
#         cur.execute(f"select * from milestones where reportid = {report_id}")
#         select_result = cur.fetchall()
#         print(select_result)
#         username = user_name()
#         return render_template('section_B1.html', select_result = select_result, report_id = report_id, user_name = username, user_role = session['role'], user_action = 'edit')
#     else:
#         uid = request.form.get('uid')
#         reportid = request.form.get('reportid')
#         questionid = request.form.get('questionid')
#         submit_type = request.form.get('submit')
#         InductionProgramme = request.form.get('InductionProgramme')
#         if InductionProgramme == 'N' or InductionProgramme == 'null':
#             InductionProgrammeDate = None
#         else:
#             InductionProgrammeDate = request.form.get('InductionProgrammeDate')
#             if InductionProgrammeDate == '':
#                 InductionProgrammeDate = datetime.today()
        
#         MutualExpectationAgreement = request.form.get('MutualExpectationAgreement')
#         if MutualExpectationAgreement == 'N' or MutualExpectationAgreement == 'null':
#             MutualExpectationAgreementDate = None
#         else:
#             MutualExpectationAgreementDate = request.form.get('MutualExpectationAgreementDate')
#             if MutualExpectationAgreementDate == '':
#                 MutualExpectationAgreementDate = datetime.today()
        
#         KMRM = request.form.get('KMRM')
#         if KMRM == 'N' or KMRM == 'null':
#             KMRMDate = None
#         else:
#             KMRMDate = request.form.get('KMRMDate')
#             if KMRMDate == '':
#                 KMRMDate = datetime.today()

#         IntellectualPropertyAgreement = request.form.get('IntellectualPropertyAgreement')
#         if IntellectualPropertyAgreement == 'N' or IntellectualPropertyAgreement == 'null':
#             IntellectualPropertyAgreementDate = None
#         else:
#             IntellectualPropertyAgreementDate = request.form.get('IntellectualPropertyAgreementDate')
#             if IntellectualPropertyAgreementDate == '':
#                 IntellectualPropertyAgreementDate = datetime.today()

#         ThesisProposalSeminar = request.form.get('ThesisProposalSeminar')
#         if ThesisProposalSeminar == 'N' or ThesisProposalSeminar == 'null':
#             ThesisProposalSeminarDate = None
#         else:
#             ThesisProposalSeminarDate = request.form.get('ThesisProposalSeminarDate')
#             if ThesisProposalSeminarDate == '':
#                 ThesisProposalSeminarDate = datetime.today()

#         ProposalApproval = request.form.get('ProposalApproval')
#         if ProposalApproval == 'N' or ProposalApproval == 'null':
#             ProposalApprovalDate = None
#         else:
#             ProposalApprovalDate = request.form.get('ProposalApprovalDate')
#             if ProposalApprovalDate == '':
#                 ProposalApprovalDate = datetime.today()

#         PGConference = request.form.get('PGConference')
#         if PGConference == 'N' or PGConference == 'null':
#             PGConferenceDate = None
#         else:
#             PGConferenceDate = request.form.get('PGConferenceDate')
#             if PGConferenceDate == '':
#                 PGConferenceDate = datetime.today()

#         ResultsSeminar = request.form.get('ResultsSeminar')
#         if ResultsSeminar == 'N' or ResultsSeminar == 'null':
#             ResultsSeminarDate = None
#         else:
#             ResultsSeminarDate = request.form.get('ResultsSeminarDate')
#             if ResultsSeminarDate == '':
#                 ResultsSeminarDate = datetime.today()

#         cur = getCursor()
#         cur.execute ("update Milestones set \
#         InductionProgramme=%s, InductionProgrammeDate=%s,\
#             MutualExpectationAgreement=%s, MutualExpectationAgreementDate=%s,\
#             KMRM=%s, KMRMDate=%s , IntellectualPropertyAgreement=%s, \
#             IntellectualPropertyAgreementDate=%s, ThesisProposalSeminar=%s,\
#             ThesisProposalSeminarDate=%s, ProposalApproval=%s, \
#             ProposalApprovalDate=%s, PGConference=%s, PGConferenceDate=%s,\
#             ResultsSeminar=%s, ResultsSeminarDate=%s where uid =%s",(InductionProgramme, 
#             InductionProgrammeDate,MutualExpectationAgreement,MutualExpectationAgreementDate,KMRM,KMRMDate,
#             IntellectualPropertyAgreement,IntellectualPropertyAgreementDate,ThesisProposalSeminar,ThesisProposalSeminarDate,
#             ProposalApproval,ProposalApprovalDate,PGConference,PGConferenceDate,ResultsSeminar,ResultsSeminarDate,str(uid)))
        
#         if submit_type == 'Next':
#             return redirect(f'/section_b2/edit?report={reportid}')
#         elif submit_type == 'Save & Exit':
#             return redirect(f'/student') ###########################Needs to add student id once ready
#         else: 
#             return redirect(f"/section_a/edit?report={reportid}")


# @app.route('/section_b2/edit', methods=['GET', 'POST'])
# @login_required
# @restricted_access_student
# def studentSectionB2():
#     cur = getCursor()
#     username = user_name()
#     if request.method == 'GET':
#         report_id = request.args.get('report')
#         cur.execute("select * from milestones where reportid = 1")
#         select_result = cur.fetchall()
#         print(select_result)
#         return render_template(f'section_B2.html', select_result = select_result, report_id=report_id, user_name = username, user_role = session['role'], user_action = 'edit')
#     else:
#         report_id = request.form.get('reportid')
#         submit_type = request.form.get('submit')
#         uid = request.form.get('uid')
#         HumanEthicsApproval = request.form.get('HumanEthicsApproval')
#         HealthSafetyApproval = request.form.get('HealthSafetyApproval')
#         AnimalEthicsApproval = request.form.get('AnimalEthicsApproval')
#         BiologicalSafetyApproval = request.form.get('BiologicalSafetyApproval')
#         RadiationProtectionApproval = request.form.get('RadiationProtectionApproval')
#         cur.execute (f"update Milestones set \
#         HumanEthicsApproval='{HumanEthicsApproval}', HealthSafetyApproval='{HealthSafetyApproval}',\
#             AnimalEthicsApproval='{AnimalEthicsApproval}', BiologicalSafetyApproval='{BiologicalSafetyApproval}',\
#             RadiationProtectionApproval='{RadiationProtectionApproval}' \
#             where uid = {uid}")
#         if submit_type == 'Previous':
#             return redirect(f'/section_b1/edit?report={report_id}')
#         elif submit_type == 'Save & Exit':
#             return redirect(f'/student') ###########################Needs to add student id once ready
#         else: 
#             return redirect(f'/section_c/edit?report={report_id}')
        

# @app.route('/admin', methods = ['GET','POST'])
# @login_required
# def admin():
#     if request.method == 'GET':
#         username = user_name()
#         return render_template('Control_panel_admin.html', user_name = username, user_role = session['role'], user_action = 'na')
#     else:
#         today = date.today()
#         search = request.form.get('search')
#         cur = getConnection()
#         cur = cur.cursor()
#         cur.execute("select s.userid,concat(s.firstname, ' ', s.lastname) as name, r.reportid, t.thesistitle, r.reportstatus, r.duedate, s.department, \
#                     q.status as statusbyconvenor, q.status as statusbysupervisor \
#                     from (((((students as s inner join thesis as t on s.userid = t.studentuserid) \
#                     inner join report as r on t.thesisid = r.thesisid) \
#                     inner join questionstatus as q on r.reportid = q.reportid) \
#                     inner join assessmentbysupervisor as abs on abs.reportid = q.reportid) \
#                     inner join assessmentbyconvenor as abc on abc.reportid = q.reportid) \
#                     group by r.reportid, s.userid,t.thesistitle, r.reportstatus,s.firstname,s.lastname, r.duedate, s.department,statusbyconvenor,statusbysupervisor\
#                     order by r.duedate asc")
#         select_result = cur.fetchall()
#         cur.execute("select count(supervisoruserid), studentuserid from supervisionteam group by studentuserid;")
#         total_supervisor_result = cur.fetchall()
#         cur.execute("select * from assessmentbyadmin;")
#         lastupdatedate_admin = cur.fetchall()
#         cur.execute(f"select abs.reportid, t.studentuserid, q.status, abs.supervisoruserid, concat(sta.firstname, ' ', sta.lastname) as name \
#                         from ((((assessmentbysupervisor as abs inner join questionstatus as q on abs.reportid = q.reportid) \
#                         inner join report as r on q.reportid = r.reportid) \
#                         inner join thesis as t on r.thesisid = t.thesisid) \
#                         inner join staff as sta on sta.userid = abs.supervisoruserid) \
#                         where q.status = 'Incomplete' \
#                         group by abs.reportid,t.studentuserid,q.status,abs.supervisoruserid, name \
#                         order by abs.reportid;")
#         un_supervisor_result = cur.fetchall()
#         return render_template('Control_panel_admin.html', select_result = select_result, 
#         total_supervisor_result=total_supervisor_result,  un_supervisor_result=un_supervisor_result,search=search,today=today,lastupdatedate_admin=lastupdatedate_admin)



# @app.route('/notification', methods = ['GET','POST'])
# @login_required
# def Notification():
#     if request.method == 'GET':
#         if request.args.get('convenor') is None:
#             username = user_name()
#             student = request.args.get('student')
#             reportid = request.args.get('reportid')
#             cur = getConnection()
#             cur = cur.cursor()
#             cur.execute(f"select luemail, personalemail from students where userid = {student};")
#             student_email = cur.fetchall()
#             for i in student_email:
#                 student_email_list=i
# #######################################################################
#             cur.execute(f"select staff.email \
#                         from ((students inner join supervisionteam on students.userid = supervisionteam.studentuserid) \
#                         inner join staff on supervisionteam.supervisoruserid = staff.staffid) \
#                         where students.userid = {student};")
#             supervisor_email = cur.fetchall()
#             supervisor_email_list=[]
#             for i in supervisor_email:
#                 str =''.join(i)
#                 supervisor_email_list.append(str)
#             supervisor_email_list = tuple(supervisor_email_list)
# #######################################################################
#             cur.execute(f"select thesistitle from thesis where studentuserid = {student};")
#             thesis = cur.fetchall()
# #######################################################################
#             convenor_email = ('megan.clayton@lincoln.ac.nz')
#             return render_template('Notification.html', student_email_list=student_email_list,supervisor_email_list=supervisor_email_list,thesis=thesis,reportid=reportid,convenor_email=convenor_email, user_name = username, user_role = session['role'], user_action = 'edit')
#         else:
#             username = user_name()
#             student = request.args.get('student')
#             convenor = request.args.get('convenor')
#             reportid = request.args.get('reportid')
#             stustatus = request.args.get('stustatus')
#             constatus = request.args.get('constatus')
#             supstatus = request.args.get('supstatus')

#             cur = getConnection()
#             cur = cur.cursor()
#             cur.execute(f"select luemail, personalemail from students where userid = {student};")
#             student_email = cur.fetchall()
#             for i in student_email:
#                 student_email_list=i
# #######################################################################
#             cur.execute(f"select thesistitle from thesis where studentuserid = {student};")
#             thesis = cur.fetchall()
# #######################################################################
#             cur.execute(f"select staff.email from ((((staff inner join supervisionteam on staff.staffid = supervisionteam.supervisoruserid) \
#                         inner join students on students.userid = supervisionteam.studentuserid) \
#                         inner join thesis on thesis.studentuserid = students.userid) \
#                         inner join report on report.thesisid = thesis.thesisid) \
#                         where students.userid = {student} and report.reportid = {reportid};")
#             supervisor_email_list = cur.fetchall()
# #######################################################################
#             convenor_email = ('megan.clayton@lincoln.ac.nz')
# #######################################################################
#             if stustatus == 'None':
#                 return render_template('Notification.html',student_email_list=student_email_list,thesis=thesis,reportid=reportid,user_name = username)
#             else:
#                 if supstatus == 'None':
#                     return render_template('Notification.html',supervisor_email_list=supervisor_email_list,thesis=thesis,reportid=reportid,user_name = username)
#                 else:
#                     return render_template('Notification.html',convenor_email=convenor_email,thesis=thesis,reportid=reportid,user_name = username)
#     else:
#         username = user_name()
#         recipient = request.form.get('recipient')
#         recipient1 = request.form.get('recipient1')
#         recipient2 = request.form.get('recipient2')
#         subject = request.form.get('subject')
#         content = request.form.get('content')
#         reportid = request.form.get('reportid')
#         today = date.today()
#         recipient3=recipient+recipient1+recipient2
#         print(recipient3)
#         print(subject)
#         print(content)
#         print(reportid)
#         # yagmail.register('comp639group5@gmail.com','lincolnuni2021')
#         # yag = yagmail.SMTP('comp639group5@gmail.com')
#         # yag.send(to = recipient2, subject= subject, contents= content)
#         cur = getConnection()
#         cur = cur.cursor()
#         cur.execute(f"UPDATE assessmentbyadmin set lastupdatedate = '{today}', action = 'done' where reportid = {reportid};")

#         # cur.execute(f"DECLARE @thesisid INT\
#         # SET @thesisid = N'SELECT thesisid FROM report WHERE reportid = {reportid}'\
#         # DECLARE @reportorder INT\
#         # SET @reportorder = N'SELECT MAX(reportorder) + 1 FROM report WHERE reportid = {reportid}'\
#         # DECLARE @duedate DATE\
#         # SET @duedate = N'SELECT MAX(duedate) + INTERVAL '6 months' FROM report WHERE reportid = {reportid};'\
#         # INSERT INTO report (thesisid, reportorder，reportstatus, duedate）\
#         # VALUES(@thesisid, @reportorder, 'Incomplete', @duedate)")
        
#         # cur.execute(f"DECLARE @thesisid INT\
#         # SET @thesisid = N'SELECT thesisid FROM report WHERE reportid = {reportid}'\
#         # DECLARE @reportid INT\
#         # SET @reportid = N'SELECT reportid FROM report WHERE thesisid = @thesisid ORDER BY reportorder DESC LIMIT 1;'\
#         # INSERT INTO questionstatus (reportid, questionid, status)\
#         # VALUES(@reportid, 1, 'Incomplete'),\
#         # (@reportid, 2, 'Incomplete'),\
#         # (@reportid, 3, 'Incomplete'),\
#         # (@reportid, 4, 'Incomplete'),\
#         # (@reportid, 5, 'Incomplete'),\
#         # (@reportid, 6, 'Incomplete'),\
#         # (@reportid, 7, 'Incomplete'),\
#         # (@reportid, 8, 'Incomplete'),\
#         # (@reportid, 9, 'Incomplete'),\
#         # (@reportid, 10, 'Incomplete'),\
#         # (@reportid, 11, 'Incomplete'),\
#         # (@reportid, 12, 'Incomplete');\
#         # INSERT INTO milestones(reportid)\
#         # VALUES (@reportid);\
#         # INSERT INTO evaluation(reportid)\
#         # VALUES (@reportid);\
#         # SELECT s.supervisoruserid \
#         # FROM thesis t\
#         # LEFT JOIN supervisionteam s\
#         # ON t.studentuserid = s.studentuserid\
#         # AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
#         # WHERE CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
#         # AND thesisid = @thesisid")
        
#         # supervisors = cur.fetchall()
#         # for s in supervisors:
#         #     cur.execute(f"DECLARE @thesisid INT\
#         #             SET @thesisid = N'SELECT thesisid FROM report WHERE reportid = {reportid}'\
#         #             DECLARE @reportid INT\
#         #             SET @reportid = N'SELECT reportid FROM report WHERE thesisid = @thesisid ORDER BY reportorder DESC LIMIT 1';\
#         #             INSERT INTO assessmentbysupervisor(reportid, supervisoruserid)\
#         #             VALUES (@reportid, {s[0]})")
        
#         # cur.execute(f"SELECT st.userid\
#         #             FROM report r\
#         #             LEFT JOIN thesis t\
#         #             ON CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
#         #             AND t.thesisid = r.thesisid\
#         #             LEFT JOIN students s\
#         #             ON CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
#         #             LEFT JOIN staff st\
#         #             ON CURRENT_TIMESTAMP BETWEEN st.validfromdate AND st.validtodate\
#         #             /*AND s.department = st.department*/\
#         #             AND st.position LIKE '%Convenor%'\
#         #             WHERE reportid = {reportid}\
#         #             LIMIT 1")
#         # convenor = cur.fetchone()
#         # cur.execute(f"DECLARE @thesisid INT\
#         #             SET @thesisid = N'SELECT thesisid FROM report WHERE reportid = {reportid}'\
#         #             DECLARE @reportid INT\
#         #             SET @reportid = N'SELECT reportid FROM report WHERE thesisid = @thesisid ORDER BY reportorder DESC LIMIT 1';\
#         #             INSERT INTO assessmentbyconvenor(reportid, convenoruserid)\
#         #             VALUES (@reportid, {convenor[0]})")
        
#         return render_template('Control_panel_admin.html',user_name = username)

# @app.route('/admin/view', methods = ['GET'])
# def adminview():
#     username = user_name()
#     Name = request.args.get('student')
#     studentName = request.args.get('student')
#     reportID = int(request.args.get('reportID'))
#     admin = request.args.get('admin')

#     print(reportID)
#     cur = dbconn
#     cur.execute("select th.studentuserid from report as re join thesis as th on th.thesisid=re.thesisid where re.reportid = %s"%reportID)
#     studentLoginID = cur.fetchall()[0][0]
#     # ---------------
#     # section A part
#     # ---------------
#     cur.execute("select st.studentid,st.enrolmentdate,st.address,st.phone,st.studymode,st.department,th.thesistitle from Students st join thesis th on th.studentuserid=st.userid where st. userid = %s"%(studentLoginID))
#     sectionA = cur.fetchall()[0]
#     cur.execute("select sp.supervisorrole, st.firstname, st.lastname from supervisionteam sp join staff st on sp.supervisoruserid=st.userid where sp.studentuserid =%s"%studentLoginID)
#     supervisionTeam =cur.fetchall()
#     cur.execute("select sc.scholarshipname,st.value,st.validtodate from scholarshipstudent st join scholarships sc on st.scholarshipid = sc.scholarshipid where st.studentuserid = %s"%studentLoginID)
#     scholarships = cur.fetchall()
#     cur.execute("select st.jobtitle,st.worktype,sf.firstname,sf.lastname,st.weeklyhours from studentemployment st join staff sf on sf.staffid=st.supervisoruserid where st.studentuserid = %s"%studentLoginID)
#     employment= cur.fetchall()
#     print(scholarships)
#     print(employment)
#     # ---------------
#     # section B part
#     # ---------------
#     cur.execute("select InductionProgramme, InductionProgrammeDate,MutualExpectationAgreement,MutualExpectationAgreementDate,KMRM,KMRMDate ,IntellectualPropertyAgreement,IntellectualPropertyAgreementDate,ThesisProposalSeminar,ThesisProposalSeminarDate,\
#         ProposalApproval,ProposalApprovalDate,PGConference,PGConferenceDate,ResultsSeminar,ResultsSeminarDate,HumanEthicsApproval,HealthSafetyApproval,AnimalEthicsApproval,BiologicalSafetyApproval,RadiationProtectionApproval from milestones where reportid=%s"%reportID)
#     sectionB = cur.fetchall()[0]
#     # ---------------
#     # section C part
#     # ---------------
#     cur.execute("select AccessPrincipalSupervisor,AccessPrincipalSupervisorComment,AccesssAssociateSupervisor,AccesssAssociateSupervisorComment,ExpertisePrincipalSupervisor,ExpertisePrincipalSupervisorComment,ExpertiseAssociateSupervisor,ExpertiseAssociateSupervisorComment,FeedbackQualityPrincipalSupervisor,FeedbackQualityPrincipalSupervisorComment,FeedbackQualityAssociateSupervisor,FeedbackQualityAssociateSupervisorComment,TimelinessPrincipalSupervisor,TimelinessPrincipalSupervisorComment,\
#         TimelinessAssociateSupervisor,TimelinessAssociateSupervisorComment,CourseAvailability,CourseAvailabilityComment,Workspace,WorkspaceComment,ComputerFacility,ComputerFacilityComment,ITSupport,ITSupportComment,ResearchSoftware,ResearchSoftwareComment,Library,LibraryComment,LearningSupport,LearningSupportComment,StatSupport,StatSupportComment,ResearchEquipment,ResearchEquipmentComment,TechSupport,TechSupportComment,FinancialSupport,FinancialSupportComment,Other,OtherComment,SupervisorMeetingFreq,\
#         FeedbackWaitPeriod,FeedbackMethod from evaluation where reportid=%s"%reportID)
#     sectionC = cur.fetchall()[0]
#     # ---------------
#     # section D part
#     # ---------------
#     cur.execute("select objectivecomment, completionstatus,reasonforchange from currentobjective where reportid=%s order by uid"%reportID)
#     sectionD1=cur.fetchall()
#     cur.execute("select comment from covideffect where reportid=%s order by uid"%reportID)
#     sectionD2=cur.fetchall()
#     cur.execute("select comment from academicachievement where reportid= %s order by uid"%reportID)
#     sectionD3=cur.fetchall()
#     cur.execute("select title, duedate, comment from futureobjective where reportid=%s order by uid"%reportID)
#     sectionD4=cur.fetchall()
#     cur.execute("select title, amount, comment from expenditure where reportid=%s order by uid"%reportID) 
#     sectionD5=cur.fetchall()
#     sectionD=[sectionD1,sectionD2,sectionD3,sectionD4,sectionD5]
#     # ---------------
#     # section F part
#     # ---------------
#     cur.execute("SELECT abs.reportid, CONCAT(s.firstname, ' ', s.lastname) AS name, comments, s.userid, s.position, s.email\
#         FROM assessmentbystudent abs\
#         LEFT JOIN staff s\
#         ON abs.talkinpersonuserid = s.userid\
#         WHERE reportid = %s"%reportID)
#     sectionF = cur.fetchone()
#     print(sectionF)
#     # ---------------
#     # section E part
#     # ---------------
#     cur.execute("select a.uid, a.supervisoruserid, a.sixmonthprogress,a.phdprogress,a.academicqaulity,\
#         a.technicalskills,a.likelytoachieveobjectives,a.recommendationcarriedout, a.comments, \
#         s.firstname, s.lastname, t.supervisorrole\
#         from assessmentbysupervisor a \
#         LEFT JOIN staff s\
#         ON a.supervisoruserid = s.userid\
#             AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
#         LEFT JOIN report r\
#         ON r.reportid = a.reportid\
#         LEFT JOIN thesis th\
#         ON th.thesisid = r.thesisid\
#         AND CURRENT_TIMESTAMP BETWEEN th.validfromdate AND th.validtodate\
#         LEFT JOIN supervisionteam t\
#         ON t.supervisoruserid = s.userid\
#             AND CURRENT_TIMESTAMP BETWEEN t.validfromdate AND t.validtodate\
#             AND t.studentuserid = th.studentuserid \
#         WHERE a.reportid = %s \
#         ORDER BY CASE WHEN t.supervisorrole LIKE 'Supervisor' THEN 0\
#             WHEN t.supervisorrole LIKE 'Associate' THEN 1\
#             ELSE 2 END ASC"%reportID)
#     supervisor_feedback = cur.fetchall()
#     cur.execute(f"SELECT a.uid, a.convenoruserid, a.areaofconsideration, a.rating, s.firstname, s.lastname\
#             FROM assessmentbyconvenor a\
#             LEFT JOIN staff s\
#             ON a.convenoruserid = s.userid\
#             AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate\
#             WHERE a.reportid =%s"%reportID)
#     convenor_feedback = cur.fetchone()
    

#     return render_template('admin_view.html',reportID = reportID, 
#     Name = studentName, sectionA=sectionA,sectionB=sectionB,sectionC=sectionC,sectionD=sectionD,
#     supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment,
#     admin=admin,sectionF=sectionF,supervisor_feedback =supervisor_feedback, convenor_feedback =convenor_feedback,user_name = username)


# @app.route('/student/view', methods = ['GET'])
# def studentview():
#     username = user_name()
#     Name = request.args.get('student')
#     studentName = request.args.get('student')
#     reportID = int(request.args.get('reportID'))

#     print(reportID)
#     cur = dbconn
#     cur.execute("select th.studentuserid from report as re join thesis as th on th.thesisid=re.thesisid where re.reportid = %s"%reportID)
#     studentLoginID = cur.fetchall()[0][0]
#     # ---------------
#     # section A part
#     # ---------------
#     cur.execute("select st.studentid,st.enrolmentdate,st.address,st.phone,st.studymode,st.department,th.thesistitle from Students st join thesis th on th.studentuserid=st.userid where st. userid = %s"%(studentLoginID))
#     sectionA = cur.fetchall()[0]
#     cur.execute("select sp.supervisorrole, st.firstname, st.lastname from supervisionteam sp join staff st on sp.supervisoruserid=st.userid where sp.studentuserid =%s"%studentLoginID)
#     supervisionTeam =cur.fetchall()
#     cur.execute("select sc.scholarshipname,st.value,st.validtodate from scholarshipstudent st join scholarships sc on st.scholarshipid = sc.scholarshipid where st.studentuserid = %s"%studentLoginID)
#     scholarships = cur.fetchall()
#     cur.execute("select st.jobtitle,st.worktype,sf.firstname,sf.lastname,st.weeklyhours from studentemployment st join staff sf on sf.staffid=st.supervisoruserid where st.studentuserid = %s"%studentLoginID)
#     employment= cur.fetchall()
#     print(scholarships)
#     print(employment)
#     # ---------------
#     # section B part
#     # ---------------
#     cur.execute("select InductionProgramme, InductionProgrammeDate,MutualExpectationAgreement,MutualExpectationAgreementDate,KMRM,KMRMDate ,IntellectualPropertyAgreement,IntellectualPropertyAgreementDate,ThesisProposalSeminar,ThesisProposalSeminarDate,\
#         ProposalApproval,ProposalApprovalDate,PGConference,PGConferenceDate,ResultsSeminar,ResultsSeminarDate,HumanEthicsApproval,HealthSafetyApproval,AnimalEthicsApproval,BiologicalSafetyApproval,RadiationProtectionApproval from milestones where reportid=%s"%reportID)
#     sectionB = cur.fetchall()[0]
#     # ---------------
#     # section C part
#     # ---------------
#     cur.execute("select AccessPrincipalSupervisor,AccessPrincipalSupervisorComment,AccesssAssociateSupervisor,AccesssAssociateSupervisorComment,ExpertisePrincipalSupervisor,ExpertisePrincipalSupervisorComment,ExpertiseAssociateSupervisor,ExpertiseAssociateSupervisorComment,FeedbackQualityPrincipalSupervisor,FeedbackQualityPrincipalSupervisorComment,FeedbackQualityAssociateSupervisor,FeedbackQualityAssociateSupervisorComment,TimelinessPrincipalSupervisor,TimelinessPrincipalSupervisorComment,\
#         TimelinessAssociateSupervisor,TimelinessAssociateSupervisorComment,CourseAvailability,CourseAvailabilityComment,Workspace,WorkspaceComment,ComputerFacility,ComputerFacilityComment,ITSupport,ITSupportComment,ResearchSoftware,ResearchSoftwareComment,Library,LibraryComment,LearningSupport,LearningSupportComment,StatSupport,StatSupportComment,ResearchEquipment,ResearchEquipmentComment,TechSupport,TechSupportComment,FinancialSupport,FinancialSupportComment,Other,OtherComment,SupervisorMeetingFreq,\
#         FeedbackWaitPeriod,FeedbackMethod from evaluation where reportid=%s"%reportID)
#     sectionC = cur.fetchall()[0]
#     # ---------------
#     # section D part
#     # ---------------
#     cur.execute("select objectivecomment, completionstatus,reasonforchange from currentobjective where reportid=%s order by uid"%reportID)
#     sectionD1=cur.fetchall()
#     cur.execute("select comment from covideffect where reportid=%s order by uid"%reportID)
#     sectionD2=cur.fetchall()
#     cur.execute("select comment from academicachievement where reportid= %s order by uid"%reportID)
#     sectionD3=cur.fetchall()
#     cur.execute("select title, duedate, comment from futureobjective where reportid=%s order by uid"%reportID)
#     sectionD4=cur.fetchall()
#     cur.execute("select title, amount, comment from expenditure where reportid=%s order by uid"%reportID) 
#     sectionD5=cur.fetchall()
#     sectionD=[sectionD1,sectionD2,sectionD3,sectionD4,sectionD5]
#     # ---------------
#     # section F part
#     # ---------------
#     cur.execute("SELECT abs.reportid, CONCAT(s.firstname, ' ', s.lastname) AS name, comments, s.userid, s.position, s.email\
#         FROM assessmentbystudent abs\
#         LEFT JOIN staff s\
#         ON abs.talkinpersonuserid = s.userid\
#         WHERE reportid = %s"%reportID)
#     sectionF = cur.fetchone()
#     print(sectionF)
    

#     return render_template('student_view.html',reportID = reportID, 
#     Name = studentName, sectionA=sectionA,sectionB=sectionB,sectionC=sectionC,sectionD=sectionD,
#     supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment,sectionF=sectionF,user_name = username)



































































































































































































































    # return render_template('view_report.html',reportID = reportID, Name = studentName, sectionA=sectionA,sectionB=sectionB,sectionC=sectionC,sectionD=sectionD,supervisionTeam=supervisionTeam,scholarships=scholarships,employment=employment)






















































































































    # supervisorID  = session['id']
    # print("supervisorID",supervisorID)
    # cur = getCursor()
    # cur.execute("select studentuserid from supervisionteam where supervisoruserid= %s"%(supervisorID))
    # students = cur.fetchall()
    # username = user_name()
    # print('student',students)
    # if students:
    #     DataUndersupervision = []
    #     for eachstudent in students:
    #         cur.execute("select firstname,lastname from students where CURRENT_DATETIME BETWEEN validfromdate AND validtodate AND userid = %s"%(eachstudent))
    #         studentName = cur.fetchone()
    #         studentName= studentName[0]+' '+studentName[1]
    #         name = [studentName]
    #         print('eachstudent',eachstudent)
    #         username = user_name()
    #         cur.execute("select re.reportorder,re.duedate,re.reportid from report as re \
    #         join thesis as th on th.thesisid=re.thesisid \
    #         join login as lo on th.studentuserid = lo.userid \
    #         where re.reportstatus = 'Incomplete' and lo.userid = %s "%(eachstudent))
    #         reportInfo = cur.fetchall()
    #         print(reportInfo)
    #         if not DataUndersupervision and not reportInfo:
    #             print('###########not DataUndersupervision and not reportInfo#########')
    #             DataUndersupervision=None
    #             return render_template('Control_panel_supervisor.html',pendingReport=DataUndersupervision, user_name = username, user_role = session['role'], user_action = 'na')
    #         elif reportInfo:
    #             Info = [name,reportInfo[0][0],reportInfo[0][1],reportInfo[0][2]]
    #             DataUndersupervision.append(Info)
            
    #     roles=[]
    #     for each in DataUndersupervision:
    #         cur.execute("select sp.supervisorrole from supervisionteam sp \
    #         join thesis th on th.studentuserid = sp.studentuserid \
    #         join report re on th.thesisid = re.thesisid where sp.supervisoruserid =%s and re.reportid = %s"%(supervisorID,each[3]))
    #         supervisorRole = cur.fetchall()[0]
    #         roles.append(supervisorRole)
    #     for aa in range(len(DataUndersupervision)):
    #         DataUndersupervision[aa].append(roles[aa])
    # print(DataUndersupervision)
    # return render_template('Control_panel_supervisor.html',pendingReport=DataUndersupervision, 
    # user_name = username, user_role = session['role'], user_action = 'na')










