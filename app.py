from flask import Flask, render_template, request, redirect, url_for, jsonify
import subprocess
import globalvar  # Ensure this module is correctly defined and available
from automation_report import *
from database import *

app = Flask(__name__)

# Mock database for user authentication
users = {
    "admin": "123",
}

@app.route("/", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            return redirect(url_for('dashboard', username=username))
        else:
            error = "Invalid credentials or account deactivated."

    return render_template('index.html', error=error)

@app.route("/dashboard")
def dashboard():
    username = request.args.get('username')  # Get username from query parameters
    return render_template('dashboard.html', username=username)
    
@app.route("/add_project", methods=["GET", "POST"])
def add_project():
    if request.method == "GET":
        return render_template('add_project.html')
    elif request.method == "POST":
        try:
            # Retrieve the list of data from the AJAX request
            domain = request.json.get('domain')
            country = request.json.get('country')
            keywords = request.json.get('keywords')

            conn = DB_Connection()
            cursor = conn.cursor()
            # duplicates = []  # List to store indexes of duplicate entries

            # for i, entry in enumerate(data):
                # project_name = entry['domain']
                # country = entry['country']
                # keyword = entry['keyword']
            country_code = domain_country_dict.get_country_code(country)

            duplicate_query = "SELECT * FROM project WHERE project_name = %s AND country = %s"
            cursor.execute(duplicate_query, (domain.strip(), country_code))
            existing_data = cursor.fetchall()

            if len(existing_data) == 0:
                project_query = "INSERT INTO project (project_name, country) VALUES (%s, %s)"
                cursor.execute(project_query, (domain.strip(), country_code))
                project_id = cursor.lastrowid
                
                duplicates = []

                # Check each keyword and insert if not already present
                for keyword in keywords:
                    duplicate_query_kw = "SELECT * FROM keywords WHERE keyword = %s AND project_id = %s"
                    cursor.execute(duplicate_query_kw, (keyword, project_id))
                    existing_data_kw = cursor.fetchall()

                    if len(existing_data_kw) == 0:
                        keyword_query = "INSERT INTO keywords (keyword, project_id) VALUES (%s, %s)"
                        cursor.execute(keyword_query, (keyword, project_id))
                    else:
                        duplicates.append(keyword)  # Collect duplicates
                
                # Commit the transaction after all insertions
                conn.commit()

                if duplicates:
                    # Return duplicate status with the list of duplicate keywords
                    return jsonify({"status": "duplicate", "duplicates": "duplicates", "username": "GunGun"})
                else:
                    # Return success response if no duplicates
                    return jsonify({"status": "success", "redirect_url": url_for('add_project')})


            else:
                # Return duplicate status with the indices of duplicate entries
                return jsonify({"status": "duplicate", "duplicates": "duplicates", "username": "GunGun"})


        except Exception as e:
            conn.rollback()
            print(e)
            return jsonify({"status": "error", "message": str(e)})


@app.route('/view_report', methods=["GET", "POST"])
def view_report():
    if request.method == "GET":
        try:
            # Connect to the database
            conn = DB_Connection()
            cursor = conn.cursor()

            # Query to get project data (including keywords)
            query = """
            SELECT p.project_name, p.country, GROUP_CONCAT(k.keyword) as keywords
            FROM project p
            LEFT JOIN keywords k ON p.project_id = k.project_id
            GROUP BY p.project_name, p.country
            """
            cursor.execute(query)
            project_data = cursor.fetchall()

            # Close connection
            cursor.close()
            conn.close()

            # Format the data to send to the frontend
            updated_project_data = []
            for project_name, country_code, keywords in project_data:
                country_name = domain_country_dict.get_country_by_code(country_code)
                keyword_list = keywords.split(',') if keywords else []
                updated_project_data.append((project_name, country_name, country_code, keyword_list))

            # Render the template
            return render_template('view_project.html', project_data=updated_project_data)

        except Exception as e:
            print(e)
            return "An error occurred while fetching data"



@app.route('/report', methods=["GET", "POST"])
def report():
    if request.method == "GET":
        try:

            project = request.args.get('domain')
            country = request.args.get('country')
            conn = DB_Connection()
            cursor = conn.cursor()

            query = "SELECT project_id FROM project WHERE project_name = %s AND country = %s"
            cursor.execute(query, (project,country,))
            project_id = cursor.fetchone()

            if project_id:
                # Query to get keywords associated with the project
                query = """
                SELECT k.kw_id, k.keyword 
                FROM keywords k 
                WHERE k.project_id = %s
                """
                cursor.execute(query, (project_id[0],))
                keywords_data = cursor.fetchall()

                updated_project_data = []

                for kw_id, keyword in keywords_data:
                    # Get the current position using ChromeDriver
                    # Scrape for each keyword and track the ranking
                    curr_position = check_position(project, country, keyword)
                    if curr_position == None: curr_position = 0

                    # Insert the current position into the report table
                    insert_query = "INSERT INTO report (kw_id, position) VALUES (%s, %s)"
                    cursor.execute(insert_query, (kw_id, curr_position))
                    conn.commit()


                    # Optionally append data for display
                    updated_project_data.append((keyword, curr_position))

            # Query to get domains and countries from the database
            query = """SELECT report_id, kw_id, keyword, position
                    FROM (
                        SELECT 
                            r.report_id, 
                            k.kw_id, 
                            k.keyword, 
                            r.position,
                            ROW_NUMBER() OVER (PARTITION BY k.kw_id ORDER BY r.report_id DESC) as row_num
                        FROM keywords k
                        LEFT JOIN project p ON k.project_id = p.project_id
                        INNER JOIN report r ON k.kw_id = r.kw_id
                        WHERE k.project_id = %s
                    ) ranked_reports
                    WHERE row_num <= 7
                    ORDER BY kw_id, row_num;"""
            cursor.execute(query,(project_id[0]))
            project_data = cursor.fetchall()

            keyword_positions = {}

            for row in project_data:
                keyword = row[2]  # Extract keyword
                position = row[3]  # Extract position

                if keyword not in keyword_positions:
                    keyword_positions[keyword] = []
                keyword_positions[keyword].append(position)

            # Convert to list of tuples for the template
            updated_project_data = [(keyword, positions) for keyword, positions in keyword_positions.items()]

            cursor.close()
            conn.close()

            # Render the report.html template with the structured data
            return render_template('report.html', project_data=updated_project_data)
        except Exception as e:
            print(e)
            return "An error occurred while fetching data"



@app.route('/edit_project', methods=["GET", "POST"])
def edit_project():
    if request.method == "GET":
        return render_template('edit_project.html')
    # elif request.method == "POST":
        # try:
        #     project = request.form['Domain']
        #     globalvar.country = request.form['country_value']
        #     globalvar.keyword = request.form['Keyword_value']

        #     # Run the automation_report.py script
        #     # subprocess.run(['python', 'automation_report.py'])
        #     country_code = domain_country_dict.get_country_code(globalvar.country)
        #     keyword = globalvar.keyword
        #     ChromeDriver(project,country_code,keyword)

        #     # return redirect(url_for('dashboard', username=request.form.get('username')))  # Redirect to dashboard
        # except Exception as e:
        #     print(e)
if __name__ == "__main__":


    app.run(debug=True, port=5001)
