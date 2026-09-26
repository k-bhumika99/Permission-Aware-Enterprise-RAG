from flask import Blueprint, render_template, request, flash, redirect, url_for, g
from models import db
from models.audit import QueryRecord, AuditLog
from services.auth_service import login_required

profile_bp = Blueprint('profile_bp', __name__)

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_view():
    user = g.user
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if name:
            user.name = name
            db.session.commit()
            flash('Profile details updated successfully.', 'success')
            return redirect(url_for('profile_bp.profile_view'))

    user_queries_count = QueryRecord.query.filter_by(user_id=user.id).count()
    recent_activity = db.session.query(AuditLog).filter_by(user_id=user.id).order_by(AuditLog.timestamp.desc()).limit(8).all()

    return render_template(
        'profile.html',
        user=user,
        query_count=user_queries_count,
        recent_activity=recent_activity
    )
