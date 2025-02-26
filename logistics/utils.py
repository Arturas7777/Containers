from io import BytesIO
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.core.mail import EmailMessage
from django.template.loader import render_to_string


def generate_invoice_pdf(invoice):
    buffer = BytesIO()
    p = canvas.Canvas(buffer)
    p.drawString(100, 800, f"Счет #{invoice.id}")
    p.drawString(100, 780, f"Клиент: {invoice.client.name}")
    p.drawString(100, 760, f"Сумма: {invoice.amount} USD")
    p.drawString(100, 740, f"Дата выставления: {invoice.issue_date}")
    p.drawString(100, 720, f"Срок оплаты: {invoice.due_date}")
    p.drawString(100, 700, f"Статус: {invoice.status}")
    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer


def send_invoice_email(invoice):
    pdf_buffer = generate_invoice_pdf(invoice)
    email = EmailMessage(
        subject=f"Счет #{invoice.id} - {invoice.client.name}",
        body=render_to_string("email/invoice_email.html", {"invoice": invoice}),
        from_email="yourcompany@example.com",
        to=[invoice.client.email],
    )
    email.attach(f"invoice_{invoice.id}.pdf", pdf_buffer.getvalue(), "application/pdf")
    email.send()