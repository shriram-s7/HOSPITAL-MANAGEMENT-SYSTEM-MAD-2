import datetime
import json
from app import create_app
from models import db, User, Department, DoctorProfile, PatientProfile, Appointment, Treatment

app = create_app()

DOCTORS = [
    {"username": "dr_arun_sharma",    "email": "arun.sharma@hms.in",    "spec": "Cardiology",       "dept": "Cardiology"},
    {"username": "dr_priya_nair",     "email": "priya.nair@hms.in",     "spec": "Neurology",        "dept": "Neurology"},
    {"username": "dr_rajesh_gupta",   "email": "rajesh.gupta@hms.in",   "spec": "Orthopedics",      "dept": "Orthopedics"},
    {"username": "dr_deepa_menon",    "email": "deepa.menon@hms.in",    "spec": "Dermatology",      "dept": "Dermatology"},
    {"username": "dr_vikram_iyer",    "email": "vikram.iyer@hms.in",    "spec": "General Medicine", "dept": "General Medicine"},
    {"username": "dr_kavya_reddy",    "email": "kavya.reddy@hms.in",    "spec": "Gynecology",       "dept": "Gynecology"},
    {"username": "dr_suresh_pillai",  "email": "suresh.pillai@hms.in",  "spec": "Pediatrics",       "dept": "Pediatrics"},
    {"username": "dr_ananya_bose",    "email": "ananya.bose@hms.in",    "spec": "Psychiatry",       "dept": "Psychiatry"},
    {"username": "dr_mohan_das",      "email": "mohan.das@hms.in",      "spec": "Ophthalmology",    "dept": "Ophthalmology"},
    {"username": "dr_lakshmi_kumar",  "email": "lakshmi.kumar@hms.in",  "spec": "ENT",              "dept": "ENT"},
]

PATIENTS = [
    {"username": "rahul_mehta",    "email": "rahul.mehta@gmail.com",    "contact": "9876543210", "address": "12 MG Road, Bangalore", "blood": "B+"},
    {"username": "sneha_patel",    "email": "sneha.patel@gmail.com",    "contact": "9845123456", "address": "45 Juhu Beach, Mumbai",  "blood": "O+"},
    {"username": "arjun_verma",    "email": "arjun.verma@gmail.com",    "contact": "9900112233", "address": "7 Connaught Place, Delhi","blood": "A+"},
    {"username": "divya_krishnan", "email": "divya.krishnan@gmail.com", "contact": "9988776655", "address": "23 T. Nagar, Chennai",   "blood": "AB-"},
    {"username": "karan_singh",    "email": "karan.singh@gmail.com",    "contact": "9123456789", "address": "89 Hazratganj, Lucknow", "blood": "O-"},
]

APPOINTMENTS = [
    (0, 0, -30, "09:00", "Completed", "Hypertension Stage 2",         "Amlodipine 5mg OD, Losartan 50mg OD",           "Follow-up in 4 weeks"),
    (1, 1, -25, "10:00", "Completed", "Migraine with aura",           "Sumatriptan 50mg PRN, Propranolol 40mg BD",      "Return if frequency increases"),
    (2, 2, -20, "11:00", "Completed", "ACL tear right knee",          "Physiotherapy 3x/week, Diclofenac 50mg TDS",     "Surgery consult next month"),
    (3, 3, -18, "09:30", "Completed", "Atopic dermatitis",            "Hydrocortisone 1% cream, Cetirizine 10mg OD",    "Avoid allergens. Review in 3 weeks"),
    (4, 4, -15, "14:00", "Completed", "Viral fever & throat infection","Paracetamol 500mg TDS, Azithromycin 500mg OD",   "Rest 5 days, plenty of fluids"),
    (0, 5, -12, "10:30", "Completed", "Irregular menstrual cycle",    "Progesterone 200mg OD, Folic acid 5mg OD",       "Ultrasound pelvis advised"),
    (1, 6, -10, "11:30", "Completed", "Acute bronchitis",             "Amoxicillin 500mg TDS, Salbutamol inhaler PRN",  "Chest X-ray if no improvement in 5 days"),
    (2, 7, -8,  "15:00", "Completed", "Moderate depression",          "Sertraline 50mg OD, Therapy sessions weekly",    "Follow-up in 2 weeks"),
    (3, 8, -5,  "09:00", "Completed", "Dry eye syndrome",             "Hydroxypropyl methylcellulose drops TDS",        "Screen time reduction advised"),
    (4, 9, -3,  "10:00", "Completed", "Chronic sinusitis",            "Mometasone nasal spray OD, Levocetirizine 5mg",  "CT sinuses if persists"),
    (0, 1, -2,  "11:00", "Completed", "Tension headache",             "Ibuprofen 400mg PRN, Paracetamol 500mg TDS",     "Stress management advised"),
    (1, 2, -1,  "14:30", "Completed", "Knee osteoarthritis",          "Glucosamine 1500mg OD, Physiotherapy",           "Review after 6 weeks"),
    (2, 3,  0,  "09:00", "Booked",    None, None, None),
    (3, 4,  0,  "10:00", "Booked",    None, None, None),
    (4, 5,  1,  "09:30", "Booked",    None, None, None),
    (0, 6,  2,  "11:00", "Booked",    None, None, None),
    (1, 7,  3,  "14:00", "Booked",    None, None, None),
    (2, 8,  4,  "09:00", "Booked",    None, None, None),
    (3, 0,  -7, "10:00", "Cancelled", None, None, None),
    (4, 1, -14, "15:00", "Cancelled", None, None, None),
]

