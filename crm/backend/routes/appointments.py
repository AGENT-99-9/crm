"""
Appointment routes — thin controllers that delegate to appointment_service.
"""
from flask import Blueprint, request, jsonify, current_app
from middleware.auth import login_required, admin_required, get_current_user_id
from services.appointment_service import (
    get_all_appointments, get_appointment_by_id,
    create_appointment, update_appointment, delete_appointment
)
from utils.validators import ValidationError

appointments_bp = Blueprint('appointments', __name__)


@appointments_bp.route('/', methods=['GET'])
@login_required
def list_appointments():
    user_id = get_current_user_id()
    appointments = get_all_appointments(user_id)
    return jsonify(appointments), 200


@appointments_bp.route('/<int:appt_id>', methods=['GET'])
@login_required
def get_appt(appt_id):
    user_id = get_current_user_id()
    appt = get_appointment_by_id(user_id, appt_id)
    if not appt:
        return jsonify({'error': 'Appointment not found'}), 404
    return jsonify(appt), 200


@appointments_bp.route('/', methods=['POST'])
@login_required
def add_appointment():
    user_id = get_current_user_id()
    data = request.get_json()

    try:
        appt_id = create_appointment(user_id, data)
        current_app.logger.info(f"Appointment {appt_id} created by user {user_id}")
        return jsonify({'id': appt_id, 'message': 'Appointment created successfully'}), 201
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400


@appointments_bp.route('/<int:appt_id>', methods=['PUT'])
@login_required
def edit_appointment(appt_id):
    user_id = get_current_user_id()
    data = request.get_json()

    try:
        success = update_appointment(user_id, appt_id, data)
        if not success:
            return jsonify({'error': 'Appointment not found'}), 404
        return jsonify({'message': 'Appointment updated successfully'}), 200
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400


@appointments_bp.route('/<int:appt_id>', methods=['DELETE'])
@admin_required
def remove_appointment(appt_id):
    user_id = get_current_user_id()
    success = delete_appointment(user_id, appt_id)
    if not success:
        return jsonify({'error': 'Appointment not found'}), 404
    current_app.logger.info(f"Appointment {appt_id} deleted by user {user_id}")
    return jsonify({'message': 'Appointment deleted successfully'}), 200
