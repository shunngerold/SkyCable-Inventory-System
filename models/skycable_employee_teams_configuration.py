# -*- coding: utf-8 -*-
from openerp import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime

class team_configuration(models.Model):
    _name = "team.configuration"
    _rec_name = "team_number"

    team_number = fields.Char(string="Team Code", required=True, copy=False, default="New")
    team_members = fields.One2many("team.configuration.line", "team_members_lines1")
    teamType = fields.Selection([("one_man", "1-man Team"),("two_man", "2-man Team")],default="one_man")

    @api.constrains("team_members", "teamType")
    def _validations(self):
        if self.teamType == "two_man":
            if len(self.team_members) > 2 or len(self.team_members) < 2:
                raise ValidationError("Wrong number of members.")

        if self.teamType == "one_man":
            if len(self.team_members) > 1:
                raise ValidationError("Exceed the maximum number of member(1).")

        if len(self.team_members) == 0:
            raise ValidationError("Invalid, Empty team members!")

    @api.model
    def create(self, vals):
        if vals.get("team_number", "New") == "New":
            vals["team_number"] = self.env["ir.sequence"].next_by_code("team_sequence") or "New"

        res = super(team_configuration, self).create(vals)
        for rec in res.team_members:
            rec.team_members_lines.write({"team_number_id": res.team_number})
            self.env["team.page.lines"].create({
                "team_page_lines": rec.team_members_lines.id,
                "team_number_team": res.team_number,
                "status": "permanent",
                "teamTypeHistory": res.teamType,
                "createdDateHistory": datetime.today(),
            })
        return res

    @api.multi
    def write(self, values):
        res = super(team_configuration, self).write(values)

        b = []
        c = []
        temp3 = []
        temp4 = []

        a = self.env["hr.employee"].search([("team_number_id", "=", self.team_number)])
        for recs in a:
            b.append(recs.id)

        for record in self.team_members:
            c.append(record.team_members_lines.id)

        for rec in c:
            if rec not in b:
                temp4.append(rec)

        if "teamType" in values:
            for rec in self.team_members:
                rec.team_members_lines.write({"team_number_id": self.team_number})
                c.append(rec.team_members_lines.id)
                self.env["team.page.lines"].create({
                    "team_page_lines": rec.team_members_lines.id,
                    "team_number_team": self.team_number,
                    "status": "permanent",
                    "teamTypeHistory": self.teamType,
                    "createdDateHistory": datetime.today(),
                })
        elif "team_members" in values:
            for rec1 in temp4:
                self.env["hr.employee"].search([("id", "=", rec1)]).write(
                    {"team_number_id": self.team_number}
                )
                self.env["team.page.lines"].create({
                    "team_page_lines": rec1,
                    "team_number_team": self.team_number,
                    "status": "permanent",
                    "teamTypeHistory": self.teamType,
                    "createdDateHistory": datetime.today(),
                })

        for element in b:
            if element not in c:
                temp3.append(element)

        for removed in temp3:
            self.env["hr.employee"].search([("id", "=", removed)]).write(
                {"team_number_id": ""}
            )
            self.env["team.page.lines"].create({
                "team_page_lines": removed,
                "team_number_team": self.team_number,
                "status": "removed",
                "teamTypeHistory": self.teamType,
                "createdDateHistory": datetime.today(),
            })

        return res

class team_configuration_line(models.Model):
    _name = "team.configuration.line"
    _rec_name = "team_members_lines"

    team_members_lines = fields.Many2one("hr.employee")
    team_members_lines1 = fields.Many2one("team.configuration")

    @api.model
    def create(self, vals):
        y = []
        x = self.env["team.configuration"].search([]).mapped("team_members")
        
        for rec in x:
            y.append(rec.team_members_lines.id)

        res = super(team_configuration_line, self).create(vals)

        if res.team_members_lines.id in y:
            raise ValidationError("Selecting same employee is not allowed!")
        return res

    @api.multi
    def write(self, vals):
        y = []
        x = self.env["team.configuration"].search([]).mapped("team_members")
        for rec in x:
            y.append(rec.team_members_lines.id)

        res = super(team_configuration_line, self).write(vals)

        if self.team_members_lines.id in y:
            raise ValidationError("Invalid team member")

        return res

    @api.onchange("team_members_lines")
    def _check_team_members(self):
        s = []
        x = self.env["team.configuration"].search([]).mapped("team_members")
        for rec in x:
            s.append(rec.team_members_lines.id)
        if self.team_members_lines.id in s:
            raise ValidationError("Employee already part of a team!")


class team_page(models.Model):
    _inherit = "hr.employee"

    history = fields.One2many("team.page.lines", "team_page_lines")
    team_number_id = fields.Char(readonly=True)

class team_page_lines(models.Model):
    _name = "team.page.lines"
    _rec_name = "team_page_lines"

    team_page_lines = fields.Many2one("hr.employee")
    team_number_team = fields.Char()
    transaction_number = fields.Char()
    status = fields.Selection([
            ("permanent", "Permanent"),
            ("temporary", "Temporary"),
            ("removed", "Removed"),
        ],
        default="permanent",
    )
    teamTypeHistory = fields.Selection([("one_man", "1-man Team"),("two_man", "2-man Team"),])
    createdDateHistory = fields.Date()
    replaced_by = fields.Char()