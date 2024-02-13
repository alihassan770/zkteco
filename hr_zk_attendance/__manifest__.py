# -*- coding: utf-8 -*-
{
    'name': 'Biometric Device Integration',
    'version': '17.0.1.0.0',
    'category': 'Human Resources',
    'summary': "Integrating Biometric Device (Model: ZKteco uFace 202) With HR"
               "Attendance (Face + Thumb)",
    'description': "This module integrates Odoo with the biometric"
                   "device(Model: ZKteco uFace 202),odoo17,odoo,hr,attendance",
    'author': '',
    'company': '',
    'maintainer': '',
    'website': "https://www.demo.com",
    'depends': ['base_setup', 'hr_attendance'],
    'data': [
        'security/ir.model.access.csv',
        'views/biometric_device_details_views.xml',
        'views/hr_employee_views.xml',
        'views/daily_attendance_views.xml',
        'views/biometric_device_attendance_menus.xml',
    ],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 2
}

