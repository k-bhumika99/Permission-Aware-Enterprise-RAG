from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, g
from models import db
from models.user import User
from models.document import Document
from models.audit import AuditLog, QueryRecord
from services.auth_service import login_required
from services.permission_service import PermissionService

dashboard_bp = Blueprint('dashboard_bp', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    user = g.user
    
    try:
        all_docs = Document.query.all()
        authorized_docs = PermissionService.filter_authorized_documents(user, all_docs)
        restricted_docs_count = len(all_docs) - len(authorized_docs)

        # Naive UTC datetime for SQLite compatibility
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        queries_today = QueryRecord.query.filter(QueryRecord.timestamp >= today_start).count()
        
        total_users = User.query.count()
        permission_denials = db.session.query(AuditLog).filter(AuditLog.authorization_status == 'DENIED').count()
        security_events = db.session.query(AuditLog).filter(AuditLog.action.in_(['UNAUTHORIZED_QUERY', 'PERMISSION_DENIED', 'LOGIN'])).count()
        successful_queries = QueryRecord.query.filter(QueryRecord.authorization_status == 'ALLOWED').count()

        recent_queries = QueryRecord.query.order_by(QueryRecord.timestamp.desc()).limit(5).all()
        recent_audit_events = db.session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(6).all()

        # Classification Distribution breakdown
        class_counts = {
            'PUBLIC': sum(1 for d in all_docs if d.classification == 'PUBLIC'),
            'INTERNAL': sum(1 for d in all_docs if d.classification == 'INTERNAL'),
            'CONFIDENTIAL': sum(1 for d in all_docs if d.classification == 'CONFIDENTIAL'),
            'RESTRICTED': sum(1 for d in all_docs if d.classification == 'RESTRICTED')
        }

        # Security Score calculation
        total_q = successful_queries + permission_denials
        sec_score = int((successful_queries / total_q) * 100) if total_q > 0 else 100

        return render_template(
            'dashboard.html',
            user=user,
            total_documents=len(all_docs),
            authorized_documents_count=len(authorized_docs),
            restricted_documents_count=restricted_docs_count,
            queries_today=queries_today,
            total_users=total_users,
            permission_denials=permission_denials,
            security_events=security_events,
            successful_queries=successful_queries,
            recent_queries=recent_queries,
            recent_audit_events=recent_audit_events,
            authorized_docs=authorized_docs[:5],
            class_counts=class_counts,
            sec_score=sec_score
        )
    except Exception as e:
        print(f"[Dashboard Error] {e}")
        # Safe fallback rendering
        return render_template(
            'dashboard.html',
            user=user,
            total_documents=0,
            authorized_documents_count=0,
            restricted_documents_count=0,
            queries_today=0,
            total_users=1,
            permission_denials=0,
            security_events=0,
            successful_queries=0,
            recent_queries=[],
            recent_audit_events=[],
            authorized_docs=[],
            class_counts={'PUBLIC': 1, 'INTERNAL': 2, 'CONFIDENTIAL': 1, 'RESTRICTED': 1},
            sec_score=100
        )

@dashboard_bp.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    user = g.user
    all_docs = Document.query.all()
    authorized_docs = PermissionService.filter_authorized_documents(user, all_docs)
    
    return jsonify({
        'user': user.to_dict(),
        'total_documents': len(all_docs),
        'authorized_documents': len(authorized_docs),
        'restricted_documents': len(all_docs) - len(authorized_docs),
        'total_users': User.query.count(),
        'permission_denials': db.session.query(AuditLog).filter(AuditLog.authorization_status == 'DENIED').count(),
        'security_events': db.session.query(AuditLog).count()
    })
