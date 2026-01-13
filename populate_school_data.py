"""
Populate School ERP System with Sample Data
Generates realistic school data for demonstration
"""

import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import QueryEngine
from core.storage import Storage

# Sample data
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
               "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
               "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra",
               "Donald", "Ashley", "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]

KENYAN_STREETS = ["Kenyatta Avenue", "Moi Avenue", "University Way", "Ngong Road", "Thika Road", 
                  "Waiyaki Way", "Jogoo Road", "Lang'ata Road", "Kiambu Road", "Limuru Road"]

COURSE_TITLES = [
    ("Introduction to Computer Science", "CS101", "Fundamentals of programming and algorithms"),
    ("Data Structures & Algorithms", "CS201", "Advanced data structures and algorithmic techniques"),
    ("Database Systems", "CS301", "Relational databases and SQL"),
    ("Web Development", "CS202", "HTML, CSS, JavaScript, and frameworks"),
    ("Calculus I", "MATH101", "Limits, derivatives, and integrals"),
    ("Linear Algebra", "MATH201", "Vectors, matrices, and transformations"),
    ("Physics I", "PHY101", "Classical mechanics and thermodynamics"),
    ("Chemistry I", "CHEM101", "Atomic structure and chemical reactions"),
    ("English Composition", "ENG101", "Academic writing and critical thinking"),
    ("Business Management", "BUS201", "Principles of management and organization"),
    ("Marketing Fundamentals", "BUS301", "Marketing strategies and consumer behavior"),
    ("Financial Accounting", "ACC101", "Principles of accounting and financial statements"),
    ("Microeconomics", "ECON201", "Supply, demand, and market structures"),
    ("Psychology 101", "PSY101", "Introduction to psychological concepts"),
    ("Sociology", "SOC101", "Social structures and cultural dynamics")
]

BOOK_TITLES = [
    ("Introduction to Algorithms", "Cormen et al.", "Computer Science"),
    ("Clean Code", "Robert Martin", "Programming"),
    ("Design Patterns", "Gang of Four", "Software Engineering"),
    ("The Pragmatic Programmer", "Hunt & Thomas", "Programming"),
    ("Calculus Early Transcendentals", "James Stewart", "Mathematics"),
    ("Linear Algebra Done Right", "Sheldon Axler", "Mathematics"),
    ("Physics for Scientists", "Serway & Jewett", "Physics"),
    ("Chemistry: The Central Science", "Brown et al.", "Chemistry"),
    ("Principles of Economics", "Mankiw", "Economics"),
    ("Psychology", "David Myers", "Psychology")
]

