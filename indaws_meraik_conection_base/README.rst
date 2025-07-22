================================
MerAik Base Module (indaws_meraik_conection_base)
================================

The indaws_meraik_conection_base module is the core of the MerAik platform. It provides the essential infrastructure for process automation through the management of contracts, requests, and responses. This module lays the foundation for interacting with AI services, allowing other specific modules to extend its functionality.
**Table of contents**

.. contents::
   :local:

Structure and Main Components
=============

MeraikContract Model
---------------------

This model defines the basic structure of a contract within MerAik and is responsible for the primary interaction with AI services.

Main Fields:
- name: The name of the contract, which identifies it within the system.
- state: The status of the contract (draft, test, active, cancel, blocked).
- request_qty: The number of requests associated with the contract, calculated automatically.

Key Methods:
-create_request: Sends a request to be processed by the AI.
- get_conection_info: Retrieves the connection information necessary to interact with the remote service.

MeraikRequestResponse Model
---------------------------

This model manages the responses to requests sent through a contract, storing and processing the results returned by the AI.

Main Fields:
- response_json: Stores the response in JSON format.
- state: The status of the request, which can be pending, success, error, among others.

Key Methods:
- check_result: Verifies the status and content of a received response and updates the corresponding records based on the AI's feedback.
- process_document: Applies business logic to the document or record based on the processed response, ensuring that the data is correctly integrated into the company's workflows.

Key Features
=====
The indaws_meraik_conection_base module provides the following central functionalities that can be utilized and extended by other modules:

1. Contract Management: Allows the creation and management of contracts that define how and when requests should be sent to the AI, and how the responses should be handled.
2. Request Submission: Facilitates communication with the AI by sending data for automated processing. The data can include documents, structured information, or specific configurations.
3. Response Processing: Manages the updating of records in the system once responses are received from the AI, applying the necessary business logic.

Interaction with Other Modules
=====================
The indaws_meraik_conection_base module is designed to be extended by specific use-case modules that add additional functionality based on business needs. These modules inherit and customize the capabilities of the base module to handle specific scenarios such as purchase order management, sales, and expenses.

Each of these modules may implement additional models and specific logic, but they all rely on indaws_meraik_conection_base to manage the interaction with the AI and handle process automation.

Webhook Integration
=====================
In Odoo 16, the native base.automation webhook triggers from v17 are not available. To receive and process incoming HTTP requests (webhooks), follow these guidelines:

1. Install an HTTP controller module
- For example, use Web Controller from OCA (web_controller) or any similar addon that exposes HTTP routes.

2. Define your webhook endpoint
- Implement a controller method in your module, e.g., controllers/webhook.py, listening on /meraik/webhook with type='json', methods=['POST'] and csrf=False.

3. Expected payload

{
  "ai_contract_id": 123,        // Remote contract ID
  "id": 456,                    // Remote request ID
  "state": "done",            // Request state
  "response": { ... }           // Response data
}

4. Processing logic

- Search the contract:

contract = request.env['meraik.contract'].sudo().search([
    ('remote_id', '=', int(payload['ai_contract_id']))
], limit=1)

-Build values for the response model:

vals = {
    'contract_id': contract.id,
    'request_remote_id': int(payload['id']),
    'state': payload['state'],
    'response_json': json.dumps(payload['response']),
}

-Create or update:

Response = request.env['meraik.request.response'].sudo()
existing = Response.search([('request_remote_id', '=', vals['request_remote_id'])], limit=1)
if existing:
    existing.with_context(process_document=True).write(vals)
else:
    Response.with_context(process_document=True).create(vals)

5. Security considerations

- Use auth='none' if you secure the URL via a secret token, or auth='user' with API keys in headers.
- Disable CSRF (csrf=False) for the endpoint or implement custom validation headers.




Known issues / Roadmap
======================


Bug Tracker
===========

Credits
=======

Authors
-------

Contributors
------------

Maintainers
-----------
