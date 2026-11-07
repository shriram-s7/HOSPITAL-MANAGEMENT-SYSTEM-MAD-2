from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from models import db, cache, User, DoctorProfile, PatientProfile, Appointment, Treatment, Department
from sqlalchemy import or_
import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'msg': 'Missing JSON payload'}), 400
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        token = create_access_token(
            identity=str(user.id), 
            additional_claims={'id': user.id, 'role': user.role, 'username': user.username}
        )
        return jsonify({'token': token, 'role': user.role, 'id': user.id, 'username': user.username}), 200
    return jsonify({'msg': 'Invalid credentials'}), 401

@api_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'msg': 'Missing JSON payload'}), 400
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'msg': 'Username and password required'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'msg': 'Username already exists'}), 400
    email = data.get('email', '').strip()
    user = User(username=username, role='Patient', email=email if email else None)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    profile = PatientProfile(user_id=user.id)
    db.session.add(profile)
    db.session.commit()
    return jsonify({'msg': 'Registered successfully'}), 201

@api_bp.route('/admin/dashboard', methods=['GET'])
@jwt_required()
def admin_dashboard():
    current_user = get_jwt()
    if current_user.get('role') != 'Admin':
        return jsonify({'msg': 'Unauthorized'}), 403
    doctors_count = User.query.filter_by(role='Doctor').count()
    patients_count = User.query.filter_by(role='Patient').count()
    appointments_count = Appointment.query.count()
    return jsonify({
        'doctors': doctors_count,
        'patients': patients_count,
        'appointments': appointments_count
    }), 200

@api_bp.route('/departments', methods=['GET', 'POST'])
@jwt_required()
@cache.cached(timeout=300, query_string=True)
def manage_departments():
    if request.method == 'GET':
        deps = Department.query.all()
        return jsonify([{'id': d.id, 'name': d.name, 'description': d.description} for d in deps])
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'msg': 'Missing JSON payload'}), 400
        
    dep = Department(name=data.get('name'), description=data.get('description'))
    db.session.add(dep)
    db.session.commit()
    return jsonify({'msg': 'Created'}), 201

@api_bp.route('/admin/doctors', methods=['GET', 'POST'])
@jwt_required()
def manage_doctors():
    current_user = get_jwt()
    if current_user.get('role') != 'Admin':
        return jsonify({'msg': 'Unauthorized'}), 403
    
    if request.method == 'GET':
        search = request.args.get('search', '')
        query = User.query.filter_by(role='Doctor').outerjoin(DoctorProfile)
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f'%{search}%'),
                    DoctorProfile.specialization.ilike(f'%{search}%')
                )
            )
        doctors = query.all()
        res = []
        for d in doctors:
            profile = d.doctor_profile
            res.append({
                'id': d.id, 'username': d.username, 'email': d.email,
                'specialization': profile.specialization if profile else '',
                'availability': profile.availability if profile else ''
            })
        return jsonify(res)
    
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'msg': 'Missing JSON payload in request'}), 400
        
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    specialization = data.get('specialization')

    if not username or not password or not email or not specialization:
        return jsonify({'msg': 'Username, password, email, and specialization are required fields.'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'msg': 'User already exists'}), 400
        
    try:
        user = User(username=username, role='Doctor', email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        
        profile = DoctorProfile(user_id=user.id, specialization=specialization)
        db.session.add(profile)
        db.session.commit()
        return jsonify({'msg': 'Doctor created', 'id': user.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'msg': f'Failed to create doctor: {str(e)}'}), 500

@api_bp.route('/admin/doctors/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def update_doctor(id):
    current_user = get_jwt()
    if current_user.get('role') != 'Admin':
        return jsonify({'msg': 'Unauthorized'}), 403
    user = User.query.get_or_404(id)
    if request.method == 'DELETE':
        apps = Appointment.query.filter_by(doctor_id=id).all()
        for app in apps:
            Treatment.query.filter_by(appointment_id=app.id).delete()
        Appointment.query.filter_by(doctor_id=id).delete()
        DoctorProfile.query.filter_by(user_id=id).delete()
        db.session.delete(user)
        db.session.commit()
        return jsonify({'msg': 'Deleted'})
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'msg': 'Missing JSON payload'}), 400
    if data.get('username'): user.username = data.get('username')
    if data.get('email'): user.email = data.get('email')
    profile = user.doctor_profile
    if profile:
        profile.specialization = data.get('specialization', profile.specialization)
    db.session.commit()
    return jsonify({'msg': 'Updated'})

