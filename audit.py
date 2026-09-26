from flask import Blueprint, render_template, request, jsonify, g
from models import db
from models.audit import AuditLog
from services.auth_service import login_required

audit_bp = Blueprint('audit_bp', __name__)

@audit_bp.route('/audit')
@login_required
def audit_view():
    user = g.user
    role_filter = request.args.get('role', '').strip()
    action_filter = request.args.get('action', '').strip()
    status_filter = request.args.get('status', '').strip()
    search_q = request.args.get('q', '').strip()

    query = db.session.query(AuditLog)

    if role_filter:
        query = query.filter_by(role=role_filter)
    if action_filter:
        query = query.filter_by(action=action_filter)
    if status_filter:
        query = query.filter_by(authorization_status=status_filter)
    if search_q:
        query = query.filter(
            (AuditLog.user_name.ilike(f'%{search_q}%')) |
            (AuditLog.query.ilike(f'%{search_q}%')) |
            (AuditLog.result_summary.ilike(f'%{search_q}%'))
        )

    logs = query.order_by(AuditLog.timestamp.desc()).limit(150).all()

    # Distinct actions and roles for dropdown filters
    roles = ['ADMIN', 'MANAGER', 'HR', 'EMPLOYEE', 'UNAUTHENTICATED']
    actions = ['LOGIN', 'LOGOUT', 'QUERY', 'DOCUMENT_ACCESS', 'DOCUMENT_UPLOAD', 'DOCUMENT_DELETE', 'UNAUTHORIZED_QUERY', 'PERMISSION_DENIED']
    statuses = ['PASS', 'DENIED', 'ALLOWED']

    return render_template(
        'audit.html',
        user=user,
        logs=logs,
        roles=roles,
        actions=actions,
        statuses=statuses,
        current_role=role_filter,
        current_action=action_filter,
        current_status=status_filter,
        search_q=search_q
    )


@audit_bp.route('/api/audit-logs')
@login_required
def api_audit_logs():
    logs = db.session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return jsonify({'logs': [l.to_dict() for l in logs]})
