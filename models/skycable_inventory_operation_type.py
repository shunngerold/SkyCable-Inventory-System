from odoo import api, fields, models
import time
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime

class stock_picking_inherit(models.Model):
    _inherit = 'stock.picking.type'
    subscriber_checkbox = fields.Boolean('Subscriber')