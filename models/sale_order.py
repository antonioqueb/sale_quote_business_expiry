from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _is_business_day(self, day):
        return day.weekday() < 5

    @api.model
    def _add_business_days(self, start_date, business_days):
        """Return the date reached after adding N business days.

        The creation date itself is not counted; only the following business days
        are considered.
        """
        current_date = start_date
        added_days = 0
        while added_days < business_days:
            current_date += timedelta(days=1)
            if self._is_business_day(current_date):
                added_days += 1
        return current_date

    @api.model
    def _business_days_between(self, start_date, end_date):
        """Business days between two dates.

        Count is exclusive of start_date and inclusive of end_date.
        """
        if start_date == end_date:
            return 0

        step = 1 if end_date > start_date else -1
        current_date = start_date
        days = 0
        while current_date != end_date:
            current_date += timedelta(days=step)
            if self._is_business_day(current_date):
                days += 1
        return days

    def _compute_default_validity_date(self):
        self.ensure_one()
        reference_dt = self.create_date or fields.Datetime.now()
        reference_date = fields.Datetime.context_timestamp(self, reference_dt).date()
        return self._add_business_days(reference_date, 10)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for order in records.filtered(lambda o: o.state in ("draft", "sent")):
            order.with_context(allow_quote_validity_write=True).write({
                "validity_date": order._compute_default_validity_date(),
            })
        return records

    def write(self, vals):
        if "validity_date" in vals and not self.env.context.get("allow_quote_validity_write"):
            protected_orders = self.filtered(lambda o: o.state in ("draft", "sent"))
            if protected_orders:
                raise UserError(_(
                    "La fecha de vencimiento de la cotización se calcula automáticamente a 10 días hábiles desde la creación y no es editable."
                ))
        return super().write(vals)

    def get_quote_expiry_report_message(self):
        self.ensure_one()

        if not self.validity_date:
            return _("Sin fecha de vencimiento configurada.")

        today = fields.Date.context_today(self)
        expiry_date = self.validity_date

        if today < expiry_date:
            remaining_days = self._business_days_between(today, expiry_date)
            if remaining_days == 0:
                return _("Cotización vigente. Vence hoy (%s).") % fields.Date.to_string(expiry_date)
            return _(
                "Cotización vigente. Vence en %(days)s día(s) hábil(es), el %(date)s."
            ) % {
                "days": remaining_days,
                "date": fields.Date.to_string(expiry_date),
            }

        if today == expiry_date:
            return _("Cotización vigente. Vence hoy (%s).") % fields.Date.to_string(expiry_date)

        expired_days = self._business_days_between(expiry_date, today)
        if expired_days == 0:
            return _("Cotización expirada. Venció el %s.") % fields.Date.to_string(expiry_date)

        return _(
            "Cotización expirada. Venció hace %(days)s día(s) hábil(es), el %(date)s."
        ) % {
            "days": expired_days,
            "date": fields.Date.to_string(expiry_date),
        }
