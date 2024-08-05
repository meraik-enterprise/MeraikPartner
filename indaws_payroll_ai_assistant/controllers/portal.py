from odoo import fields, http, SUPERUSER_ID, _
from odoo.http import request
from odoo.addons.portal.controllers import portal
from odoo.addons.portal.controllers.portal import pager as portal_pager
class CustomerPortal(portal.CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'doc_payroll_count' in counters:
            values['doc_payroll_count'] = self.get_doc_payroll_reports(only_count=True)
        return values

    def get_doc_payroll_reports(self, only_count=False):
        company_id = request.env.company
        doc_payroll_count = 0
        doc_payroll_ids = request.env["ir.attachment"]
        employee_id = request.env.user.employee_ids.filtered(
            lambda emp: emp.company_id.id == company_id.id and emp.employee_type == "employee"
        )[:1]
        if not employee_id:
            employee_id = request.env.user.employee_ids[:1]
        if employee_id:
            payroll_ai_log_ids = employee_id.payroll_ai_log_ids
            if payroll_ai_log_ids:
                doc_payroll_ids = payroll_ai_log_ids.mapped('attachment_id')
                doc_payroll_count = len(doc_payroll_ids.ids)
        return doc_payroll_count if only_count else doc_payroll_ids

    @http.route(['/my/doc_payrolls', '/my/doc_payrolls/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payroll_reports(self):
        values = self._prepare_doc_payrolls_rendering_values()
        return request.render("indaws_payroll_ai_assistant.portal_my_payroll_reports", values)

    def _prepare_doc_payrolls_rendering_values(
            self, page=1, sortby=None,
    ):
        attachment_ids = self.get_doc_payroll_reports()
        values = self._prepare_portal_layout_values()
        url = "/my/doc_payrolls"
        pager_values = portal_pager(
            url=url,
            total=len(attachment_ids),
            page=page,
            step=self._items_per_page,
        )
        values.update({
            'attachment_ids': attachment_ids,
            'page_name': 'doc_payroll_reports',
            'pager': pager_values,
            'default_url': url,
            'sortby': sortby,
        })
        return values
