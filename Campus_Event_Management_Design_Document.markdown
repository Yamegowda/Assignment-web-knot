# Campus Event Management Platform - Design Document

## 1. System Overview

The Campus Event Management Platform is designed to facilitate event management across multiple colleges. It comprises two main components:

- **Admin Portal (Web)**: Enables college staff to manage events, including creation, updates, and reporting.
- **Student App (Mobile)**: Allows students to browse events, register, and track attendance.

This document focuses on the **Event Reporting System**, which tracks and analyzes event data across multiple colleges to provide insights into event popularity, student participation, and other metrics.

## 2. Assumptions & Decisions

### Scale Assumptions
- **Colleges**: 50 colleges using the platform.
- **Students**: Approximately 500 students per college, totaling 25,000 students.
- **Events**: Approximately 20 events per semester per college, totaling 1,000 events per semester.

### Key Decisions
- **Multi-tenant Architecture**: Each college operates as a separate tenant with isolated data to ensure data privacy and separation.
- **Global Event IDs**: Event IDs are unique across all colleges, using UUID format for scalability and uniqueness.
- **Centralized Database**: A single database with college-based partitioning to enable efficient cross-college analytics.
- **Event Types**: Supported event types include Workshop, Hackathon, Tech Talk, Fest, Seminar, and Cultural Event.
- **Attendance Window**: Students can check in from 30 minutes before the event start time to 2 hours after the event start time.
- **Edge Cases Handled**:
  - **Duplicate Student Registrations**: Prevented using unique constraints on event_id and student_id.
  - **Late Registrations**: Allowed up to the event start time.
  - **Missing Feedback**: Feedback is optional, with default null values.
  - **Event Cancellations**: Handled via soft deletes by updating the event status.
  - **Capacity Limits**: Enforced to prevent over-registration.

## 3. Data Model & Database Schema

### Core Entities

