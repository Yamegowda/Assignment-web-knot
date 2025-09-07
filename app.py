from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__)

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///campus_events.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database Models
class College(db.Model):
    __tablename__ = 'colleges'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    students = db.relationship('Student', backref='college', lazy=True)
    events = db.relationship('Event', backref='college', lazy=True)

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone = db.Column(db.String(15))
    year = db.Column(db.Integer)
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    registrations = db.relationship('Registration', backref='student', lazy=True)

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    college_id = db.Column(db.Integer, db.ForeignKey('colleges.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50), nullable=False)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(255))
    max_capacity = db.Column(db.Integer)
    current_registrations = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    registrations = db.relationship('Registration', backref='event', lazy=True)

class Registration(db.Model):
    __tablename__ = 'registrations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    registration_time = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='registered')
    
    attendance = db.relationship('Attendance', backref='registration', uselist=False)
    feedback = db.relationship('Feedback', backref='registration', uselist=False)
    
    __table_args__ = (db.UniqueConstraint('event_id', 'student_id'),)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), nullable=False)
    check_in_time = db.Column(db.DateTime, nullable=False)
    check_out_time = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    registration_id = db.Column(db.Integer, db.ForeignKey('registrations.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper Functions
def to_dict(model):
    """Convert SQLAlchemy model to dictionary"""
    return {column.name: getattr(model, column.name) for column in model.__table__.columns}

# ---------------------------
# API Routes
# ---------------------------

# College Management
@app.route('/api/colleges', methods=['GET'])
def get_colleges():
    colleges = College.query.all()
    return jsonify([to_dict(college) for college in colleges])

@app.route('/api/colleges', methods=['POST'])
def create_college():
    data = request.get_json()
    college = College(
        name=data['name'],
        location=data.get('location'),
        contact_email=data.get('contact_email')
    )
    db.session.add(college)
    db.session.commit()
    return jsonify(to_dict(college)), 201

# Student Management
@app.route('/api/colleges/<int:college_id>/students', methods=['GET'])
def get_students(college_id):
    students = Student.query.filter_by(college_id=college_id).all()
    return jsonify([to_dict(student) for student in students])

@app.route('/api/colleges/<int:college_id>/students', methods=['POST'])
def create_student(college_id):
    data = request.get_json()
    student = Student(
        college_id=college_id,
        student_id=data['student_id'],
        name=data['name'],
        email=data['email'],
        phone=data.get('phone'),
        year=data.get('year'),
        department=data.get('department')
    )
    db.session.add(student)
    db.session.commit()
    return jsonify(to_dict(student)), 201

# Event Management
@app.route('/api/colleges/<int:college_id>/events', methods=['GET'])
def get_events(college_id):
    events = Event.query.filter_by(college_id=college_id).all()
    return jsonify([to_dict(event) for event in events])

@app.route('/api/colleges/<int:college_id>/events', methods=['POST'])
def create_event(college_id):
    data = request.get_json()
    event = Event(
        college_id=college_id,
        title=data['title'],
        description=data.get('description'),
        event_type=data['event_type'],
        start_datetime=datetime.fromisoformat(data['start_datetime']),
        end_datetime=datetime.fromisoformat(data['end_datetime']),
        location=data.get('location'),
        max_capacity=data.get('max_capacity', 100)
    )
    db.session.add(event)
    db.session.commit()
    return jsonify(to_dict(event)), 201

@app.route('/api/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event = Event.query.get_or_404(event_id)
    return jsonify(to_dict(event))

# Registration Management
@app.route('/api/events/<int:event_id>/register', methods=['POST'])
def register_student(event_id):
    data = request.get_json()
    student_id = data['student_id']
    
    # Check if student is already registered
    existing = Registration.query.filter_by(event_id=event_id, student_id=student_id).first()
    if existing:
        return jsonify({'error': 'Student already registered for this event'}), 400
    
    # Check event capacity
    event = Event.query.get_or_404(event_id)
    if event.current_registrations >= event.max_capacity:
        return jsonify({'error': 'Event is at full capacity'}), 400
    
    # Create registration
    registration = Registration(event_id=event_id, student_id=student_id)
    event.current_registrations += 1
    
    db.session.add(registration)
    db.session.commit()
    
    return jsonify(to_dict(registration)), 201

@app.route('/api/registrations/<int:registration_id>/checkin', methods=['POST'])
def checkin_student(registration_id):
    registration = Registration.query.get_or_404(registration_id)
    
    # Check if already checked in
    if registration.attendance:
        return jsonify({'error': 'Student already checked in'}), 400
    
    # Create attendance record
    attendance = Attendance(
        registration_id=registration_id,
        check_in_time=datetime.utcnow()
    )
    registration.status = 'attended'
    
    db.session.add(attendance)
    db.session.commit()
    
    return jsonify(to_dict(attendance)), 201

# Feedback Management
@app.route('/api/registrations/<int:registration_id>/feedback', methods=['POST'])
def submit_feedback(registration_id):
    data = request.get_json()
    
    # Validate rating
    rating = data.get('rating')
    if not rating or rating < 1 or rating > 5:
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    
    # Check if feedback already exists
    existing_feedback = Feedback.query.filter_by(registration_id=registration_id).first()
    if existing_feedback:
        return jsonify({'error': 'Feedback already submitted'}), 400
    
    feedback = Feedback(
        registration_id=registration_id,
        rating=rating,
        comments=data.get('comments')
    )
    
    db.session.add(feedback)
    db.session.commit()
    
    return jsonify(to_dict(feedback)), 201

# Reporting APIs
@app.route('/api/reports/events/popularity', methods=['GET'])
def event_popularity_report():
    """Get events sorted by number of registrations"""
    results = db.session.query(
        Event.id,
        Event.title,
        Event.event_type,
        Event.current_registrations,
        College.name.label('college_name')
    ).join(College).order_by(Event.current_registrations.desc()).all()
    
    report = []
    for result in results:
        report.append({
            'event_id': result.id,
            'title': result.title,
            'event_type': result.event_type,
            'registrations': result.current_registrations,
            'college': result.college_name
        })
    
    return jsonify({
        'report_type': 'Event Popularity',
        'total_events': len(report),
        'data': report
    })

@app.route('/api/reports/students/participation', methods=['GET'])
def student_participation_report():
    """Get student participation statistics"""
    results = db.session.query(
        Student.id,
        Student.name,
        Student.email,
        College.name.label('college_name'),
        db.func.count(Registration.id).label('total_registrations'),
        db.func.count(Attendance.id).label('total_attended')
    ).join(College).outerjoin(Registration).outerjoin(Attendance).group_by(
        Student.id, Student.name, Student.email, College.name
    ).order_by(db.func.count(Registration.id).desc()).all()
    
    report = []
    for result in results:
        attendance_rate = 0
        if result.total_registrations > 0:
            attendance_rate = (result.total_attended / result.total_registrations) * 100
        
        report.append({
            'student_id': result.id,
            'name': result.name,
            'email': result.email,
            'college': result.college_name,
            'total_registrations': result.total_registrations,
            'total_attended': result.total_attended,
            'attendance_rate': round(attendance_rate, 2)
        })
    
    return jsonify({
        'report_type': 'Student Participation',
        'total_students': len(report),
        'data': report
    })

@app.route('/api/reports/students/top-active', methods=['GET'])
def top_active_students():
    """Get top 3 most active students"""
    results = db.session.query(
        Student.id,
        Student.name,
        Student.email,
        College.name.label('college_name'),
        db.func.count(Attendance.id).label('events_attended')
    ).join(College).join(Registration).join(Attendance).group_by(
        Student.id, Student.name, Student.email, College.name
    ).order_by(db.func.count(Attendance.id).desc()).limit(3).all()
    
    report = []
    for i, result in enumerate(results, 1):
        report.append({
            'rank': i,
            'student_id': result.id,
            'name': result.name,
            'email': result.email,
            'college': result.college_name,
            'events_attended': result.events_attended
        })
    
    return jsonify({
        'report_type': 'Top 3 Most Active Students',
        'data': report
    })

@app.route('/api/reports/events/analytics', methods=['GET'])
def event_analytics():
    """Get comprehensive event analytics with filters"""
    event_type = request.args.get('event_type')
    college_id = request.args.get('college_id')
    
    query = db.session.query(
        Event.id,
        Event.title,
        Event.event_type,
        College.name.label('college_name'),
        Event.current_registrations,
        db.func.count(Attendance.id).label('total_attended'),
        db.func.avg(Feedback.rating).label('avg_rating')
    ).join(College).outerjoin(Registration).outerjoin(Attendance).outerjoin(Feedback).group_by(
        Event.id, Event.title, Event.event_type, College.name, Event.current_registrations
    )
    
    # Apply filters
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if college_id:
        query = query.filter(Event.college_id == college_id)
    
    results = query.all()
    
    report = []
    for result in results:
        attendance_rate = 0
        if result.current_registrations > 0:
            attendance_rate = (result.total_attended / result.current_registrations) * 100
        
        report.append({
            'event_id': result.id,
            'title': result.title,
            'event_type': result.event_type,
            'college': result.college_name,
            'registrations': result.current_registrations,
            'attended': result.total_attended,
            'attendance_rate': round(attendance_rate, 2),
            'avg_rating': round(float(result.avg_rating or 0), 2)
        })
    
    return jsonify({
        'report_type': 'Event Analytics',
        'filters': {
            'event_type': event_type,
            'college_id': college_id
        },
        'total_events': len(report),
        'data': report
    })

# ---------------------------
# Initialize Database at Startup
# ---------------------------
with app.app_context():
    db.create_all()
    
    # Add sample data if tables are empty
    if College.query.count() == 0:
        # Sample Colleges
        college1 = College(
            name="City College",
            location="Delhi",
            contact_email="contact@citycollege.edu"
        )
        college2 = College(
            name="Global Institute",
            location="Chennai",
            contact_email="info@globalinstitute.edu"
        )
        
        db.session.add_all([college1, college2])
        db.session.commit()
        
        # Sample Students
        student1 = Student(
            college_id=college1.id,
            student_id="CC2023001",
            name="Rahul Gupta",
            email="rahul.gupta@citycollege.edu",
            phone="9876543210",
            year=3,
            department="Electrical Engineering"
        )
        student2 = Student(
            college_id=college2.id,
            student_id="GI2023002",
            name="Anita Rao",
            email="anita.rao@globalinstitute.edu",
            phone="8765432109",
            year=2,
            department="Mechanical Engineering"
        )
        
        db.session.add_all([student1, student2])
        db.session.commit()
        
        # Sample Events
        event1 = Event(
            college_id=college1.id,
            title="Robotics Workshop",
            description="Hands-on workshop on robotics and automation",
            event_type="Workshop",
            start_datetime=datetime.now() + timedelta(days=5),
            end_datetime=datetime.now() + timedelta(days=5, hours=4),
            location="Main Auditorium",
            max_capacity=60
        )
        event2 = Event(
            college_id=college2.id,
            title="Tech Symposium",
            description="Annual technology symposium with guest speakers",
            event_type="Seminar",
            start_datetime=datetime.now() + timedelta(days=10),
            end_datetime=datetime.now() + timedelta(days=10, hours=6),
            location="Conference Hall",
            max_capacity=100
        )
        
        db.session.add_all([event1, event2])
        db.session.commit()
        
        # Sample Registrations
        registration1 = Registration(
            event_id=event1.id,
            student_id=student1.id
        )
        registration2 = Registration(
            event_id=event2.id,
            student_id=student2.id
        )
        
        event1.current_registrations += 1
        event2.current_registrations += 1
        
        db.session.add_all([registration1, registration2])
        db.session.commit()
        
        # Sample Attendance
        attendance1 = Attendance(
            registration_id=registration1.id,
            check_in_time=datetime.now()
        )
        
        registration1.status = 'attended'
        
        db.session.add(attendance1)
        db.session.commit()
        
        # Sample Feedback
        feedback1 = Feedback(
            registration_id=registration1.id,
            rating=4,
            comments="Very informative workshop!"
        )
        
        db.session.add(feedback1)
        db.session.commit()

# ---------------------------
# Run the Application
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)