@api_bp.route('/admin/patients/<int:id>', methods=['PUT', 'DELETE'])
@jwt_required()
def manage_patient(id):
    current_user = get_jwt()
    if current_user.get('role') != 'Admin':
        return jsonify({'msg': 'Unauthorized'}), 403
    user = User.query.get_or_404(id)
    if request.method == 'DELETE':
        apps = Appointment.query.filter_by(patient_id=id).all()
        for app in apps:
            Treatment.query.filter_by(appointment_id=app.id).delete()
        Appointment.query.filter_by(patient_id=id).delete()
        PatientProfile.query.filter_by(user_id=id).delete()
        db.session.delete(user)
        db.session.commit()
        return jsonify({'msg': 'Deleted'})
    data = request.get_json(silent=True) or {}
    if data.get('username'): user.username = data.get('username')
    profile = user.patient_profile
    if profile:
        if 'contact' in data: profile.contact_number = data.get('contact')
    db.session.commit()
    return jsonify({'msg': 'Updated'})

@api_bp.route('/admin/patients', methods=['GET'])
@jwt_required()
def get_patients():
    current_user = get_jwt()
    if current_user.get('role') != 'Admin':
        return jsonify({'msg': 'Unauthorized'}), 403
    search = request.args.get('search', '')
    query = User.query.filter_by(role='Patient')
    if search:
        query = query.join(PatientProfile).filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.id == (int(search) if search.isdigit() else -1),
                PatientProfile.contact_number.ilike(f'%{search}%')
            )
        )
    patients = query.all()
    res = [{'id': p.id, 'username': p.username, 'contact': p.patient_profile.contact_number} for p in patients]
    return jsonify(res)

@api_bp.route('/admin/appointments', methods=['GET'])
@jwt_required()
def all_appointments():
    current_user = get_jwt()
    if current_user.get('role') != 'Admin':
        return jsonify({'msg': 'Unauthorized'}), 403
    apps = Appointment.query.all()
    res = [{'id': a.id, 'patient': a.patient.username, 'doctor': a.doctor.username, 'date': a.date.strftime('%Y-%m-%d'), 'time': a.time.strftime('%H:%M'), 'status': a.status} for a in apps]
    return jsonify(res)

@api_bp.route('/doctor/appointments', methods=['GET'])
@jwt_required()
def doctor_appointments():
    current_user = get_jwt()
    if current_user.get('role') != 'Doctor':
        return jsonify({'msg': 'Unauthorized'}), 403
    apps = Appointment.query.filter_by(doctor_id=current_user.get('id')).all()
    res = [{'id': a.id, 'patient_id': a.patient.id, 'patient': a.patient.username, 'date': a.date.strftime('%Y-%m-%d'), 'time': a.time.strftime('%H:%M'), 'status': a.status} for a in apps]
    return jsonify(res)

@api_bp.route('/doctor/appointments/<int:id>/status', methods=['PUT'])
@jwt_required()
def update_status(id):
    current_user = get_jwt()
    if current_user.get('role') != 'Doctor':
        return jsonify({'msg': 'Unauthorized'}), 403
    data = request.get_json(silent=True) or {}
    app = Appointment.query.get_or_404(id)
    app.status = data.get('status', 'Cancelled')
    db.session.commit()
    return jsonify({'msg': 'Status updated'})

@api_bp.route('/doctor/availability', methods=['GET', 'POST'])
@jwt_required()
def availability():
    current_user = get_jwt()
    if current_user.get('role') != 'Doctor':
        return jsonify({'msg': 'Unauthorized'}), 403
    profile = DoctorProfile.query.filter_by(user_id=current_user.get('id')).first()
    if request.method == 'GET':
        return jsonify({'availability': profile.availability})
    data = request.get_json(silent=True) or {}
    profile.availability = data.get('availability', '')
    db.session.commit()
    return jsonify({'msg': 'Availability updated'})

@api_bp.route('/doctor/patients/<int:patient_id>/history', methods=['GET'])
@jwt_required()
def patient_history(patient_id):
    apps = Appointment.query.filter_by(patient_id=patient_id, status='Completed').all()
    res = []
    for a in apps:
        res.append({
            'date': a.date.strftime('%Y-%m-%d'),
            'doctor': a.doctor.username,
            'diagnosis': a.treatment.diagnosis if a.treatment else '',
            'prescription': a.treatment.prescription if a.treatment else ''
        })
    return jsonify(res)

@api_bp.route('/doctor/appointments/<int:id>/treatment', methods=['POST'])
@jwt_required()
def add_treatment(id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'msg': 'Missing JSON payload'}), 400
    t = Treatment(appointment_id=id, diagnosis=data.get('diagnosis'), prescription=data.get('prescription'), notes=data.get('notes'))
    db.session.add(t)
    app = Appointment.query.get(id)
    app.status = 'Completed'
    db.session.commit()
    return jsonify({'msg': 'Treatment added'})

@api_bp.route('/patient/profile', methods=['GET', 'PUT'])
@jwt_required()
def patient_profile():
    current_user = get_jwt()
    if current_user.get('role') != 'Patient':
        return jsonify({'msg': 'Unauthorized'}), 403
    profile = PatientProfile.query.filter_by(user_id=current_user.get('id')).first()
    if request.method == 'GET':
        return jsonify({'contact_number': profile.contact_number, 'address': profile.address, 'blood_group': profile.blood_group})
    data = request.get_json(silent=True) or {}
    profile.contact_number = data.get('contact_number')
    profile.address = data.get('address')
    profile.blood_group = data.get('blood_group')
    db.session.commit()
    return jsonify({'msg': 'Profile updated'})

