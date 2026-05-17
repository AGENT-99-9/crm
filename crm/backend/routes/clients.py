"""
Client routes — thin controllers that delegate to client_service.
"""
from flask import Blueprint, request, jsonify, current_app
from middleware.auth import login_required, admin_required, get_current_user_id
from services.client_service import (
    get_all_clients, get_client_by_id, create_client,
    update_client, delete_client, search_clients
)
from utils.validators import ValidationError

clients_bp = Blueprint('clients', __name__)


@clients_bp.route('/', methods=['GET'])
@login_required
def list_clients():
    user_id = get_current_user_id()
    clients = get_all_clients(user_id)
    return jsonify(clients), 200


@clients_bp.route('/export', methods=['GET'])
@login_required
def export_clients():
    from flask import Response
    from services.client_service import export_clients_csv
    user_id = get_current_user_id()
    csv_data = export_clients_csv(user_id)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=clients.csv"}
    )


@clients_bp.route('/<int:client_id>', methods=['GET'])
@login_required
def get_client(client_id):
    user_id = get_current_user_id()
    client = get_client_by_id(user_id, client_id)
    if not client:
        return jsonify({'error': 'Client not found'}), 404
    return jsonify(client), 200


@clients_bp.route('/', methods=['POST'])
@login_required
def add_client():
    user_id = get_current_user_id()
    data = request.get_json()

    try:
        client_id = create_client(user_id, data)
        current_app.logger.info(f"Client {client_id} created by user {user_id}")
        return jsonify({'id': client_id, 'message': 'Client created successfully'}), 201
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400


@clients_bp.route('/<int:client_id>', methods=['PUT'])
@login_required
def edit_client(client_id):
    user_id = get_current_user_id()
    data = request.get_json()

    try:
        success = update_client(user_id, client_id, data)
        if not success:
            return jsonify({'error': 'Client not found'}), 404
        return jsonify({'message': 'Client updated successfully'}), 200
    except ValidationError as e:
        return jsonify({'error': e.message, 'field': e.field}), 400


@clients_bp.route('/<int:client_id>', methods=['DELETE'])
@admin_required
def remove_client(client_id):
    user_id = get_current_user_id()
    success = delete_client(user_id, client_id)
    if not success:
        return jsonify({'error': 'Client not found'}), 404
    return jsonify({'message': 'Client deleted successfully'}), 200


@clients_bp.route('/search', methods=['GET'])
@login_required
def search():
    user_id = get_current_user_id()
    query = request.args.get('q', '')
    results = search_clients(user_id, query)
    return jsonify(results), 200
