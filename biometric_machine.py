from openerp import models, fields, api
from datetime import datetime , timedelta
from zklib import zklib
import time
from zklib import zkconst
from openerp import _
from openerp.exceptions import Warning

class account_move_line_custom_dos(models.Model):
    _inherit = 'hr.employee'
    machine_id = fields.Integer(string='Machine Id')

    _sql_constraints = [
    ('machine_id', 'unique(machine_id)', 'This ID already exists!')
    ]

class bio_machine_users(models.Model):
    _name = 'bio.machine.users'
    user_id = fields.Integer('USER ID')
    user_name = fields.Char('Name ')
    user_role = fields.Char('Role')
    emp_id = fields.Integer('emp_id')


class bio_machine_attendance(models.Model):
    _name = 'bio.machine.attendance'
    user_id = fields.Integer('USER ID')
    time = fields.Datetime('Time')
    status = fields.Char('Status')

class biometric_machine(models.Model):
    _name= 'biometric.machine'
    name = fields.Char("Machine IP")
    ref_name =  fields.Char("Location")
    port = fields.Integer("Port Number")
    address_id = fields.Many2one("res.partner",'Working Address')
    company_id = fields.Many2one("res.company","Company Name")

    @api.multi
    def update_users(self):
        zk = zklib.ZKLib(self.name, int(self.port))
        res = zk.connect()
        if res == True:
            zk.enableDevice()
            zk.disableDevice()
            users = zk.getUser()
            timesheet_obj = self.env['bio.machine.users']
            timesheet_obj.search([]).unlink()
            if (users):
                for user in users:
                    print users[user][1]
                    if users[user][2] == 14:
                        level = 'Admin'
                    else:
                        level = 'User'

                    employee_id = self.env['hr.employee'].search([('machine_id','=',users[user][0])]).id  
                    if(employee_id):
                        emp_id = employee_id
                    else: 
                        emp_id = None 
                    
                    valuessss={
                            'user_id': users[user][0],
                            'user_name': users[user][1],
                            'user_role': level,
                            'emp_id' : emp_id,
                            }
                    timesheet_obj.create(valuessss)
            
            zk.enableDevice()
            zk.disconnect()
            return True
        else:
            raise Warning(_('Unable to connect, please check the parameters and network connections.'))

    @api.multi
    def update_attandance(self):
        zk = zklib.ZKLib(self.name, int(self.port))
        res = zk.connect()
        if res == True:
            zk.enableDevice()
            zk.disableDevice()
            attendance = zk.getAttendance()
            timesheet_obj = self.env['bio.machine.attendance']
            if (attendance):
                for lattendance in attendance:
                    print lattendance
                    time_att = str(lattendance[2].date()) + ' ' +str(lattendance[2].time())
                    atten_time1 = datetime.strptime(str(time_att), '%Y-%m-%d %H:%M:%S')
                    atten_time = atten_time1 - timedelta(hours=5,minutes=30)
                    atten_time = datetime.strftime(atten_time,'%Y-%m-%d %H:%M:%S')
                    if lattendance[1] == 1:
                        state = 'Check In'
                    elif lattendance[1] == 0:
                        state = 'Check Out'
                    else:
                        state = 'Undefined'

                    valuessss={
                            'user_id': lattendance[0],
                            'time': atten_time,
                            'status': state,
                            }
                    timesheet_obj.create(valuessss)
            zk.clearAttendance()        
            zk.enableDevice()
            zk.disconnect()

            machine_att = self.env['bio.machine.attendance'].search([])
            hr_att = self.env['hr.attendance']
     
            if (machine_att):
                for att in machine_att:
                    print att
                    machine_user = self.env['bio.machine.users'].search([('user_id','=',att.user_id)])
                    if att.status == 'Check In':
                        action = 'sign_in'
                    elif att.status == 'Check Out':
                        action = 'sign_out' 
                    valuessss={
                        'name': att.time,
                        'employee_id': machine_user.emp_id,
                        'action': action,
                    }
                    hr_att.create(valuessss)
            machine_att.unlink() 
        else:
            raise Warning(_('Unable to connect, please check the parameters and network connections.'))

