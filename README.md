# ReFL3KT - Frictionless Productivity Solution for Students

## Project Description

ReFL3KT is a seamless productivity and goal-tracking platform designed for students. It integrates time tracking, goal setting (with hierarchy and group features), journaling, and analytics into a unified, intuitive workflow. AI-driven prioritization, gamified LUBE points, and minimal manual input ensure students can focus on growth, not admin tasks. The mobile-first approach ensures accessibility and engagement, while group goals and community features foster accountability and collaboration.

---

## Setup Instructions

1. **Clone the Repository**
git clone <repo-url>

2. **Set Up Virtual Environment**
python -m venv venv
venv\Scripts\activate # On Windows

3. **Install Dependencies**
pip install -r requirements.txt

4. **Configure PostgreSQL**
- Install PostgreSQL and create a database/user as per your environment.
- Update `backend/settings.py` with your DB credentials.

5. **Apply Migrations**
python manage.py makemigrations
python manage.py migrate

6. **Run the Development Server**
python manage.py runserver

---

## Tech Stack Used

- **Frontend:** Flutter (Dart)
- **Backend:** Django (Python)
- **Database:** PostgreSQL
- **Other:** Gin (Go, for microservices/AI), SQL

---

## Dependencies

- Django
- Django REST Framework
- psycopg2-binary
- django-cors-headers
- PostgreSQL
- Flutter & Dart SDK (frontend)
- Gin (Go, for AI/microservices, optional)

See `requirements.txt` for full Python dependencies.

---

## Team Details

**Team Mangoes**
- Hrithiq Gupta (CSE AI&ML, 230962300)
- Akshat Pandey (CSE, 230905032)
- Aryan Vivek (IT, 230911172)
- Mohammad Tausif (CSE, 230905330)
- Aditya Sinha (CSE, 230905218)

---

## Workflow Explanation

**User Flow:**
1. **Sign Up/Login:** Secure authentication for students.
2. **Time Tracking:** Log tasks with categories and durations.
3. **Goal Tracking:** Set personal/group goals, track progress, maintain streaks, and earn LUBE points.
4. **Journaling:** Reflect on daily activities and goal progress.
5. **AI Recommendations:** Receive smart suggestions and dynamic scheduling.
6. **Analytics:** Visualize time usage and goal achievement.
7. **Group Study:** Collaborate and track shared goals.

**Backend Workflow Diagram:**

[User]->[Frontend (Flutter)]->[API Gateway (Django REST)]->[Core Modules: Time Tracking | Goal Tracking | Journal | Analytics]->[PostgreSQL Database]

---

### **Explanation**

- **Mobile App (Flutter):**  
  Students interact with a user-friendly mobile interface to log time, set goals, journal, and view analytics.

- **API Layer (Django REST API):**  
  The app communicates with the backend via RESTful API endpoints. This layer handles authentication, request validation, and routes requests to the appropriate modules.

- **Core Modules:**
    - **User Management:** Handles authentication, registration, and user profiles.
    - **Time Tracking:** Manages time entries, categories, and integrates with goals.
    - **Goal Tracking:** Supports hierarchical and group goals, progress, streaks, and LUBE points.
    - **Journal:** Stores and retrieves daily reflections and logs.
    - **Analytics & AI Recommendations:** Processes data to generate productivity insights, dynamic scheduling, and personalized recommendations.
    - **Group Goals:** Manages collaborative goal setting and progress tracking.

- **Database (PostgreSQL):**  
  All modules interact with a centralized PostgreSQL database, which stores structured data such as users, time entries, categories, goals, journals, analytics, and group goal information.

---

**This modular backend ensures seamless integration of time tracking, goal management, journaling, and analytics, enabling frictionless productivity and personalized recommendations for students.**  

## Important External Links

- [Project Documentation]
- [Team & Problem Statement (Hack_Some_Thorns_Mangoes.pdf)]
- [Official PostgreSQL Download](https://www.postgresql.org/download/windows/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Flutter Documentation](https://docs.flutter.dev/)

---

> **ReFL3KT: Align your time, goals, and growth—frictionlessly.**

