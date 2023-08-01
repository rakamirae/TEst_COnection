from odoo import api, fields, models, _
from zk import ZK, const
from datetime import datetime, date, timedelta
import pymssql


class DeviceList(models.Model):
    _name = 'device.list'
    _description = 'List of Device'
    _order = 'id desc'

    name = fields.Char(string="Name", required=True)
    ip = fields.Char(string="Device IP", required=True)
    is_device = fields.Boolean(string="Is Device", default=True)
    active = fields.Boolean(string="Active", default=True)
    
    _sql_constraints = [ ('ip_unique', 'unique(ip)', 'IP Address must be unique!'), ] 
    
    def get_device_log(self):
        active = self.env['device.list'].browse(self._context.get('active_ids'))
        if not active:            
            active = self

        for res in active:
            conn = None
            ip = res.ip
            istoday = date.today()
            strDateTime = istoday.strftime("%Y-%m-%d 00:00:00")
            isDateTime = datetime.strptime(strDateTime, "%Y-%m-%d %H:%M:%S")            

            if res.is_device:
                zk = ZK(ip, port=4370, timeout=5, password=0, force_udp=False, ommit_ping=False)
                try:
                    conn = zk.connect()
                    conn.disable_device()
                    attendances = zk.get_attendance()
                    for i in attendances:
                      if i.timestamp >= isDateTime+timedelta(hours=-7): 
                        emp_id = self.env['hr.employee'].search([('employee_number', '=', i.user_id)])
                        if emp_id:
                            data = self.env['device.log'].search(['&', 
                                                                  ('device_id', '=', res.id), 
                                                                  ('employee_id', '=', emp_id.id), 
                                                                  ('timestamp', '=', i.timestamp+timedelta(hours=-7))])
                            if not data:
                                self.env['device.log'].create({
                                    'device_id': res.id, 
                                    'employee_id': emp_id.id,
                                    'timestamp': i.timestamp+timedelta(hours=-7)
                                })   
                finally:
                    conn.enable_device()
                    conn.disconnect()
            else:
                conn = pymssql.connect(ip, 'sa', 'Br4pr0M15', 'IFaceDB')
                cur = conn.cursor()
                cur.execute(
                    '''            
                    Select PIN, MIN(event_time) event_time, CONVERT(VARCHAR(12), event_time, 113) DT  
                    From [dbo].[acc_transaction]
                    Where PIN <> '' and event_time >= %s Group By PIN, CONVERT(VARCHAR(12), event_time, 113)
                    UNION
                    Select PIN, MAX(event_time) event_time, CONVERT(VARCHAR(12), event_time, 113) DT   
                    From [dbo].[acc_transaction] 
                    Where PIN <> '' and event_time >= %s Group By PIN, CONVERT(VARCHAR(12), event_time, 113)
                    ''', (istoday+timedelta(days=-1), istoday+timedelta(days=-1)))
                for row in cur:
                    if row[1] >= isDateTime+timedelta(days=-1):
                        emp_id = self.env['hr.employee'].search([('employee_number', '=', row[0])])
                        if emp_id:
                            data = self.env['device.log'].search(['&', 
                                                                  ('device_id', '=', res.id), 
                                                                  ('employee_id', '=', emp_id.id), 
                                                                  ('timestamp', '=', row[1]+timedelta(hours=-7))]) 
                            if not data:
                                self.env['device.log'].create({
                                    'device_id': res.id, 
                                    'employee_id': emp_id.id,
                                    'timestamp': row[1]+timedelta(hours=-7)
                                })                

        self.env['hr.attendance'].SyncAttendance()
    

    def SyncAtt(self):
        self.env['hr.attendance'].SyncAttendance()
    
class DeviceLog(models.Model):
    _name = 'device.log'
    _description = 'Device Log'
    _order = 'timestamp desc'

    device_id = fields.Many2one("device.list", string="Device", index=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, ondelete='cascade', index=True)
    employee_number = fields.Char(related="employee_id.employee_number")
    timestamp = fields.Datetime(string="Date Time Log") 

    _sql_constraints = [ ('log_unique', 'unique(device_id, employee_id, timestamp)', 'Log for employee must be unique!'), ] 