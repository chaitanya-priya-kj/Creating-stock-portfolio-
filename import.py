import sqlite3
import csv

# Connect to the SQLite database
conn = sqlite3.connect('chai.db')
c = conn.cursor()

# Execute a query to fetch the table data
c.execute("SELECT * FROM price")

# Fetch all rows from the result set
rows = c.fetchall()

# Define the path for the CSV file
csv_file_path = 'price_data.csv'

# Write the fetched data into a CSV file
with open(csv_file_path, 'w', newline='') as csvfile:
    # Create a CSV writer object
    csv_writer = csv.writer(csvfile)
    
    # Write the header row
    csv_writer.writerow([description[0] for description in c.description])
    
    # Write the data rows
    csv_writer.writerows(rows)

# Close the database connection
conn.close()

print(f"CSV file '{csv_file_path}' has been created successfully.")
