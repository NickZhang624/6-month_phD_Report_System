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

#dbconn = None
#def getConnection():
#    global dbconn
#    if dbconn == None:
#        dbconn = psycopg2.connect(dbname=db_details.dbname, user=db_details.dbuser,password=db_details.dbpass, host=db_details.dbhost, port=db_details.dbport)
#        dbconn.autocommit = True
#        return dbconn
#    else:
#        return dbconn


class SecD:
    def __init__(self,report_id):
        self.reportID = report_id
        self.formInfo = []
        self.totalRow = None
        self.uid = None
        self.databaseForm = None
        self.rowName=[]
        self.questionid = None




    def form1(self):
        cur = getCursor()
        cur.execute("select uid from currentobjective where reportid = %s order by uid"%(self.reportID))
        self.uid = cur.fetchall()
        formName = request.form
        currentobjective = []
        for aa in formName:
            currentobjective.append(request.form[aa])
        self.formInfo = currentobjective
        
        cur.execute("select objectivecomment,completionstatus,reasonforchange from currentobjective where reportid = %s order by uid"%(self.reportID))
        self.databaseForm = cur.fetchall()
        self.totalRow = len(self.databaseForm)
        
        self.rowName=[]
        for aa in range(self.totalRow):
            temp=("status"+str(aa+1),"comments"+str(aa+1))
            self.rowName.append(temp)
        
        cur.execute(f"SELECT questionid FROM questions WHERE description LIKE '%Current Objective%'")
        result = cur.fetchone()
        self.questionid = result[0]





    
    def form2(self):
        cur = getCursor()
        cur.execute("select uid from covideffect where reportid = %s order by uid"%(self.reportID))
        self.uid = cur.fetchall()

        cur.execute("select comment from covideffect where reportid = %s order by uid"%(self.reportID))
        self.databaseForm = cur.fetchall()
        self.totalRow = len(self.databaseForm)

        #covideffect=[]
        #formName = request.form
        #for aa in formName:
        #    covideffect.append(request.form[aa])
        #self.formInfo = covideffect

        self.rowName=[]
        for aa in range(self.totalRow):
            temp=[("covidComment"+str(aa+1))]
            self.rowName.append(temp)

    
    def form3(self):
        cur = getCursor()
        cur.execute("select uid from academicachievement where reportid = %s order by uid"%(self.reportID))
        self.uid = cur.fetchall()

        #formName = request.form
        #otherAchieve = []
        #for aa in formName:
        #    otherAchieve.append(request.form[aa])
        #self.formInfo = otherAchieve

        cur.execute("select comment from academicachievement where reportid = %s order by uid"%(self.reportID))
        self.databaseForm = cur.fetchall()
        self.totalRow = len(self.databaseForm)

        self.rowName=[]
        for aa in range(self.totalRow):
            temp=[("otherAchieve"+str(aa+1))]
            self.rowName.append(temp)


    def form4(self):
        cur = getCursor()
        cur.execute("select uid from futureobjective where reportid = %s order by uid"%(self.reportID))
        self.uid = cur.fetchall()

        cur.execute("select title,duedate,comment from futureobjective where reportid = %s order by uid"%(self.reportID))
        self.databaseForm = cur.fetchall()
        self.totalRow = len(self.databaseForm)

        #formName = request.form
        #futureObjective = []
        #for aa in formName:
        #    futureObjective.append(request.form[aa])
        #self.formInfo = futureObjective
        #if request.method=="POST":
        #    for aa in range(self.totalRow):
        #        if futureObjective[aa*3+1]:
        #            futureObjective[aa*3+1] = datetime.strptime(futureObjective[aa*3+1] , '%Y-%m-%d')

        self.rowName=[]
        for aa in range(self.totalRow):
            temp=("item"+str(aa+1),"amount"+str(aa+1),"note"+str(aa+1))
            self.rowName.append(temp)



    def form5(self):
        cur = getCursor()
        cur.execute("select uid from expenditure where reportid = %s order by uid"%(self.reportID))
        self.uid = cur.fetchall()

        #formName = request.form
        #expenditure = []
        #for aa in formName:
        #    expenditure.append(request.form[aa])
        #self.formInfo = expenditure

        cur.execute("select title,amount,comment from expenditure where reportid = %s order by uid"%(self.reportID))
        self.databaseForm = cur.fetchall()
        self.totalRow = len(self.databaseForm)
        self.rowName=[]
        for aa in range(self.totalRow):
            temp=("title"+str(aa+1),"amount"+str(aa+1),"comment"+str(aa+1))
            self.rowName.append(temp)
        


        

    