@api_bp.route('/patient/doctors', methods=['GET'])
@jwt_required()
@cache.cached(timeout=60, query_string=True)
def patient_doctors():
    doctors = User.query.filter_by(role='Doctor').outerjoin(DoctorProfile).all()
    res = [{'id': p.id, 'username': p.username, 'specialization': p.doctor_profile.specialization if p.doctor_profile else '', 'availability': p.doctor_profile.availability if p.doctor_profile else ''} for p in doctors]
    return jsonify(res)

@api_bp.route('/patient/appointments', methods=['GET', 'POST'])
@jwt_required()
def patient_appointments():
    current_user = get_jwt()
    if request.method == 'GET':
        apps = Appointment.query.filter_by(patient_id=current_user.get('id')).all()
        res = []
        for a in apps:
            t_data = None
            if a.treatment:
                t_data = {'diagnosis': a.treatment.diagnosis, 'prescription': a.treatment.prescription, 'notes': a.treatment.notes}
            res.append({'id': a.id, 'doctor': a.doctor.username, 'date': a.date.strftime('%Y-%m-%d'), 'time': a.time.strftime('%H:%M'), 'status': a.status, 'treatment': t_data})
        return jsonify(res)
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'msg': 'Missing JSON payload'}), 400
    date_obj = datetime.datetime.strptime(data.get('date'), '%Y-%m-%d').date()
    time_obj = datetime.datetime.strptime(data.get('time'), '%H:%M').time()
    
    existing = Appointment.query.filter_by(doctor_id=data.get('doctor_id'), date=date_obj, time=time_obj).first()
    if existing and existing.status != 'Cancelled':
        return jsonify({'msg': 'Doctor is already booked at this time'}), 400
        
    app = Appointment(patient_id=current_user.get('id'), doctor_id=data.get('doctor_id'), date=date_obj, time=time_obj)
    db.session.add(app)
    db.session.commit()
    return jsonify({'msg': 'Appointment booked'})

@api_bp.route('/admin/test/daily-reminders', methods=['POST'])
@jwt_required()
def test_daily():
    current_user = get_jwt()
    if current_user.get('role') != 'Admin':
        return jsonify({'msg': 'Unauthorized'}), 403
    import datetime
    today = datetime.date.today()
    
    appt_today = Appointment.query.filter_by(date=today, status='Booked').first()
    if not appt_today:
        patient = User.query.filter_by(role='Patient').first()
        doctor = User.query.filter_by(role='Doctor').first()
        if patient and doctor:
            dummy = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                date=today,
                time=datetime.time(9, 0),
                status='Booked'
            )
            db.session.add(dummy)
            db.session.commit()
    
    from celery_worker import daily_reminders
    daily_reminders.delay()
    return jsonify({'msg': 'Testing: Daily reminder job fired. Check hospitalmanagementsystem79@gmail.com inbox.'})

@api_bp.route('/admin/test/monthly-report', methods=['POST'])
@jwt_required()
def test_monthly():
    current_user = get_jwt()
    if current_user.get('role') != 'Admin':
        return jsonify({'msg': 'Unauthorized'}), 403
    from celery_worker import monthly_report
    monthly_report.delay()
    return jsonify({'msg': 'Testing alert: Monthly reports invoked and sent.'})

@api_bp.route('/patient/appointments/<int:id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_appointment(id):
    app = Appointment.query.get_or_404(id)
    app.status = 'Cancelled'
    db.session.commit()
    return jsonify({'msg': 'Cancelled'})

@api_bp.route('/patient/export', methods=['POST'])
@jwt_required()
def export_csv():
    current_user = get_jwt()
    from celery_worker import export_csv_job
    export_csv_job.delay(current_user.get('id'))
    return jsonify({'msg': 'Export triggered. You will receive it via email shortly.'})

@api_bp.route('/patient/export/download', methods=['GET'])
@jwt_required()
def export_csv_download():
    import io, csv as csv_module
    from flask import make_response
    current_user = get_jwt()
    user_id = current_user.get('id')
    user = User.query.get(user_id)
    apps = Appointment.query.filter_by(patient_id=user_id, status='Completed').all()
    si = io.StringIO()
    cw = csv_module.writer(si)
    cw.writerow(['User ID', 'Username', 'Consulting Doctor', 'Appointment Date', 'Diagnosis', 'Treatment', 'Next Visit'])
    for a in apps:
        cw.writerow([
            user_id,
            user.username,
            a.doctor.username,
            a.date.strftime('%Y-%m-%d'),
            a.treatment.diagnosis if a.treatment else '',
            a.treatment.prescription if a.treatment else '',
            a.treatment.notes if a.treatment else ''
        ])
    output = make_response(si.getvalue())
    output.headers['Content-Disposition'] = 'attachment; filename=treatment_history.csv'
    output.headers['Content-Type'] = 'text/csv'
    return output
