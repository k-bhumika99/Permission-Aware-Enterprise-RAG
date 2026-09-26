from flask import Blueprint, render_template, request, flash, redirect, url_for, g
from config import Config
from services.auth_service import login_required, role_required

settings_bp = Blueprint('settings_bp', __name__)

@settings_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_view():
    user = g.user
    if request.method == 'POST':
        if user.role != 'ADMIN':
            flash('Only administrators can modify system security settings.', 'danger')
            return redirect(url_for('settings_bp.settings_view'))

        llm_provider = request.form.get('llm_provider', 'auto')
        strict_mode = request.form.get('strict_mode') == 'on'
        
        Config.LLM_PROVIDER = llm_provider
        Config.STRICT_PERMISSION_MODE = strict_mode
        
        flash('Enterprise RAG security settings updated successfully.', 'success')
        return redirect(url_for('settings_bp.settings_view'))

    settings_data = {
        'database_url': Config.DATABASE_URL.split('@')[-1] if '@' in Config.DATABASE_URL else 'SQLite local db',
        'llm_provider': Config.LLM_PROVIDER,
        'embedding_model': Config.EMBEDDING_MODEL,
        'strict_mode': Config.STRICT_PERMISSION_MODE,
        'vector_store_path': Config.VECTOR_STORE_PATH
    }

    return render_template('settings.html', user=user, settings=settings_data)
