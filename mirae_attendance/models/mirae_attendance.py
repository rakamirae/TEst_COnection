from odoo import api, fields, models, exceptions, _
from datetime import datetime, date, timedelta
from odoo.tools import format_datetime

class MiraeAttendance(models.Model):
    _inherit = 'hr.attendance'
    _order = 'isdate desc'

    check_in = fields.Datetime(required=False)
    isdate = fields.Date(required=True)
    status = fields.Char(string="Status", compute='_compute_status', store=True, readonly=True)

    _sql_constraints = [ ('att_unique', 'unique(employee_id, isdate)', 'Attendance must be unique!'), ] 

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        pass

    def SyncAttendance(self):
        dtFirst = date.today()+timedelta(days=-3)
        # dtFirst = date(2023,7,1) # ini buat test get all data 
        dtTo = date.today()

        while (dtFirst <= dtTo):
            isdt_from = datetime.strptime(dtFirst.strftime("%Y-%m-%d 00:00:00"), '%Y-%m-%d %H:%M:%S')+timedelta(hours=-7)
            isdt_to = datetime.strptime(dtFirst.strftime("%Y-%m-%d 23:59:59"), '%Y-%m-%d %H:%M:%S')+timedelta(hours=-7)
            rows = self.env['device.log'].read_group([('timestamp', '>=', isdt_from), 
                                                      ('timestamp', '<=', isdt_to)], 
                                                      fields=['employee_id'], groupby=['employee_id'])
            if rows:
                for row in rows:
                    emp = self.env['hr.employee'].search([('id', '=', row['employee_id'][0])])
                    for res in self.env['resource.calendar'].search([('id', '=', emp.resource_calendar_id.id)]):
                        time_in = self.env['resource.calendar.attendance'].search([('calendar_id', '=', res.id), 
                                                                                   ('dayofweek', '=', dtFirst.weekday()),
                                                                                   ('day_period', '=', 'morning')], limit=1)
                        time_out = self.env['resource.calendar.attendance'].search([('calendar_id', '=', res.id), 
                                                                                   ('dayofweek', '=', dtFirst.weekday()),
                                                                                   ('day_period', '=', 'afternoon')], limit=1)
                
                        to_in = datetime.strptime(dtFirst.strftime("%Y-%m-%d ")+str(
                            time_in.hour_to).replace('.', ':'), "%Y-%m-%d %H:%M")+timedelta(hours=-7)
                        frm_out = datetime.strptime(dtFirst.strftime("%Y-%m-%d ")+str(
                            time_out.hour_from).replace('.', ':'), "%Y-%m-%d %H:%M")+timedelta(hours=-7)

                        att_in = self.env['device.log'].search([('employee_id', '=', emp.id), 
                                                                ('timestamp', '>=', isdt_from), 
                                                                ('timestamp', '<=', to_in)], 
                                                                limit=1, order='timestamp asc')
                        att_out = self.env['device.log'].search([('employee_id', '=', emp.id),
                                                                 ('timestamp', '>=', frm_out),
                                                                 ('timestamp', '<=', isdt_to)],                                                                  
                                                                 limit=1, order='timestamp desc')
                        
                        if att_in.timestamp and att_out.timestamp:
                            if not self.env['hr.attendance'].search([('employee_id', '=', emp.id), 
                                                                     ('isdate', '=', dtFirst)]):
                                self.env['hr.attendance'].create({
                                    'employee_id': emp.id,
                                    'isdate':dtFirst,
                                    'check_in': att_in.timestamp,
                                    'check_out': att_out.timestamp
                                })
                            else:
                                self.env['hr.attendance'].search([
                                    ('employee_id', '=', emp.id), 
                                    ('isdate', '=', dtFirst)]).write({
                                        'check_in': att_in.timestamp,
                                        'check_out': att_out.timestamp })
                        elif att_in.timestamp and not att_out.timestamp:
                            if not self.env['hr.attendance'].search([('employee_id', '=', emp.id), 
                                                                     ('isdate', '=', dtFirst)]):
                                self.env['hr.attendance'].create({
                                    'employee_id': emp.id,
                                    'isdate':dtFirst, 
                                    'check_in': att_in.timestamp, 
                                    'check_out': None
                                })
                            else:
                                self.env['hr.attendance'].search([
                                    ('employee_id', '=', emp.id), 
                                    ('isdate', '=', dtFirst)]).write({
                                        'check_in': att_in.timestamp,
                                        'check_out': None })
                        elif not att_in.timestamp and att_out.timestamp:
                            if not self.env['hr.attendance'].search([('employee_id', '=', emp.id), 
                                                                     ('isdate', '=', dtFirst)]):
                                self.env['hr.attendance'].create({
                                    'employee_id': emp.id, 
                                    'isdate':dtFirst,
                                    'check_in': None,
                                    'check_out': att_out.timestamp
                                })
                            else:
                                self.env['hr.attendance'].search([
                                    ('employee_id', '=', emp.id), 
                                    ('isdate', '=', dtFirst)]).write({
                                        'check_in': None,
                                        'check_out': att_out.timestamp })
                                                                   
            dtFirst = dtFirst+timedelta(days=1)
    
    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for attendance in self:
            if attendance.check_out and attendance.check_in:
                emp = self.env['hr.employee'].search([('id', '=', attendance.employee_id.id)])
                for res in self.env['resource.calendar'].search([('id', '=', emp.resource_calendar_id.id)]):
                    is_in = self.env['resource.calendar.attendance'].search([('calendar_id', '=', res.id), 
                                                                               ('dayofweek', '=', attendance.isdate.weekday()),
                                                                               ('day_period', '=', 'morning')], limit=1)
                    time_in = datetime.strptime(attendance.isdate.strftime("%Y-%m-%d ")+str(
                            is_in.hour_from).replace('.', ':'), "%Y-%m-%d %H:%M")+timedelta(hours=-7)
                    if attendance.check_in > time_in:
                        delta = attendance.check_out - attendance.check_in
                    else:
                        delta = attendance.check_out - time_in
                    attendance.worked_hours = delta.total_seconds() / 3600.0
            else:
                attendance.worked_hours = False
    
    @api.depends('check_in', 'check_out')
    def _compute_status(self):
        istoday = date.today()
        for attendance in self:
            if attendance.isdate != istoday:
                if not attendance.check_out and attendance.check_in:
                    attendance.status = "Forget Out"
                elif attendance.check_out and not attendance.check_in:
                    attendance.status = "Forget In"
                else:
                    attendance.status =""
            else:
                attendance.status =""
    
