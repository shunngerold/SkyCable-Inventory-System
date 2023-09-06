# -*- coding: utf-8 -*-
from odoo import models, fields, api

class subscriber(models.Model):
    _inherit = 'res.partner'

    subscriber = fields.Boolean()
