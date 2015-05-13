# -*- coding: utf8 -*-
#
# Copyright (C) 2014 NDP Systèmes (<http://www.ndp-systemes.fr>).
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

from datetime import datetime
from dateutil.relativedelta import relativedelta

from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from openerp import fields, models, api, _

class purchase_order_line_jit(models.Model):
    _inherit = 'purchase.order.line'

    line_no = fields.Char("Line no.")
    ack_ref = fields.Char("Acknowledge Reference", help="Reference of the supplier's last reply to confirm the delivery"
                                                        " at the planned date")
    date_ack = fields.Date("Last Acknowledge Date",
                           helps="Last date at which the supplier confirmed the delivery at the planned date.")
    opmsg_type = fields.Selection([('no_msg',"Ok"), ('late',"LATE"), ('early',"EARLY")], compute="_compute_opmsg",
                                  string="Message Type")
    opmsg_delay = fields.Integer("Message Delay", compute="_compute_opmsg")
    opmsg_reduce_qty = fields.Float("Quantity to reduce")
    opmsg_text = fields.Char("Operational message", compute="_compute_opmsg_text",
                         help="This field holds the operational messages generated by the system to the operator")

    @api.depends('date_planned','date_required')
    def _compute_opmsg(self):
        for rec in self:
            date_planned = datetime.strptime(rec.date_planned, DEFAULT_SERVER_DATE_FORMAT)
            date_required = datetime.strptime(rec.date_required, DEFAULT_SERVER_DATE_FORMAT)
            min_late_days = int(self.env['ir.config_parameter'].get_param(
                                                              "purchase_procurement_just_in_time.opmsg_min_late_delay"))
            min_early_days = int(self.env['ir.config_parameter'].get_param(
                                                             "purchase_procurement_just_in_time.opmsg_min_early_delay"))
            if date_planned >= date_required:
                delta = date_planned - date_required
                if delta.days >= min_late_days:
                    rec.opmsg_type = 'late'
                    rec.opmsg_delay = delta.days
            else:
                delta = date_required - date_planned
                if delta.days >= min_early_days:
                    rec.opmsg_type = 'early'
                    rec.opmsg_delay = delta.days

    @api.depends('opmsg_type','opmsg_delay','opmsg_reduce_qty')
    def _compute_opmsg_text(self):
        for rec in self:
            msg = ""
            if rec.opmsg_reduce_qty > 0:
                msg += _("REDUCE QTY by %.1f %s ") % (rec.opmsg_reduce_qty, rec.product_uom.name)
            if rec.opmsg_type == 'early':
                msg += _("EARLY by %i day(s)") % rec.opmsg_delay
            elif rec.opmsg_type == 'late':
                msg += _("LATE by %i day(s)") % rec.opmsg_delay
            rec.opmsg_text = msg

    @api.multi
    def open_form_purchase_order_line(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order.line',
            'name': _("Purchase Order Line: %s") % int(self.line_no),
            'views': [(False, "form")],
            'res_id': self.id,
            'context': {}
        }


    @api.model
    def create(self, vals):
        maximum = 0
        if not vals.get('line_no', False):
            list_line_no = []
            order = self.env['purchase.order'].browse(vals['order_id'])
            for item in [l.line_no for l in order.order_line]:
                try:
                    list_line_no.append(int(item))
                except ValueError:
                    pass
            theo_value = 10*(1 + len(self.env['purchase.order'].browse(vals['order_id']).order_line))
            if list_line_no != []:
                maximum = max(list_line_no)
            if maximum >= theo_value or theo_value in list_line_no:
                theo_value = maximum + 10
            vals['line_no'] = str(theo_value)
        return super(purchase_order_line_jit, self).create(vals)


class procurement_order_purchase_jit(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def propagate_cancel(self, procurement):
        # TODO: Mettre à jour opmsg_reduce_qty dans la fonction
        # if procurement.rule_id.action == 'buy' and procurement.purchase_line_id:
        #     uom_obj = self.pool.get("product.uom")
        #     purchase_line_obj = self.pool.get('purchase.order.line')
        #     uom = procurement.purchase_line_id.product_uom
        #     product_qty = uom_obj._compute_qty_obj(cr, uid, procurement.product_uom, procurement.product_qty, uom, context=context)
        #     if procurement.purchase_line_id.state not in ('draft', 'cancel'):
        #             raise osv.except_osv(_('Error!'),
        #                 _('Can not cancel this procurement as the related purchase order has been confirmed already.  Please cancel the purchase order first. '))
        #     if float_compare(procurement.purchase_line_id.product_qty, product_qty, 0, precision_rounding=uom.rounding) > 0:
        #         purchase_line_obj.write(cr, uid, [procurement.purchase_line_id.id], {'product_qty': procurement.purchase_line_id.product_qty - product_qty}, context=context)
        #     else:
        #         purchase_line_obj.action_cancel(cr, uid, [procurement.purchase_line_id.id], context=context)
        return super(procurement_order_purchase_jit, self).propagate_cancel(procurement)