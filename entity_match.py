#!/usr/bin/env python2.7
import cx_Oracle
import os
import time
import difflib
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate

# oracle credentials
ora_user        = 'user'
ora_passwd      = 'pass'

def send_mail(send_from, send_to, subject, text, files=None,
              server="127.0.0.1"):
    assert isinstance(send_to, list)

    msg = MIMEMultipart(
        From=send_from,
        To=COMMASPACE.join(send_to),
        Date=formatdate(localtime=True),
        Subject=subject
    )
    msg.attach(MIMEText(text))

    for f in files or []:
        with open(f, "rb") as fil:
            attach_file = MIMEApplication(fil.read())
            attach_file.add_header('Content-Disposition', 'attachment', filename="results.xls")
            msg.attach(attach_file)                                

    smtp = smtplib.SMTP(server)
    smtp.sendmail(send_from, send_to, msg.as_string())
    smtp.close()
    

if __name__ == '__main__':


    # dekstop path (working directory)
    desktop = os.path.expanduser("~/Desktop/")

    # for writing files
    timestr = time.strftime("%Y%m%d-%H%M%S")
    datestr = time.strftime("%Y.%m.%d")
        
    # connect to Oracle 
    ip = 'server'
    port = 1521
    SID = 'systemsid'
    dsn_tns = cx_Oracle.makedsn(ip, port, SID)
    db = cx_Oracle.connect(ora_user, ora_passwd, dsn_tns)
    cur = db.cursor()
    print "Connected to Oracle.  Loading entity data to memory."

    # setup input and output files
    file_to_search = desktop + "test.txt"
    file_to_search = "Names test 2.txt"
    output_file = desktop + timestr + "_search_results.xls"
    output_file = timestr + "_search_results.xls"
    f = open(output_file,"w")

    # query oracle for two columns:
    # 1: the name of the legal matter, which may just be a client name (e.g., US Bank SEC Subpoena)
    # 2: a string containing a semicolon-delimited list of known alternate/affiliate
    #    names to be used for searching (e.g., US Bank, United States Bank, USB, Project Blue Ribbon)

    entity_query = """
        select  upper(replace(replace(replace(mattername,CHR(9)),CHR(10)),CHR(13)))
             ,upper(replace(replace(replace(pafield2,CHR(9)),CHR(10)),CHR(13)))
               from     legalmatter
         where  status = 'Active' AND legalmattertypeid not in (2, 5)
    """

    person_query = """
        select  upper(replace(replace(replace(mattername,CHR(9)),CHR(10)),CHR(13)))
             ,upper(replace(replace(replace(pafield2,CHR(9)),CHR(10)),CHR(13)))
               from     legalmatter
         where  status = 'Active' AND legalmattertypeid in (2, 5)
    """
    
    cur.execute(entity_query)                        

    # load the list of "entities on hold" to memory    
    # load entities on hold from oracle into a dict
    # legal_holds[ "mattername" ] = ["mattername", "entity1","entity2","...","entityN"]        
    
    print "Loading legal hold information from Atlas to memory...."    
    legal_holds = {}    
    for row in cur:
        entities = []
        # include the matter name as an entity for searching
        entities.append( row[0].upper() )   
        for entity in row[1].split(";"):
            if ( entity != "" ):
                entities.append( entity.upper() )            
        legal_holds[row[0]] = entities
    cur.close()    
    print "Loaded matter and entity information."
    
    # drop connection to Oracle
    db.close()
    print "Disconnected from Oracle"   
    
    # open the input file  (the file contains the text to be searched)
    # each line in the file has to be checked for legal hold    
    lines = open( file_to_search ).read().splitlines() 
    line_count = 0

    # create a list for holding dictionaries , one dict for each line, so 
    # we can reconstitute the file submitted alongside the search results
    results = []    
    print "Processing " + str(len(lines)) + " lines."

    # process the file, line-by-line
    for line in lines:
        line = line.upper()
        line_count = line_count + 1
        words = line.split()
        
        result = {}
        result["line_number"] = line_count
        result["original_text"] = line
       
        # 1:1 lists where the responsive matter is in the same list
        # position as the term that caused the matter to respond	
        matters = []
        terms = []       
        
        # loop through all active legal hold matters
        for matter, entities in legal_holds.iteritems():

            # compare each entity on hold with the line
            for entity in entities:
                
                # get the n for n-gram creation
                n = len( entity.split(" ") )              
                
                # create the n-grams based on # of words in entity
                n_gram = [" ".join(words[i:i+n]) for i in range(0, len(words), n)]
			
                # go through each n-gram in the line checking for this entity
                for gram in n_gram:
                    
                    # do a similarity comparison between the entity and the
                    # n-grams from the file
                    seq = difflib.SequenceMatcher(None, entity, gram )
                    d = seq.ratio()*100
                    if ( d > 85 ):				
                        
                        # we have a match, add to the results 
                        matters.append(matter)
                        terms.append(gram)
                        print "Found a hit :", gram, " on matter ", matter, "(", entity, ")"
                        
        # add the lists of matter/term to the result dict
        result["matters"] = matters
        result["terms"] = terms
        results.append( result )	
        
    # output results file as "Excel" (html disguised/named as xls)
    f.write ("<style>table{border-collapse:collapse;}td{border:1px solid #ccc;}</style>")
    f.write ("<table><tr><th>No.<th>Submitted<th>Matter(s)<th>Term(s)")
    for r in results:
        s = "<tr><td>" + str(r["line_number"]) + "<td>" + r["original_text"]  + "<td>" + ";".join(r["matters"])  + "<td>" + ";".join(r["terms"])  
        f.write( s )                    
    f.write ("</table>")

    # close the output file
    f.close()   
        
    # email the results 
    #send_mail( "vince.dimascio@gmail.com", ["vincent.dimascio@pwc.com"],
    #          "A legal hold search completed", "See attached", 
    #           [output_file], "127.0.0.1")

    # remove the results

    # move the source file to the "completed" folder
        
    # done
    print "Done"

