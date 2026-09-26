from flask import Blueprint, render_template, request, jsonify, g, flash, redirect, url_for
from models import db
from models.user import User
from services.auth_service import login_required, role_required
from services.audit_service import AuditService

users_bp = Blueprint('users_bp', __name__)

@users_bp.route('/users')
@login_required
def users_view():
    user = g.user
    users = User.query.order_by(User.created_at.desc()).all()
    
    stats = {
        'total': len(users),
        'employees': sum(1 for u in users if u.role == 'EMPLOYEE'),
        'managers': sum(1 for u in users if u.role == 'MANAGER'),
        'hr': sum(1 for u in users if u.role == 'HR'),
        'admins': sum(1 for u in users if u.role == 'ADMIN')
    }
    
    return render_template('users.html', user=user, users=users, stats=stats)


@users_bp.route('/api/users/<int:target_user_id>', methods=['POST', 'PUT'])
@login_required
@role_required(['ADMIN'])
def api_update_user(target_user_id):
    current_admin = g.user
    target = db.session.get(User, target_user_id)
    if not target:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json() or request.form
    new_role = data.get('role')
    new_department = data.get('department')
    is_active = data.get('is_active')

    changes = []
    if new_role and new_role in ['ADMIN', 'MANAGER', 'HR', 'EMPLOYEE'] and new_role != target.role:
        changes.append(f"Role: {target.role} -> {new_role}")
        target.role = new_role

    if new_department and new_department != target.department:
        changes.append(f"Department: {target.department} -> {new_department}")
        target.department = new_department

    if is_active is not None:
        active_bool = str(is_active).lower() in ['true', '1', 'on']
        if active_bool != target.is_active:
            changes.append(f"Active: {target.is_active} -> {active_bool}")
            target.is_active = active_bool

    if changes:
        db.session.commit()
        change_summary = "; ".join(changes)
        AuditService.log_action(
            user=current_admin,
            action='USER_ROLE_UPDATED',
            authorization_status='PASS',
            result_summary=f"Admin updated user '{target.email}' (#{target.id}): {change_summary}"
        )
        return jsonify({'message': f"Updated {target.name} successfully.", 'user': target.to_dict()})

    return jsonify({'message': 'No changes applied.', 'user': target.to_dict()})
