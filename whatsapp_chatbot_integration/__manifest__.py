{
    'name': 'WhatsApp Chatbot Integration',
    'version': '1.0',
    'category': 'Communication',
    'summary': 'Integración de WhatsApp con servicios de chatbot IA',
    'description': """
        Módulo para integrar WhatsApp con servicios de chatbot de IA.
        Permite configurar chatbots inteligentes que responden automáticamente
        a mensajes de WhatsApp con capacidades de silenciamiento tras intervención humana.
    """,
    'author': 'Tu nombre',
    'depends': ['whatsapp', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_account_views.xml',
        'views/discuss_channel_views.xml',
        'views/whatsapp_message_views.xml',
        'views/conversation_timeout_cron_views.xml',
        'data/conversation_timeout_cron.xml',
    ],
    'installable': True,
}
