"""
Dashboard routes — dedicated endpoint for dashboard aggregation.
Replaces the old pattern of loading all clients on the frontend.
"""
from flask import Blueprint, jsonify
from middleware.auth import login_required, get_current_user_id
from services.dashboard_service import get_dashboard_data

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/', methods=['GET'])
@login_required
def get_dashboard():
    user_id = get_current_user_id()
    data = get_dashboard_data(user_id)
    return jsonify(data), 200
