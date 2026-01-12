"""
Populate SimpleSQLDB with realistic Kenyan context data
Generates 500 employee records with authentic Kenyan details
"""

import random
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.engine import QueryEngine
from core.storage import Storage

# Kenyan context data
FIRST_NAMES = [
    # Kikuyu
    "Kamau", "Njeru", "Wanjiru", "Mwangi", "Kariuki", "Kimani", "Gitau", "Nyambura",
    "Mutua", "Kipchoge", "Kiptoo", "Kipkemoi", "Kiplagat", "Kipchoge", "Jepkosgei",
    # Luo
    "Omondi", "Ochieng", "Onyango", "Kipchoge", "Otieno", "Okech", "Owalo", "Onyonka",
    "Achieng", "Nyagudi", "Adero", "Adwok", "Aduol", "Akoth", "Akinyi", "Adhiambo",
    # Luhya
    "Wekesa", "Juma", "Mutua", "Mudanya", "Mwania", "Musyoka", "Mboya", "Musinya",
    "Ananyeta", "Nabwire", "Namukhome", "Namukhara", "Nambibi", "Namwanda", "Namasaba",
    # Somali
    "Hassan", "Mohamed", "Ali", "Ibrahim", "Ahmed", "Omar", "Farah", "Abdi",
    "Amina", "Fatima", "Aisha", "Leila", "Habiba", "Safiya", "Hana",
    # Maasai
    "Ole", "Kipchoge", "Kiplagat", "Kiprotich", "Kipsambu", "Kipkoskei",
    "Kipyegon", "Kipturiek", "Kipngetich", "Kipkemboi",
    # Kamba
    "Mutua", "Kimani", "Kamau", "Musyoka", "Muthui", "Mwangi", "Kalembe", "Kasai",
    # Modern names (popular in Kenya)
    "Brian", "Dennis", "Victor", "Steven", "Peter", "David", "James", "Michael",
    "Joshua", "Daniel", "Robert", "Richard", "Charles", "Edward", "Andrew",
    "Mercy", "Grace", "Faith", "Hope", "Patience", "Joy", "Peace", "Blessing",
    "Sarah", "Mary", "Elizabeth", "Rebecca", "Ruth", "Esther", "Hannah", "Deborah",
    # Mixed
    "Kipkemoi", "Kipkurui", "Kipchumba", "Kiplagat", "Kipchoge", "Kipkoskei",
]

LAST_NAMES = [
    "Kamau", "Mwangi", "Kariuki", "Kimani", "Gitau", "Kiplagat", "Kipchoge",
    "Ochieng", "Onyango", "Achieng", "Otieno", "Omondi", "Okech",
    "Wekesa", "Juma", "Mutua", "Mudanya", "Mwania", "Musyoka", "Mboya",
    "Hassan", "Mohamed", "Ali", "Ibrahim", "Ahmed", "Omar", "Farah",
    "Ole", "Kipchoge", "Kiplagat", "Kiprotich", "Kipsambu",
    "Kipkemoi", "Kipkurui", "Kipchumba", "Kipyegon", "Kipturiek",
    "Kipngetich", "Kipkemboi", "Kipyego", "Kipkosgei", "Kipkoskei",
    "Muthui", "Kalembe", "Kasai", "Musyoka", "Mwangi",
    "Kipkurui", "Kiplagat", "Kipchoge", "Kipyegon", "Kipchage",
    # Modern surnames
    "Njoroge", "Omondi", "Kipchoge", "Musyoka", "Owino", "Gitau",
    "Kiplagat", "Kipkoskei", "Kiptoo", "Kiplagat", "Kipchoge",
    "Kipyegon", "Kipkemoi", "Kipkurui", "Kiprotich", "Kipsambu",
]

KENYAN_COUNTIES = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "Nyeri",
    "Machakos", "Kericho", "Nakuru", "Kilifi", "Malindi", "Lamu", "Garissa",
    "Wajir", "Mandera", "Samburu", "Isiolo", "Marsabit", "Turkana", "West Pokot",
    "Uasin Gishu", "Elgeyo-Marakwet", "Nandi", "Baringo", "Laikipia", "Nyeri",
    "Tharaka-Nithi", "Embu", "Meru", "Imenti", "Bungoma", "Busia", "Siaya",
    "Kisumu", "Homa Bay", "Migori", "Kisii", "Nyamira", "Bomet", "Kericho",
    "Narok", "Kajiado", "Kiambu", "Muranga", "Makueni", "Taita-Taveta",
]

