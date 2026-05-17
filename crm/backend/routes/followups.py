"""
Follow-up routes — thin controllers that delegate to followup_service.
"""
from flask import Blueprint, request, jsonify, current_app
from middleware.auth import login_required, admin_required, get_current_user_id
from services.followup_service import (
    get_all_followups, get_followup_by_id,
    create_followup, update_followup, delete_followup
)
from utils.validators import ValidationError

followups_bp = Blueprint('followups', __name__)


@followups_bp.route('/', methods=['GET'])
@login_required
def list_followups():
    user_id = get_current_user_id()
    followups = get_all_followups(user_id)
    return jsonify(followups), 200


@followups_bp.route('/<int:fu_id>', methods=['GET'])
@login_required
def get_fu(fu_id):
    user_id = get_current_user_id()
    fu = get_followup_by_id(user_id, fu_id)
    if not fu:
        return jsonify({'error': 'Follow-up not found'}), 404
    return jsonify(fu), 200


@followups_bp.route('/', methods=['POST'])
@login_required
def add_followup():
    user_id = get_current_user_id()
    data = request.get_json()

    try:
        fu_id = create_followup(user_id, data)
        current_app.logger.info(f"Follow-up {fu_id} created by user {user_id}")
        return jsonify({'id': fu_id, 'message': 'Follow-up created successfully'}), 201
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400


@followups_bp.route('/<int:fu_id>', methods=['PUT'])
@login_required
def edit_followup(fu_id):
    user_id = get_current_user_id()
    data = request.get_json()

    try:
        success = update_followup(user_id, fu_id, data)
        if not success:
            return jsonify({'error': 'Follow-up not found'}), 404
        return jsonify({'message': 'Follow-up updated successfully'}), 200
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400


@followups_bp.route('/<int:fu_id>', methods=['DELETE'])
@admin_required
def remove_followup(fu_id):
    user_id = get_current_user_id()
    success = delete_followup(user_id, fu_id)
    if not success:
        return jsonify({'error': 'Follow-up not found'}), 404
    current_app.logger.info(f"Follow-up {fu_id} deleted by user {user_id}")
    return jsonify({'message': 'Follow-up deleted successfully'}), 200
