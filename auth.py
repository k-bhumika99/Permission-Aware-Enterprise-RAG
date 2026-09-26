from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, jsonify, session
from models import db
from models.user import User
from services.auth_service import AuthService
from services.audit_service import AuditService

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/signin', methods=['GET', 'POST'])
def signin_view():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Email and password are required.', 'danger')
            return render_template('signin.html', email=email)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            AuditService.log_action(user=None, action='LOGIN', authorization_status='DENIED', result_summary=f"Failed login attempt for email: {email}")
            flash('Invalid email or password credentials.', 'danger')
            return render_template('signin.html', email=email)

        if not user.is_active:
            flash('Your account has been deactivated. Contact an administrator.', 'danger')
            return render_template('signin.html', email=email)

        token = AuthService.generate_token(user)
        session['user_id'] = user.id

        AuditService.log_action(user=user, action='LOGIN', authorization_status='PASS', result_summary=f"Successful login for {user.name} ({user.role})")

        resp = make_response(redirect(url_for('dashboard_bp.dashboard_view')))
        resp.set_cookie('jwt_token', token, httponly=True, samesite='Lax')
        return resp

    return render_template('signin.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup_view():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        department = request.form.get('department', 'Engineering')
        role = request.form.get('role', 'EMPLOYEE')

        # Validation
        if not name or not email or not password:
            flash('All required fields must be filled.', 'danger')
            return render_template('signup.html', name=name, email=email, department=department, role=role)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('signup.html', name=name, email=email, department=department, role=role)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html', name=name, email=email, department=department, role=role)

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email address already exists.', 'danger')
            return render_template('signup.html', name=name, email=email, department=department, role=role)

        new_user = User(
            name=name,
            email=email,
            department=department,
            role=role,
            is_active=True
        )
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        AuditService.log_action(user=new_user, action='USER_REGISTERED', authorization_status='PASS', result_summary=f"New user created: {email} ({role} - {department})")

        flash('Account created successfully! Please sign in with your credentials.', 'success')
        return redirect(url_for('auth_bp.signin_view'))

    return render_template('signup.html')


@auth_bp.route('/logout')
def logout_view():
    user = AuthService.get_current_user()
    if user:
        AuditService.log_action(user=user, action='LOGOUT', authorization_status='PASS', result_summary=f"User {user.email} logged out.")
    session.clear()
    resp = make_response(redirect(url_for('index_view')))
    resp.set_cookie('jwt_token', '', expires=0)
    return resp


@auth_bp.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip()
    password = data.get('password', '').strip()

    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        AuditService.log_action(user=None, action='LOGIN', authorization_status='DENIED', result_summary=f"API failed login: {email}")
        return jsonify({'error': 'Invalid credentials'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account inactive'}), 403

    token = AuthService.generate_token(user)
    session['user_id'] = user.id
    AuditService.log_action(user=user, action='LOGIN', authorization_status='PASS', result_summary=f"API login success for {email}")

    resp = jsonify({'message': 'Login successful', 'user': user.to_dict(), 'token': token})
    resp.set_cookie('jwt_token', token, httponly=True)
    return resp


@auth_bp.route('/api/auth/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    department = data.get('department', 'Engineering')
    role = data.get('role', 'EMPLOYEE')

    if not name or not email or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already registered'}), 400

    new_user = User(name=name, email=email, department=department, role=role, is_active=True)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    token = AuthService.generate_token(new_user)
    return jsonify({'message': 'User registered successfully', 'user': new_user.to_dict(), 'token': token}), 201
