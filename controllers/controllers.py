# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

# class Sample(http.Controller):
#     @http.route('/sample/sample/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/sample/sample/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('sample.listing', {
#             'root': '/sample/sample',
#             'objects': http.request.env['sample.sample'].search([]),
#         })

#     @http.route('/sample/sample/objects/<model("sample.sample"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('sample.object', {
#             'object': obj
#         })

class Team(http.Controller):
    @http.route("/teams", type="http", auth="public", website=True)
    def teamList(self, **kw):
        employees = request.env["team.configuration"].sudo().search([])
        return request.render("skycable_employee_inventory.team_page", {"employees": employees})

class Register(http.Controller):
    @http.route("/signup", type="http", auth="public", website=True)
    def registration_form(self, **kw):
        return http.request.render("skycable_employee_inventory.register_user", {})

    @http.route("/signup/submit", type="http", auth="public", website=True)
    def submit_form(self, **kw):
        t = []
        Teachers = http.request.env["res.users"].sudo().search([])
        for teacher in Teachers:
            t.append(teacher.email)
        if kw.get("email") in t:
            return request.render("skycable_employee_inventory.tmp_user_form_invalid", {})
        else:
            user = (
                http.request.env["res.users"]
                .sudo()
                .create(
                    {
                        "name": kw.get("fname"),
                        "email": kw.get("email"),
                        "login": kw.get("email"),
                    }
                )
            )
            vals = {
                "user": user,
            }
            return request.render("skycable_employee_inventory.tmp_user_form_success", vals)
