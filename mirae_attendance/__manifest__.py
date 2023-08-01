# -*- coding: utf-8 -*-
{
    'name': 'Attendance Mirae',
    'version': '1.0.0',
    'summary': 'Attendance For Mirae',
    'sequence': -10,
    'description': """Attendance For Mirae Asia Pasifik""",
    'category': 'hr',
    'author': 'Mirae',
    'maintainer': 'Mirae',
    'website': '',
    'license': 'AGPL-3',
    'depends':[ 'base', 'hr', 'hr_attendance' ],
    'data': [
        'security/ir.model.access.csv', 
        'views/device_view.xml',
        'views/mirae_attendance_view.xml'
    ],    
    'installable': True,
    'application': False,
    'auto_install': False,
}