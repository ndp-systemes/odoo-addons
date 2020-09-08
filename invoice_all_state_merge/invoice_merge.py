# -*- coding: utf8 -*-
#
# Copyright (C) 2017 NDP Systèmes (<http://www.ndp-systemes.fr>).
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
from openerp import models, fields, api
from openerp.tools.translate import _
from openerp import exceptions


class InvoiceMergeExtends(models.TransientModel):
    _inherit = 'invoice.merge'

    description = fields.Char(u"Description", default="Merge invoice", required=True)
    auto_set_payment = fields.Boolean(u"Open Invoice")
    only_invoice = fields.Boolean(u"Only type invoice selected", readonly=True)

    @api.model
    def default_get(self, fields_list):
        defaults = super(InvoiceMergeExtends, self).default_get(fields_list)
        ids = self.env.context.get('active_ids', [])
        selected = self.env['account.invoice'].browse(ids)
        defaults['description'] = \
            _(u"Merge of ") + ", ".join([b for b in selected.mapped('number') if b])
        defaults['date_invoice'] = fields.Date.today()
        defaults['only_invoice'] = all([invoice.type in ('in_invoice', 'out_invoice') for invoice in selected])
        return defaults

    @api.model
    def _dirty_check(self):
        if self.env.context.get('active_model', '') == 'account.invoice':
            ids = self.env.context['active_ids']
            if len(ids) < 2:
                raise exceptions.Warning(
                    _('Please select multiple invoice to merge in the list '
                      'view.'))

            invs = self.env['account.invoice'].browse(ids)
            for d in invs:
                if d['account_id'] != invs[0]['account_id']:
                    raise exceptions.Warning(
                        _('Not all invoices use the same account!'))
                if d['company_id'] != invs[0]['company_id']:
                    raise exceptions.Warning(
                        _('Not all invoices are at the same company!'))
                if d['partner_id'] != invs[0]['partner_id']:
                    if d['type'] in ('in_invoice', 'in_refund'):
                        raise exceptions.Warning(
                            _('Not all invoices are for the same supplier!'))
                    else:
                        raise exceptions.Warning(
                            _('Not all invoices are for the same customer!'))
                if d['type'] != invs[0]['type']:
                    raise exceptions.Warning(
                        _('Not all invoices are of the same type!'))
                if d['currency_id'] != invs[0]['currency_id']:
                    raise exceptions.Warning(
                        _('Not all invoices are at the same currency!'))
                if d['journal_id'] != invs[0]['journal_id']:
                    raise exceptions.Warning(
                        _('Not all invoices are at the same journal!'))
        return {}

    @api.multi
    def merge_invoices(self):
        invoice_obj = self.env['account.invoice']
        invoices_to_merge = invoice_obj.browse(self.env.context.get('active_ids', []))
        draft_invoices = invoice_obj
        payments_to_reconcile = self.env['account.move.line']
        if not all([invoice.partner_id == invoices_to_merge[0].partner_id for invoice in invoices_to_merge]):
            raise exceptions.UserError(_(u"You can't merge multiple invoice without the same Partner"))

        for invoice_to_merge in invoices_to_merge:
            payments_to_reconcile |= invoice_to_merge.payment_ids
            # Remove payment
            invoice_to_merge.payment_ids._remove_move_reconcile()
            # Creates refund + draft invoice for each invoice opened or paid
            if invoice_to_merge.state != 'draft':
                res = self.env['account.invoice.refund'] \
                    .with_context(active_ids=[invoice_to_merge.id], active_id=invoice_to_merge.id) \
                    .create(self._value_create_refund()) \
                    .invoice_refund()
                if res and 'domain' in res:
                    # get the newly created draft invoice
                    domain = res['domain']
                    domain.pop(0)  # remove ('type', '=', 'in_refund') from domain since we want the 'draft' one
                    domain = domain + [('state', '=', 'draft')]
                    draft_invoices |= invoice_obj.search(domain)
            else:
                draft_invoices |= invoice_to_merge
        res = super(InvoiceMergeExtends, self.with_context(active_ids=draft_invoices.ids)).merge_invoices()
        merged_invoice_result = invoice_obj.browse(set(res['domain'][0][2]) - set(draft_invoices.ids))
        for id_invoice, dict_value in merged_invoice_result._prepare_data_post_merge(draft_invoices).iteritems():
            invoice_obj.browse(id_invoice).write(dict_value)
        # Let's unlink draft invoices created to generate the merged one
        draft_invoices.unlink()
        if self.auto_set_payment and self.only_invoice:
            merged_invoice_result.signal_workflow('invoice_open')
            merged_invoice_result.register_payment(payments_to_reconcile)
        return res

    @api.multi
    def _value_create_refund(self):
        self.ensure_one()
        return dict(self.env['account.invoice.refund'].default_get(['keep_references', 'date_invoice']),
                    filter_refund='modify',
                    description=self.description,
                    date=self.date_invoice or fields.Date.today())


class InvoiceMerge(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _prepare_data_post_merge(self, old_invoices):
        return {invoice.id: {} for invoice in self}