def build_availability():
    today = datetime.date.today()
    slots = {}
    for i in range(7):
        d = today + datetime.timedelta(days=i)
        slots[d.strftime('%Y-%m-%d')] = ['Morning', 'Evening']
    return json.dumps(slots)

with app.app_context():
    print("Dropping all tables...")
    db.drop_all()
    db.create_all()

    print("Creating Admin...")
    admin = User(username='admin', role='Admin', email='admin@hms.in')
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.flush()

    print("Creating Departments & Doctors...")
    dept_map = {}
    doctor_users = []
    for d in DOCTORS:
        if d['dept'] not in dept_map:
            dept = Department(name=d['dept'])
            db.session.add(dept)
            db.session.flush()
            dept_map[d['dept']] = dept.id

        user = User(username=d['username'], role='Doctor', email=d['email'])
        user.set_password('doctor123')
        db.session.add(user)
        db.session.flush()

        profile = DoctorProfile(
            user_id=user.id,
            department_id=dept_map[d['dept']],
            specialization=d['spec'],
            availability=build_availability()
        )
        db.session.add(profile)
        doctor_users.append(user)

    print("Creating Patients...")
    patient_users = []
    for p in PATIENTS:
        user = User(username=p['username'], role='Patient', email=p['email'])
        user.set_password('patient123')
        db.session.add(user)
        db.session.flush()

        profile = PatientProfile(
            user_id=user.id,
            contact_number=p['contact'],
            address=p['address'],
            blood_group=p['blood']
        )
        db.session.add(profile)
        patient_users.append(user)

    db.session.flush()

    print("Creating Appointments & Treatments...")
    today = datetime.date.today()
    for (pat_idx, doc_idx, day_offset, time_str, status, diagnosis, prescription, notes) in APPOINTMENTS:
        appt_date = today + datetime.timedelta(days=day_offset)
        h, m = map(int, time_str.split(':'))
        appt = Appointment(
            patient_id=patient_users[pat_idx].id,
            doctor_id=doctor_users[doc_idx].id,
            date=appt_date,
            time=datetime.time(h, m),
            status=status
        )
        db.session.add(appt)
        db.session.flush()

        if status == 'Completed' and diagnosis:
            treatment = Treatment(
                appointment_id=appt.id,
                diagnosis=diagnosis,
                prescription=prescription,
                notes=notes
            )
            db.session.add(treatment)

    db.session.commit()
    print("\nSeeding complete!")
    print(f"  Admin:        admin / admin123")
    print(f"  Doctors (10): dr_arun_sharma ... dr_lakshmi_kumar / doctor123")
    print(f"  Patients (5): rahul_mehta ... karan_singh / patient123")
    print(f"  Appointments: 20 total (12 Completed, 6 Booked, 2 Cancelled)")
