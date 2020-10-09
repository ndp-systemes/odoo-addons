# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.http import request


class TrainingPortal(CustomerPortal):

    def _prepare_home_portal_values(self):
        values = super(TrainingPortal, self)._prepare_home_portal_values()

        # sessions not started
        values['session_count'] = request.env['training.sitting'].search_count([
            ('attendee_ids', 'in', request.env.user.partner_id.id),
            ('date', '>=', datetime.today()),
        ])
        # participated session
        values['participated_session_count'] = request.env['res.partner'].search_count([
            ('attendance', '=', 'done'),
            ('id', '=', request.env.user.partner_id.id),
        ])

        return values
