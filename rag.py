from flask import Blueprint, render_template, request, jsonify, g
from models import db
from models.audit import QueryRecord
from services.auth_service import login_required
from services.rag_service import RAGService

rag_bp = Blueprint('rag_bp', __name__)

@rag_bp.route('/rag')
@login_required
def rag_view():
    user = g.user
    recent_user_queries = QueryRecord.query.filter_by(user_id=user.id).order_by(QueryRecord.timestamp.desc()).limit(10).all()
    return render_template('rag.html', user=user, recent_queries=recent_user_queries)


@rag_bp.route('/api/rag/query', methods=['POST'])
@login_required
def api_rag_query():
    user = g.user
    data = request.get_json() or {}
    query_text = data.get('query', '').strip()

    if not query_text:
        return jsonify({'error': 'Please enter a valid query.'}), 400

    result = RAGService.execute_rag_pipeline(user, query_text)
    return jsonify(result)


@rag_bp.route('/query/<int:query_id>')
@login_required
def query_details_view(query_id):
    user = g.user
    record = db.session.get(QueryRecord, query_id)
    if not record:
        return render_template('query_details.html', user=user, error="Query record not found.")

    # Check access to query details (Admin can see all, user can see their own)
    if user.role != 'ADMIN' and record.user_id != user.id:
        return render_template('query_details.html', user=user, error="You are not authorized to view query logs for other users.")

    return render_template('query_details.html', user=user, query_record=record)
