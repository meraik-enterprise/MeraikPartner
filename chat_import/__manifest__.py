{
    'name': 'Chat Import',
    'version': '1.0',
    'category': 'Helpdesk',
    'summary': 'Importación de conversaciones de Chat a tickets de Helpdesk',
    'description': """
Módulo de integración entre Chat y Odoo Helpdesk

Este módulo permite:
1. Importación automática de conversaciones desde Chat a tickets de Helpdesk
2. Creación de tickets desde webhooks de Chat
3. Gestión unificada de conversaciones con seguimiento de origen

Características principales:
- Importación automática periódica de conversaciones mediante cron
- Creación de tickets en tiempo real mediante webhooks
- Sistema de detección y actualización de conversaciones existentes
- Formato mejorado de mensajes con nombres en negrita y timestamps
- Control de origen de tickets (webhook o importación automática)
- Configuración flexible de rangos de tiempo para la importación
- Prevención de duplicados mediante ID de conversación

Los tickets creados por webhook:
- Se crean en estado "New"
- Mantienen su origen como "webhook"
- Se actualizan con nuevos mensajes sin cambiar su origen

Los tickets creados por importación automática:
- Se crean en estado "Solved"
- Se identifican con origen "cron"
- Se actualizan con nuevos mensajes manteniendo su origen

El módulo asegura que cada conversación tenga un único ticket, actualizando el existente cuando se recibe nueva información.
""",
    'author': 'Meraik',
    'website': 'https://platform.meraik.com',
    'depends': ['helpdesk'],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_views.xml',
        'data/ir_cron.xml',
        'data/ir_config_parameter.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
