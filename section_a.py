from logging import debug
from flask import Flask, render_template, url_for, session, request, flash, redirect
import psycopg2, db_details
import uuid
from datetime import datetime, date, timedelta, time
import re
from types import MethodDescriptorType
from flask import Flask, render_template, request, redirect, url_for, session
import connect
import psycopg2
from functools import wraps

# Global variables
dbconn = None

def getCursor():
    global dbconn
    if dbconn == None:
        conn = psycopg2.connect(dbname=connect.dbname, user=connect.dbuser, password=connect.dbpass, host=connect.dbhost, port=connect.dbport)
        conn.autocommit = True
        dbconn = conn.cursor()
        return dbconn
    else:
        return dbconn

class SecA:
    def __init__(report_id, viewer_role, student_user_id):
        self.report_id = report_id
        self.viewer_id = session['id']
        self.viewer_role = viewer_role
        self.student_user_id = student_user_id

    
    def get_student_details(self):
        cur = getCursor()
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
        WHERE s.userid = {self.student_user_id} \
        AND CURRENT_TIMESTAMP BETWEEN s.validfromdate AND s.validtodate;"
        )

        student_details = cur.fetchone()
        return student_details
        
        student_details = get_student_details(self)
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

    def get_supervision_team(self):
        cur = getCursor()
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
        return supervisors

    def get_job_supervisors(self):
        cur = getCursor()
        cur.execute("SELECT userid, firstname, lastname\
            FROM staff WHERE position = 'Professor' \
                AND CURRENT_TIMESTAMP BETWEEN validfromdate and validtodate")
        job_supervisors = cur.fetchall()
        return job_supervisors

    def available_chief_supervisors(self):
    #Drop-down menu for adding chief supervisors - Anti join to exclude existing supervisor in the team
        cur = getCursor()
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
    def available_other_supervisors(self):
        cur = getCursor()
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

    def available_
        cur = getCursor()
        cur.execute(f"/* Get scholarship details */\
            SELECT sc.scholarshipname\
            ,ss.value\
            ,ss.startdate\
            ,ss.enddate\
            ,ROUND((CAST(ss.enddate AS date) - CAST(ss.startdate AS date))/365, 0) AS tenure\
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

        return render_template('SectionA.html', student_name = student_name, 
            student_id = student_id, enrolment_date = enrolment_date, address = address,
            phone = phone, department = department, luemail = luemail, 
            personalemail = personalemail, study_mode = study_mode, thesis_title = thesis_title, 
            supervisors = supervisors, scholarships = scholarships, employment = employment, 
            available_other_supervisors = available_other_supervisors, 
            available_chief_supervisors = available_chief_supervisors, 
            available_scholarships = available_scholarships, job_supervisors = job_supervisors,
            viewer_role = session['role'], report_id = report_id, student_user_id = student_user_id
    )

    