def populate_school_data():
    """Populate the school database with sample data"""
    
    print("\n" + "="*60)
    print("📊 Populating School ERP with Sample Data")
    print("="*60 + "\n")
    
    storage = Storage(data_dir='school_data')
    engine = QueryEngine(storage)
    
    # Clear existing data (if any)
    print("🗑️  Clearing existing data...")
    for table in storage.list_tables():
        try:
            engine.execute(f"DELETE FROM {table}")
        except:
            pass
    
    # Generate Students (500)
    print("\n👨‍🎓 Creating 500 students...")
    student_ids = []
    for i in range(500):
        user_id = 1000 + i
        student_ids.append(user_id)
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}{i}@school.edu"
        phone = f"+2547{random.randint(10000000, 99999999)}"
        address = f"{random.randint(1, 999)} {random.choice(KENYAN_STREETS)}, Nairobi"
        dob = f"{random.randint(2003, 2008)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        enrollment = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        
        engine.execute(f"""
            INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
            VALUES ({user_id}, '{first_name} {last_name}', '{email}', 'Student', 
                    '{phone}', '{address}', '{dob}', '{enrollment}')
        """)
    
    print(f"✅ Created {len(student_ids)} students")
    
    # Generate Teachers (30)
    print("\n👨‍🏫 Creating 30 teachers...")
    teacher_ids = []
    for i in range(30):
        user_id = 2000 + i
        teacher_ids.append(user_id)
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        email = f"{first_name.lower()}.{last_name.lower()}.teacher@school.edu"
        phone = f"+2547{random.randint(10000000, 99999999)}"
        address = f"{random.randint(1, 999)} {random.choice(KENYAN_STREETS)}, Nairobi"
        dob = f"{random.randint(1975, 1995)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        enrollment = f"{random.randint(2015, 2023)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        
        engine.execute(f"""
            INSERT INTO users (id, name, email, role, phone, address, date_of_birth, enrollment_date)
            VALUES ({user_id}, 'Prof. {first_name} {last_name}', '{email}', 'Teacher', 
                    '{phone}', '{address}', '{dob}', '{enrollment}')
        """)
    
    print(f"✅ Created {len(teacher_ids)} teachers")
    
    # Generate Courses (15)
    print("\n📚 Creating 15 courses...")
    course_ids = []
    for i, (title, code, description) in enumerate(COURSE_TITLES):
        course_id = 100 + i
        course_ids.append(course_id)
        teacher_id = random.choice(teacher_ids)
        credits = random.choice([3, 4])
        semester = random.choice(["Fall 2026", "Spring 2026"])
        capacity = random.randint(30, 50)
        room = f"Room {random.randint(101, 450)}"
        
        engine.execute(f"""
            INSERT INTO courses (id, title, code, description, teacher_id, credits, semester, capacity, room)
            VALUES ({course_id}, '{title}', '{code}', '{description}', {teacher_id}, 
                    {credits}, '{semester}', {capacity}, '{room}')
        """)
    
    print(f"✅ Created {len(course_ids)} courses")
    
    # Generate Enrollments (2000+)
    print("\n📝 Creating enrollments (students enrolled in courses)...")
    enrollment_id = 10000
    grades = ["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D", "F", "N/A"]
    statuses = ["Active", "Active", "Active", "Completed", "Dropped"]
    
    for student_id in random.sample(student_ids, min(400, len(student_ids))):
        courses_to_enroll = random.sample(course_ids, random.randint(3, 6))
        for course_id in courses_to_enroll:
            enrollment_id += 1
            grade = random.choice(grades)
            status = random.choice(statuses)
            midterm = round(random.uniform(40, 100), 1)
            final = round(random.uniform(40, 100), 1)
            enrollment_date = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            
            engine.execute(f"""
                INSERT INTO enrollments (id, student_id, course_id, grade, enrollment_date, status, midterm_score, final_score)
                VALUES ({enrollment_id}, {student_id}, {course_id}, '{grade}', '{enrollment_date}', 
                        '{status}', {midterm}, {final})
            """)
    
    print(f"✅ Created {enrollment_id - 10000} enrollments")
    
    # Generate Financials
    print("\n💰 Creating financial records...")
    financial_id = 50000
    for student_id in random.sample(student_ids, min(500, len(student_ids))):
        financial_id += 1
        semester = random.choice(["Fall 2026", "Spring 2026"])
        total_fees = round(random.uniform(50000, 150000), 2)
        fees_paid = round(random.uniform(0, total_fees), 2)
        balance = round(total_fees - fees_paid, 2)
        payment_date = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        payment_status = "Paid" if balance <= 0 else ("Partial" if fees_paid > 0 else "Pending")
        
        engine.execute(f"""
            INSERT INTO financials (id, student_id, semester, total_fees, fees_paid, balance, payment_date, payment_status)
            VALUES ({financial_id}, {student_id}, '{semester}', {total_fees}, {fees_paid}, 
                    {balance}, '{payment_date}', '{payment_status}')
        """)
    
    print(f"✅ Created {financial_id - 50000} financial records")
    
    # Generate Attendance Records
    print("\n📋 Creating attendance records...")
    attendance_id = 60000
    for _ in range(1000):
        attendance_id += 1
        student_id = random.choice(student_ids[:100])
        course_id = random.choice(course_ids)
        date = f"2024-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        status = random.choice(["Present", "Present", "Present", "Absent", "Late"])
        remarks = random.choice(["", "", "Medical excuse", "Family emergency", ""])
        
        engine.execute(f"""
            INSERT INTO attendance (id, student_id, course_id, date, status, remarks)
            VALUES ({attendance_id}, {student_id}, {course_id}, '{date}', '{status}', '{remarks}')
        """)
    
    print(f"✅ Created {attendance_id - 60000} attendance records")
    
    # Generate Library Books
    print("\n📖 Creating library books...")
    book_id = 300
    for i, (title, author, category) in enumerate(BOOK_TITLES):
        book_id += 1
        isbn = f"978-{random.randint(0, 9)}-{random.randint(100, 999)}-{random.randint(10000, 99999)}-{random.randint(0, 9)}"
        total_copies = random.randint(3, 10)
        available_copies = random.randint(0, total_copies)
        shelf_location = f"{random.choice(['A', 'B', 'C', 'D'])}-{random.randint(1, 20):02d}-{random.randint(1, 10):02d}"
        
        engine.execute(f"""
            INSERT INTO books (id, title, author, isbn, category, total_copies, available_copies, shelf_location)
            VALUES ({book_id}, '{title}', '{author}', '{isbn}', '{category}', 
                    {total_copies}, {available_copies}, '{shelf_location}')
        """)
    
    print(f"✅ Created {book_id - 300} books")
    
    # Generate Book Borrowings
    print("\n📚 Creating book borrowing records...")
    borrowing_id = 70000
    for _ in range(200):
        borrowing_id += 1
        student_id = random.choice(student_ids[:100])
        book_id_sample = random.randint(301, 310)
        borrow_date = datetime.now() - timedelta(days=random.randint(0, 30))
        due_date = borrow_date + timedelta(days=14)
        return_date_obj = None if random.random() > 0.7 else borrow_date + timedelta(days=random.randint(1, 20))
        status = "Returned" if return_date_obj else "Borrowed"
        fine = 0 if status == "Returned" else (random.randint(0, 500) if random.random() > 0.8 else 0)
        
        borrow_str = borrow_date.strftime("%Y-%m-%d")
        due_str = due_date.strftime("%Y-%m-%d")
        return_str = return_date_obj.strftime("%Y-%m-%d") if return_date_obj else "NULL"
        
        engine.execute(f"""
            INSERT INTO borrowings (id, student_id, book_id, borrow_date, due_date, return_date, status, fine)
            VALUES ({borrowing_id}, {student_id}, {book_id_sample}, '{borrow_str}', '{due_str}', 
                    {f"'{return_str}'" if return_str != "NULL" else "NULL"}, '{status}', {fine})
        """)
    
    print(f"✅ Created {borrowing_id - 70000} borrowing records")
    
    print("\n" + "="*60)
    print("✅ School ERP Database Population Complete!")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   • {len(student_ids)} Students")
    print(f"   • {len(teacher_ids)} Teachers")
    print(f"   • {len(course_ids)} Courses")
    print(f"   • {enrollment_id - 10000} Enrollments")
    print(f"   • {financial_id - 50000} Financial Records")
    print(f"   • {attendance_id - 60000} Attendance Records")
    print(f"   • {book_id - 300} Library Books")
    print(f"   • {borrowing_id - 70000} Book Borrowings")
    print(f"\n🚀 Ready to test the School ERP system!\n")

if __name__ == "__main__":
    populate_school_data()
