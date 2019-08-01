# -*- coding: utf8 -*-
#
#    Copyright (C) 2019 NDP Systèmes (<http://www.ndp-systemes.fr>).
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

import base64
import logging
import os

import unicodecsv as csv
from odoo import exceptions
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class CustomerFileToImport(models.Model):
    _name = 'customer.file.to.import'
    _order = 'sequence,id'

    name = fields.Char(string=u"Nom", required=True, readonly=True)
    asynchronous = fields.Boolean(string=u"Asynchronous importation", readonly=True)
    chunk_size = fields.Integer(string=u"Chunk size for asynchronous importation")
    file = fields.Binary(string=u"File to import", required=True, attachment=True)
    nb_columns = fields.Integer(string=u"Number of columns", readonly=True)
    state = fields.Selection([('draft', u"Never imported"),
                              ('processing', u"Processing"),
                              ('error', u"Error"),
                              ('done', u"Done")], string=u"State", required=True, default='draft')
    log_line_ids = fields.One2many('customer.importation.log.line', 'import_id', string=u"Log lines")
    csv_file_ids = fields.One2many('customer.generated.csv.file', 'import_id', string=u"Generated CSV files",
                                   readonly=True)
    sequence = fields.Integer(string=u"Séquence", readonly=True)
    extension = fields.Char(string=u"Extension", readonly=True, help=u"Example : '.xls', '.csv' or '.txt'")
    datas_fname = fields.Char(string=u"Donloaded file name", compute='_compute_datas_fname')

    @api.multi
    def _compute_datas_fname(self):
        for rec in self:
            rec.datas_fname = u"%s%s" % (rec.name, rec.extension)

    @api.multi
    def generate_out_csv_files_multi(self):
        for rec in self:
            rec.generate_out_csv_files()

    @api.multi
    def generate_out_csv_files(self):
        """Method to overwrite for each model"""
        self.ensure_one()
        self.log_info(u"Generating CSV file for %s" % self.name)
        self.state = 'draft'
        self.log_line_ids.unlink()
        self.csv_file_ids.unlink()

    @api.multi
    def import_actual_files(self):
        # TODO: coder un connecteur pour ordonner les traitements
        self.csv_file_ids.action_import()

    @api.multi
    def _log(self, msg, type='INFO'):
        self.ensure_one()
        if type == 'INFO':
            _logger.info(msg)
        elif type == 'WARNING':
            _logger.warning(msg)
        elif type == 'ERROR':
            _logger.error(msg)
        self.env['customer.importation.log.line'].create({
            'import_id': self.id,
            'type': type,
            'message': msg,
        })

    @api.multi
    def log_info(self, msg):
        self._log(msg)

    @api.multi
    def log_warning(self, msg):
        self._log(msg, type='WARNING')

    @api.multi
    def log_error(self, msg):
        self._log(msg, type='ERROR')

    @api.model
    def get_external_id_or_create_one(self, object):
        object.ensure_one()
        xlml_id = object.get_external_id()[object.id]
        if not xlml_id:
            self.env['ir.model.data'].create({'name': object._name.replace('.', '_') + '_' + str(object.id),
                                              'model': object._name,
                                              'res_id': object.id})
            xlml_id = object.get_external_id()[object.id]
        if not xlml_id:
            raise exceptions.UserError(u"Impossible de générer un ID XML pour l'objet %s" % object)
        return xlml_id

    @api.multi
    def save_generated_csv_file(self, model, fields_to_import, table_dict_result, sequence=0):
        self.ensure_one()
        file_path = os.tempnam() + '.csv'
        _logger.info(u"Importation file opened at path %s", file_path)
        with open(file_path, 'w') as out_file:
            out_file_csv = csv.writer(out_file)
            out_file_csv.writerow(['id'] + fields_to_import)
            for record_id in table_dict_result:
                out_file_csv.writerow([record_id] + [table_dict_result[record_id].get(field_name, '') for
                                                     field_name in fields_to_import])
        with open(file_path, 'r') as tmpfile:
            self.env['customer.generated.csv.file'].create({'import_id': self.id,
                                                            'model': model,
                                                            'sequence': sequence,
                                                            'generated_csv_file': base64.b64encode(tmpfile.read()),
                                                            'fields_to_import': str(['id'] + fields_to_import)})

    @api.multi
    def check_line_length(self, iterable):
        self.ensure_one()
        if len(iterable) != self.nb_columns:
            self.log_error(u"Importation file should have %s columns, not %s" % (self.nb_columns, len(iterable)))
            return False
        return True


class CustomerImportationLogLine(models.Model):
    _name = 'customer.importation.log.line'

    import_id = fields.Many2one('customer.file.to.import', string=u"File to import", readonly=True, required=True)
    type = fields.Selection([('ERROR', u"ERROR"), ('WARNING', u"WARNING"), ('INFO', u"INFO")],
                            string=u"Type", readonly=True, required=True)
    message = fields.Char(string=u"Message", readonly=True, required=True)


class CustomerGeneratedCsvFile(models.Model):
    _name = 'customer.generated.csv.file'
    _order = 'sequence, id'

    import_id = fields.Many2one('customer.file.to.import', string=u"File to import", readonly=True, required=True)
    generated_csv_file = fields.Binary(string=u"Generated CSV File", readonly=True, required=True)
    model = fields.Char(string=u"Model", readonly=True, required=True)
    sequence = fields.Integer(string=u"Sequence", readonly=True)
    datas_fname = fields.Char(string=u"Donloaded file name", compute='_compute_datas_fname')
    fields_to_import = fields.Char(string=u"Fields to import", readonly=True)

    @api.multi
    def _compute_datas_fname(self):
        for rec in self:
            rec.datas_fname = u"%s.csv" % rec.model

    @api.multi
    def get_default_option(self):
        self.ensure_one()
        return {u'datetime_format': u'%Y-%m-%d %H:%M:%S',
                u'date_format': u"%Y-%m-%d",
                u'keep_matches': False,
                u'encoding': u'utf-8',
                u'fields': [],
                u'quoting': u'"',
                u'headers': True,
                u'separator': u',',
                u'float_thousand_separator': u',',
                u'float_decimal_separator': u'.',
                u'advanced': True}

    @api.multi
    def get_default_values_for_importation_wizard(self):
        self.ensure_one()
        return {
            'res_model': self.model,
            'file': self.generated_csv_file.decode('base64'),
            'file_name': self.datas_fname,
            'file_type': 'text/csv',
        }

    @api.model
    def raise_error_if_needed(self, importation_result):
        if importation_result:
            msg_unknown_error = u"""Unknown error"""
            error_msg = u""""""
            error = False
            for item in importation_result:
                if item.get('type') == 'error':
                    error = True
                    if error_msg:
                        error_msg += u"""\r"""
                    error_msg += u"""%s""" % item.get('message', msg_unknown_error)
            if error:
                if not error_msg:
                    error_msg = msg_unknown_error
                raise exceptions.UserError(u"""Importation failed\r%s""" % error_msg)

    @api.multi
    def action_import(self):
        for rec in self:
            default_values_for_importation_wizard = rec.get_default_values_for_importation_wizard()
            wizard = self.env['base_import.import'].create(default_values_for_importation_wizard)
            options = rec.get_default_option()
            if rec.import_id.asynchronous:
                options[u'use_queue'] = True
                options[u'chunk_size'] = rec.import_id.chunk_size
            importation_result = wizard.do(fields=eval(rec.fields_to_import), options=options)
            self.raise_error_if_needed(importation_result)
