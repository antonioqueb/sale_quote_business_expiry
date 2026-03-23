{
    "name": "Sales Quotation Business Expiry",
    "summary": "Sets quotation expiration to 10 business days and shows expiry status on the printed report.",
    "version": "19.0.1.0.0",
    "category": "Sales/Sales",
    "author": "OpenAI",
    "license": "LGPL-3",
    "depends": ["sale"],
    "data": [
        "views/sale_order_views.xml",
        "report/sale_report_templates.xml",
    ],
    "installable": True,
    "application": False,
}