#### Colleges
```sql
CREATE TABLE colleges (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    contact_email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Students
```sql
CREATE TABLE students (
    id UUID PRIMARY KEY,
    college_id UUID REFERENCES colleges(id),
    student_id VARCHAR(50) NOT NULL, -- College-specific ID
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(15),
    year INTEGER,
    department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Events
```sql
CREATE TABLE events (
    id UUID PRIMARY KEY,
    college_id UUID REFERENCES colleges(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    event_type VARCHAR(50) NOT NULL,
    start_datetime TIMESTAMP NOT NULL,
    end_datetime TIMESTAMP NOT NULL,
    location VARCHAR(255),
    max_capacity INTEGER,
    current_registrations INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Registrations
```sql
CREATE TABLE registrations (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id),
    student_id UUID REFERENCES students(id),
    registration_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'registered',
    UNIQUE(event_id, student_id)
);
```

#### Attendance
```sql
CREATE TABLE attendance (
    id UUID PRIMARY KEY,
    registration_id UUID REFERENCES registrations(id),
    check_in_time TIMESTAMP NOT NULL,
    check_out_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Feedback
```sql
CREATE TABLE feedback (
    id UUID PRIMARY KEY,
    registration_id UUID REFERENCES registrations(id),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    comments TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### ER Diagram Relationships
- **Colleges (1:N) Students**: One college can have many students.
- **Colleges (1:N) Events**: One college can host many events.
- **Events (1:N) Registrations**: One event can have many registrations.
- **Students (1:N) Registrations**: One student can register for many events.
- **Registrations (1:1) Attendance**: Each registration can have one attendance record.
- **Registrations (1:1) Feedback**: Each registration can have one feedback record.

## 4. API Design

### Base URL
`https://api.campusevents.com/v1`

### College Management
- **GET /colleges**
  - Description: List all colleges.
  - Response: Array of college objects with id, name, location, contact_email, and created_at.
- **POST /colleges**
  - Description: Create a new college.
  - Request Body: `{ name, location, contact_email }`
  - Response: Created college object, status 201.
- **GET /colleges/{id}**
  - Description: Get details of a specific college.
  - Response: College object or 404 if not found.

### Student Management
- **GET /colleges/{college_id}/students**
  - Description: List all students for a specific college.
  - Response: Array of student objects.
- **POST /colleges/{college_id}/students**
  - Description: Register a new student for a college.
  - Request Body: `{ student_id, name, email, phone, year, department }`
  - Response: Created student object, status 201.
- **GET /students/{id}**
  - Description: Get a student's profile.
  - Response: Student object or 404 if not found.

### Event Management
- **GET /colleges/{college_id}/events**
  - Description: List all events for a specific college.
  - Response: Array of event objects.
- **POST /colleges/{college_id}/events**
  - Description: Create a new event for a college.
  - Request Body: `{ title, description, event_type, start_datetime, end_datetime, location, max_capacity }`
  - Response: Created event object, status 201.
- **GET /events/{id}**
  - Description: Get details of a specific event.
  - Response: Event object or 404 if not found.
- **PUT /events/{id}**
  - Description: Update an existing event.
  - Request Body: Updated event fields.
  - Response: Updated event object.
- **DELETE /events/{id}**
  - Description: Cancel an event (soft delete by updating status).
  - Response: Success message or 404 if not found.

### Registration & Attendance
- **POST /events/{event_id}/register**
  - Description: Register a student for an event.
  - Request Body: `{ student_id }`
  - Response: Created registration object, status 201.
- **DELETE /events/{event_id}/register/{student_id}**
  - Description: Cancel a student's registration for an event.
  - Response: Success message or 404 if not found.
- **POST /registrations/{registration_id}/checkin**
  - Description: Mark a student's check-in for an event.
  - Response: Created attendance object, status 201.
- **POST /registrations/{registration_id}/checkout**
  - Description: Mark a student's check-out for an event.
  - Response: Updated attendance object.

### Feedback
- **POST /registrations/{registration_id}/feedback**
  - Description: Submit feedback for an event.
  - Request Body: `{ rating, comments }`
  - Response: Created feedback object, status 201.
- **GET /events/{event_id}/feedback**
  - Description: Get all feedback for a specific event.
  - Response: Array of feedback objects.

### Reporting APIs
- **GET /reports/events/popularity**
  - Description: Generate a report of events sorted by registration count.
  - Response: Report with event details and registration counts.
- **GET /reports/students/participation**
  - Description: Generate a report of student participation across events.
  - Response: Report with student details, registration, and attendance stats.
- **GET /reports/students/top-active**
  - Description: List the top 3 most active students based on attendance.
  - Response: Report with top 3 students and their event counts.
- **GET /reports/events/analytics**
  - Description: Generate comprehensive event analytics with optional filters (e.g., event_type, college_id).
  - Response: Report with event metrics, attendance rates, and average ratings.

## 5. Workflows

### Student Registration Flow
1. Student browses available events in the mobile app.
2. Student selects an event and clicks "Register."
3. System validates:
   - Event capacity has not been exceeded.
   - Student is not already registered for the event.
   - Registration deadline (event start time) has not passed.
4. Create a registration record in the `registrations` table.
5. Increment the `current_registrations` count in the `events` table.
6. Send a confirmation notification to the student.

### Attendance Marking Flow
1. Student arrives at the event venue.
2. Student scans a QR code or provides their registration ID via the mobile app.
3. System validates:
   - A valid registration exists for the student and event.
   - Current time is within the attendance window (30 minutes before to 2 hours after event start).
   - Student has not already checked in.
4. Create an attendance record in the `attendance` table with `check_in_time`.
5. Update the registration status to 'attended' in the `registrations` table.

### Report Generation Flow
1. Admin requests a specific report via the admin portal.
2. System queries relevant tables (e.g., `events`, `registrations`, `attendance`, `feedback`) with applied filters.
3. Aggregate data based on the report type (e.g., count registrations, calculate attendance rates).
4. Format the response with metrics and insights.
5. Return paginated results to the admin.

## 6. Security Considerations
- **Authentication**: Use JWT tokens for secure API access.
- **Authorization**: Implement role-based access control (Admin, Student, Super Admin).
- **Data Validation**: Sanitize and validate all inputs to prevent injection attacks.
- **Rate Limiting**: Apply API throttling to prevent abuse and ensure fair usage.
- **College Isolation**: Restrict data access to college-specific data to maintain tenant isolation.

## 7. Performance Optimizations
- **Database Indexing**: Create indexes on frequently queried fields (`college_id`, `event_id`, `student_id`) for faster queries.
- **Pagination**: Implement pagination for API endpoints returning large datasets.
- **Caching**: Use Redis to cache frequently accessed data, such as event lists or reports.
- **Connection Pooling**: Configure database connection pooling to optimize database access.

## 8. Future Enhancements
- **Real-time Notifications**: Implement WebSockets for instant event updates and notifications.
- **College Authentication Integration**: Integrate with college authentication systems (e.g., SSO).
- **Mobile App APIs**: Develop APIs with push notification support for the student app.
- **Advanced Analytics**: Incorporate machine learning for predictive insights (e.g., event popularity).
- **Event Recommendation System**: Suggest events to students based on their interests and participation history.
- **Multi-language Support**: Add support for multiple languages to enhance accessibility.