# -*- coding: utf-8 -*-
import datetime
import logging
from collections import defaultdict

import pytz

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

from odoo.tools import attrgetter

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")


class BiometricDeviceDetails(models.Model):
    """Model for configuring and connect the biometric device with odoo"""
    _name = 'biometric.device.details'
    _description = 'Biometric Device Details'

    name = fields.Char(string='Name', required=True, help='Record Name')
    device_ip = fields.Char(string='Device IP', required=True,
                            help='The IP address of the Device')
    port_number = fields.Integer(string='Port Number', required=True,
                                 help="The Port Number of the Device")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda
                                     self: self.env.user.company_id.id,
                                 help='Current Company')
    date_to = fields.Date(string="Date Range", default=fields.Date.today)
    date_from = fields.Date(string="Date from", default=fields.Date.today)

    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception:
            return False

    def action_test_connection(self):
        """Checking the connection status"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=30,
                password=False, ommit_ping=False)
        try:
            if zk.connect():
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': 'Successfully Connected',
                        'type': 'success',
                        'sticky': False
                    }
                }
        except Exception as error:
            raise ValidationError(f'{error}')


    def action_download_attendance(self):
        """Function to download attendance records from the device"""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        hr_attendance = self.env['hr.attendance']
        for info in self:
            machine_ip = info.device_ip
            zk_port = info.port_number
            try:
                # Connecting with the device with the ip and port provided
                zk = ZK(machine_ip, port=zk_port, timeout=30,
                        password=0,
                        force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                conn.disable_device()
                user = conn.get_users()
                attendance = conn.get_attendance()
                if attendance:
                    attendance_dict = defaultdict(list)
                    for each in attendance:
                        atten_time = each.timestamp
                        local_tz = pytz.timezone(
                            self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        atten_time = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        atten_time_datetime = datetime.strptime(atten_time, "%Y-%m-%d %H:%M:%S")
                        atten_date = atten_time_datetime.date()
                        if info.date_to <= atten_date <= info.date_from:
                            attendance_dict[each.user_id].append({
                                'punch': each.punch,
                                'timestamp': atten_time_datetime,
                            })
                    for user_id, records in attendance_dict.items():
                        records.sort(key=lambda x: x['timestamp'])
                        for user_id, records in attendance_dict.items():
                            records.sort(key=lambda x: x['timestamp'])
                            existing_attendances = zk_attendance.search([('device_id_num', '=', user_id)])
                            existing_attendances_dates = {attendance.check_in.date() for attendance in
                                                          existing_attendances}

                            for record in records:
                                if len(records) == 2:
                                    if record['timestamp'].date() not in existing_attendances_dates:
                                        zk_attendance.create({
                                            'device_id_num': user_id,
                                            'check_in': records[0].get('timestamp').strftime("%Y-%m-%d %H:%M:%S"),
                                            'i_check': 'i',
                                            'check_out': records[1].get('timestamp').strftime("%Y-%m-%d %H:%M:%S"),
                                            'o_check': 'o'
                                        })
                                else:
                                    if record.get('punch') == 0:
                                        if record['timestamp'].date() not in existing_attendances_dates:
                                            zk_attendance.create({
                                                'device_id_num': user_id,
                                                'check_in': records[0].get('timestamp').strftime("%Y-%m-%d %H:%M:%S"),
                                                'i_check': 'i',
                                            })
                                    else:
                                        if record['timestamp'].date() not in existing_attendances_dates:
                                            zk_attendance.create({
                                                'device_id_num': user_id,
                                                'check_in': record['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                                                'check_out': record['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                                                'i_check': 'i',
                                                'o_check': 'o',
                                                'is_danger': False,
                                            })

                conn.disconnect()
                return True
            else:
                raise UserError(_('Unable to connect, please check the'
                                  'parameters and network connections.'))

        else:
            raise UserError(_('Unable to get the attendance log, please'
                              'try again later.'))

    def action_restart_device(self):
        """For restarting the device"""
        zk = ZK(self.device_ip, port=self.port_number, timeout=15,
                password=0,
                force_udp=False, ommit_ping=False)
        self.device_connect(zk).restart()
