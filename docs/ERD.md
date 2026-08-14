# ERD textual

Institution 1──N TechnicalCareer
Institution 1──N AcademicPeriod
Institution 1──N User
Institution 1──N StudentProfile
Institution 1──N Opportunity

Company 1──N Supervisor
Company 1──N User
Company 1──N Opportunity
Company 1──N Internship

TechnicalCareer 1──N StudentProfile
TechnicalCareer 1──N Opportunity

StudentProfile 1──N Application
Opportunity 1──N Application

Application 1──1 Internship
Internship 1──N Activity
Internship 1──1 Evaluation
Internship 1──N Evidence
Internship 1──1 InternshipCertificate

User 1──N AuditLog
User 1──N Notification
