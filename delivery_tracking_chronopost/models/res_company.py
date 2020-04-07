# -*- coding: utf8 -*-
#
#    Copyright (C) 2020 NDP Systèmes (<http://www.ndp-systemes.fr>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    login_chronopost = fields.Char("Login Chronopost")
    password_chronopost = fields.Char("Password Chronopost")
    pre_alert_chronopost = fields.Selection([('0', u"Pas de préalerte"),
                                             ('11', u"Abonnement tracking expéditeur")],
                                            string=u"Pre Alert Chronopost", default='0')
    account_number_chronopost = fields.Char("Account Number Chronopost")
