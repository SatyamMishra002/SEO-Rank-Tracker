import pymysql.cursors
import sys, os
import time

def DB_Connection():
    connection = ''
    a = 0
    while a == 0:
        try:
            connection = pymysql.connect(host = 'localhost', user = "root", passwd = "root", db ="site_report")
            return connection
        except Exception as e:
            exc_type , exc_obj , exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print("Error ON : " , sys._getframe().f_code.co_name + "--> " + str(e) , "\n" , exc_type , "\n" , fname ,"\n" , exc_tb.tb_lineno)
            a = 0
            time.sleep(10)
            
            
# thread_id = mydb.thread_id()
# kill_query(thread_id)
def kill_query(thread_id):
    try:
        mydb = DB_Connection()
        mycursor = mydb.cursor() 
        thread_id2 = mydb.thread_id()
        mycursor.execute(f'KILL QUERY {thread_id}')
        mycursor.close()
        mydb.close()
    except Exception as close_error:
        mycursor.close()
        mydb.close()
        print(f"Error on KILL QUERY: {close_error}")
        
        