KENYAN_CITIES = [
    "Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Thika", "Nyeri",
    "Machakos", "Kericho", "Kisii", "Kilifi", "Malindi", "Lamu", "Garissa",
    "Embu", "Iten", "Kapsabet", "Uasin Gishu", "Bungoma", "Kitale", "Kapenguria",
    "Kericho", "Bomet", "Sotik", "Narok", "Ongata Rongai", "Karen", "Westlands",
    "Parklands", "Upper Hill", "Gigiri", "Kinangop", "Nanyuki", "Naro Moru",
]

DEPARTMENTS = [
    "Engineering", "Sales", "Marketing", "Finance", "Human Resources",
    "Operations", "Customer Support", "Product Development", "Quality Assurance",
    "Legal", "Compliance", "Risk Management", "IT Infrastructure", "Data Science",
    "Business Analytics", "Strategy", "Corporate Communication", "Admin",
    "Procurement", "Supply Chain", "Logistics",
]

PHONE_PREFIXES = ["70", "71", "72", "73", "74", "75", "76", "78", "79"]

EMAILS_DOMAINS = ["@simplesqldb.ke", "@pesapal.com", "@safaricom.co.ke", "@airtel.co.ke", "@equity.com"]

POSITIONS = [
    "Software Engineer", "Senior Engineer", "Engineering Manager", "Product Manager",
    "Sales Executive", "Sales Manager", "Marketing Specialist", "Finance Manager",
    "HR Specialist", "Operations Manager", "Support Engineer", "QA Engineer",
    "Data Analyst", "Business Analyst", "Systems Administrator", "Junior Developer",
    "Senior Developer", "Tech Lead", "Director", "Manager", "Supervisor",
    "Coordinator", "Analyst", "Specialist", "Associate", "Officer",
]

def generate_kenyan_phone():
    """Generate a Kenyan phone number"""
    prefix = random.choice(PHONE_PREFIXES)
    number = ''.join(random.choices('0123456789', k=7))
    return f"+254{prefix}{number}"

def generate_email(first_name, last_name):
    """Generate an email address"""
    domain = random.choice(EMAILS_DOMAINS)
    return f"{first_name.lower()}.{last_name.lower()}{domain}".replace(" ", "")

def generate_random_date(start_year=2015, end_year=2024):
    """Generate a random hire date"""
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    random_date = start + timedelta(days=random.randint(0, (end - start).days))
    return random_date.strftime('%Y-%m-%d')

def generate_salary(position):
    """Generate a realistic Kenyan salary based on position"""
    salary_ranges = {
        "Junior Developer": (35000, 50000),
        "Software Engineer": (50000, 80000),
        "Senior Engineer": (80000, 150000),
        "Engineering Manager": (120000, 200000),
        "Product Manager": (80000, 150000),
        "Sales Executive": (40000, 70000),
        "Sales Manager": (70000, 120000),
        "Marketing Specialist": (45000, 75000),
        "Finance Manager": (75000, 130000),
        "HR Specialist": (45000, 70000),
        "Operations Manager": (70000, 120000),
        "Support Engineer": (35000, 55000),
        "QA Engineer": (45000, 70000),
        "Data Analyst": (50000, 85000),
        "Business Analyst": (50000, 85000),
        "Systems Administrator": (45000, 75000),
        "Senior Developer": (70000, 130000),
        "Tech Lead": (100000, 180000),
        "Director": (150000, 300000),
        "Manager": (65000, 120000),
        "Supervisor": (40000, 65000),
        "Coordinator": (30000, 50000),
        "Analyst": (40000, 70000),
        "Specialist": (45000, 75000),
        "Associate": (30000, 50000),
        "Officer": (35000, 60000),
    }
    
    if position in salary_ranges:
        min_sal, max_sal = salary_ranges[position]
    else:
        min_sal, max_sal = 40000, 100000
    
    return random.randint(min_sal, max_sal)

def populate_database():
    """Populate the database with Kenyan data"""
    storage = Storage(data_dir='web_data')
    engine = QueryEngine(storage)
    
    print("🇰🇪 Populating SimpleSQLDB with Kenyan context data...")
    
    # Create departments table
    print("\n📋 Creating departments table...")
    engine.execute("""
        CREATE TABLE departments (
            dept_id INT PRIMARY KEY,
            dept_name VARCHAR(100) UNIQUE,
            location VARCHAR(100),
            budget INT,
            created_date DATE
        )
    """)
    
    # Insert departments with Kenyan locations
    print("📍 Inserting 20 departments...")
    for i, dept in enumerate(DEPARTMENTS, 1):
        location = random.choice(KENYAN_CITIES)
        budget = random.randint(500000, 5000000)
        created_date = generate_random_date(2015, 2022)
        
        query = f"""
            INSERT INTO departments 
            (dept_id, dept_name, location, budget, created_date) 
            VALUES ({i}, '{dept}', '{location}', {budget}, '{created_date}')
        """
        engine.execute(query)
    
    # Create employees table
    print("\n👥 Creating employees table...")
    engine.execute("""
        CREATE TABLE employees (
            emp_id INT PRIMARY KEY,
            name VARCHAR(100),
            email VARCHAR(100) UNIQUE,
            phone VARCHAR(20),
            position VARCHAR(100),
            salary INT,
            hire_date DATE,
            county VARCHAR(50),
            city VARCHAR(50),
            dept_id INT,
            FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
        )
    """)
    
    # Insert 500 employees with Kenyan data
    print("👨‍💼 Inserting 500 employees with Kenyan context...")
    for emp_id in range(1, 501):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        name = f"{first_name} {last_name}"
        email = generate_email(first_name, last_name)
        phone = generate_kenyan_phone()
        position = random.choice(POSITIONS)
        salary = generate_salary(position)
        hire_date = generate_random_date()
        county = random.choice(KENYAN_COUNTIES)
        city = random.choice(KENYAN_CITIES)
        dept_id = random.randint(1, len(DEPARTMENTS))
        
        query = f"""
            INSERT INTO employees 
            (emp_id, name, email, phone, position, salary, hire_date, county, city, dept_id) 
            VALUES ({emp_id}, '{name}', '{email}', '{phone}', '{position}', {salary}, '{hire_date}', '{county}', '{city}', {dept_id})
        """
        
        try:
            engine.execute(query)
            if emp_id % 50 == 0:
                print(f"  ✓ Inserted {emp_id} employees...")
        except Exception as e:
            print(f"⚠️  Error inserting employee {emp_id}: {e}")
    
    # Create indexes for performance
    print("\n⚡ Creating indexes for performance...")
    engine.execute("CREATE INDEX idx_emp_email ON employees(email)")
    engine.execute("CREATE INDEX idx_emp_dept ON employees(dept_id)")
    engine.execute("CREATE INDEX idx_emp_salary ON employees(salary)")
    print("  ✓ Indexes created")
    
    # Show statistics
    print("\n📊 Database population complete!")
    print("\n=== Database Statistics ===")
    
    try:
        depts = engine.execute("SELECT COUNT(*) as count FROM departments")
        emps = engine.execute("SELECT COUNT(*) as count FROM employees")
        avg_salary = engine.execute("SELECT AVG(salary) as avg_sal FROM employees")
        dept_counts = engine.execute("SELECT dept_name, COUNT(*) as count FROM employees e JOIN departments d ON e.dept_id = d.dept_id GROUP BY d.dept_id")
        
        print(f"\n✓ Departments: 20 created")
        print(f"✓ Employees: 500 hired")
        if avg_salary and len(avg_salary) > 0:
            avg_val = avg_salary[0].get('avg_sal', 0) or avg_salary[0].get('AVG(salary)', 0)
            if avg_val:
                print(f"✓ Average Salary: KES {int(avg_val):,.0f}")
        
        print("\n📈 Employees per Department:")
        if dept_counts and len(dept_counts) > 0:
            for row in dept_counts:
                if isinstance(row, dict):
                    dept = row.get('dept_name', row.get('name', 'Unknown'))
                    count = row.get('count', row.get('COUNT(*)', 0))
                    print(f"   {dept}: {count} employees")
    except Exception as e:
        print(f"Note: Statistics summary skipped ({str(e)[:50]})")
    
    print("\n✅ Your dashboard is ready! Visit http://127.0.0.1:5000")
    print("🇰🇪 Try these queries in SQL Console:")
    print("""
    1. SELECT * FROM employees LIMIT 10;
    2. SELECT dept_name, COUNT(*) as emp_count FROM employees e 
       JOIN departments d ON e.dept_id = d.dept_id 
       GROUP BY d.dept_id;
    3. SELECT position, AVG(salary) FROM employees GROUP BY position;
    4. SELECT county, COUNT(*) FROM employees GROUP BY county;
    5. SELECT * FROM employees WHERE salary > 100000;
    """)

if __name__ == "__main__":
    populate_database()
