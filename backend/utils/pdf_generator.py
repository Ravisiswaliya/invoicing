import os
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from django.conf import settings


def generate_pdf(data, filename="document.pdf", doc_type="invoice"):
    elements = []
    page_width = 595
    margin = 30
    usable_width = page_width - 2 * margin

    logo_width, logo_height = 40, 30
    company_width = 0.55 * usable_width
    header_width = usable_width - logo_width - company_width

    # --- Styles ---
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Heading", fontSize=14, leading=16, alignment=1, spaceAfter=12
        )
    )
    styles.add(
        ParagraphStyle(
            name="Bold",
            fontSize=10,
            leading=12,
            spaceAfter=6,
            fontName="Helvetica-Bold",
        )
    )
    styles.add(
        ParagraphStyle(name="RightAlign", fontSize=10, alignment=2, spaceBefore=40)
    )

    # --- Save Path ---
    folder = "invoices" if doc_type == "invoice" else "quotations"
    save_dir = os.path.join(settings.MEDIA_ROOT, folder)
    os.makedirs(save_dir, exist_ok=True)
    full_path = os.path.join(save_dir, filename)

    # --- Seller & Buyer ---
    seller = data["party"]["user"]
    buyer = data["party"]
    # --- Document Title ---
    elements.append(Paragraph(doc_type.upper(), styles["Heading"]))

    # --- Top-left Logo & Company Info Table ---
    logo_element = None
    logo_path = seller.get("logo")

    if logo_path:
        logo_full_path = os.path.join(settings.MEDIA_ROOT, logo_path.split("/")[-1])

        if os.path.exists(logo_full_path):
            logo_element = Image(logo_full_path, width=logo_width, height=logo_height)

    # Company info text
    company_info = f"""
        <b>{seller['company_name']}</b><br/>
        {seller['address']}, {seller['city']}<br/>
        GSTIN: {seller['gstin'] or '-'} | PAN: {seller['pan'] or '-'}<br/>
        State: {seller['state']} ({seller['statecode']})<br/>
        Mobile: {seller['mobile'] or '-'}
    """
    company_paragraph = Paragraph(company_info, styles["Normal"])

    # --- Document Header (Invoice/Quotation info) ---
    if doc_type == "invoice":
        header_info = f"""
            <b>Invoice No:</b> {data['billno']}<br/>
            <b>Date:</b> {data['date']}<br/>
            <b>Place of Supply:</b> {data.get('placeofsupply') or '-'}
        """
    else:
        header_info = f"""
            <b>Quotation No:</b> {data['quotationno']}<br/>
            <b>Date:</b> {data['date']}<br/>
            <b>Subject:</b> {data['subject']}
        """
    # elements.append(Paragraph(header_info, styles["Normal"]))
    # elements.append(Spacer(1, 12))
    header_paragraph = Paragraph(header_info, styles["Normal"])

    # Combine logo and company info into one row
    # Combine logo, company info, and invoice/quotation info
    if logo_element:
        header_table = Table(
            [[logo_element, company_paragraph, header_paragraph]],
            colWidths=[logo_width, company_width, header_width],
            hAlign="LEFT",
        )
    else:
        header_table = Table(
            [[company_paragraph, header_paragraph]],
            colWidths=[0.65 * usable_width, 0.35 * usable_width],
            hAlign="LEFT",
        )

    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # --- Buyer Info ---
    buyer_label = "Bill To:" if doc_type == "invoice" else "Quotation For:"
    elements.append(Paragraph(f"<b>{buyer_label}</b>", styles["Bold"]))
    buyer_info = f"""
        {buyer['name']}<br/>
        {buyer['address']}, {buyer['city']}<br/>
        GSTIN: {buyer.get('gstin') or '-'}<br/>
        State: {buyer['state']} ({buyer['statecode']})
    """
    elements.append(Paragraph(buyer_info, styles["Normal"]))
    elements.append(Spacer(1, 12))

    # --- Product Table ---
    details_key = "productdetails" if doc_type == "invoice" else "quotationdetails"
    header_color = (
        colors.HexColor("#4A90E2")
        if doc_type == "invoice"
        else colors.HexColor("#7B68EE")
    )

    product_data = [
        [
            "Description",
            "HSN",
            "Qty",
            "Unit",
            "Unit Price",
            "CGST%",
            "SGST%",
            "IGST%",
            "Total",
        ]
    ]
    subtotal, gst_total = 0, 0
    for p in data[details_key]:
        item_price = float(p["unit_price"]) * p["product_quantity"]
        subtotal += item_price
        gst_total += float(p["single_item_total_gst"])
        product_data.append(
            [
                p["product_discription"],
                p.get("hsncode") or "-",
                p["product_quantity"],
                p.get("unit_type") or "-",
                f"{p['unit_price']}",
                f"{p['cgst']}%",
                f"{p['sgst']}%",
                f"{p['igst']}%",
                f"{p['single_item_total_amount_after_tax']}",
            ]
        )

    product_table = Table(
        product_data, repeatRows=1, colWidths=[120, 50, 40, 50, 60, 50, 50, 50, 80]
    )
    product_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), header_color),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]
        )
    )
    elements.append(product_table)
    elements.append(Spacer(1, 12))

    # --- Summary ---
    if doc_type == "invoice":
        grand_total = subtotal + gst_total
    else:
        grand_total = float(data["total_amount_after_gst"])
        gst_total = float(data["total_gst_amount"])

    summary_data = [
        ["Subtotal", f"{subtotal:.2f}"],
        ["GST Total", f"{gst_total:.2f}"],
        ["Grand Total", f"{grand_total:.2f} INR"],
    ]
    summary_table = Table(summary_data, colWidths=[400, 120])
    summary_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
            ]
        )
    )
    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # --- Bank Details ---
    elements.append(Paragraph("<b>Bank Details:</b>", styles["Bold"]))
    bank_info = (
        f"Bank: {seller.get('bank_name','')} | "
        f"A/c: {seller.get('bank_account','')} | "
        f"IFSC: {seller.get('bank_ifsc','')} | "
        f"SWIFT: {seller.get('swift_code','')}"
    )
    elements.append(Paragraph(bank_info, styles["Normal"]))
    elements.append(Spacer(1, 20))

    # --- Terms & Conditions ---
    elements.append(Paragraph("<b>Terms & Conditions:</b>", styles["Bold"]))
    elements.append(Paragraph(data["tc"], styles["Normal"]))
    elements.append(Spacer(1, 30))

    # --- Signature ---
    elements.append(Paragraph("For " + seller["company_name"], styles["RightAlign"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph("Authorized Signatory", styles["RightAlign"]))

    # --- Build PDF ---
    doc = SimpleDocTemplate(full_path, pagesize=A4)
    doc.build(elements)

    relative_path = os.path.relpath(full_path, settings.MEDIA_ROOT)
    print(f"{doc_type.capitalize()} generated: {relative_path}")
    return relative_path


# import os
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
# from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
# from reportlab.lib import colors
# from django.conf import settings
# from reportlab.platypus import Image


# def generate_pdf(data, filename="document.pdf", doc_type="invoice"):
#     """
#     Generate PDF for Invoice or Quotation.
#     :param data: dict containing invoice/quotation data
#     :param filename: output PDF filename
#     :param doc_type: "invoice" or "quotation"
#     """
#     elements = []
#     seller = data["party"]["user"]

#     # --- Logo ---
#     logo_path = seller.get("logo")

#     if logo_path:
#         # assume logo_path is relative to MEDIA_ROOT
#         logo_path_full = os.path.join(settings.MEDIA_ROOT, logo_path.split("/")[-1])
#         if os.path.exists(logo_path_full):
#             logo = Image(logo_path_full, width=40, height=30)  # adjust size
#             logo.hAlign = "LEFT"
#             elements.append(logo)
#             elements.append(Spacer(1, 1))  # space after logo
#     else:
#         print("Logo not found")
#     # Decide save folder
#     folder = "invoices" if doc_type == "invoice" else "quotations"
#     save_dir = os.path.join(settings.MEDIA_ROOT, folder)
#     os.makedirs(save_dir, exist_ok=True)
#     full_path = os.path.join(save_dir, filename)

#     doc = SimpleDocTemplate(full_path, pagesize=A4)

#     # --- Styles ---
#     styles = getSampleStyleSheet()
#     styles.add(
#         ParagraphStyle(
#             name="Heading", fontSize=14, leading=16, alignment=1, spaceAfter=12
#         )
#     )
#     styles.add(
#         ParagraphStyle(
#             name="Bold",
#             fontSize=10,
#             leading=12,
#             spaceAfter=6,
#             fontName="Helvetica-Bold",
#         )
#     )
#     styles.add(
#         ParagraphStyle(name="RightAlign", fontSize=10, alignment=2, spaceBefore=40)
#     )

#     # --- Header ---
#     elements.append(Paragraph(doc_type.upper(), styles["Heading"]))

#     seller = data["party"]["user"]
#     buyer = data["party"]

#     # Document-specific header fields
#     if doc_type == "invoice":
#         header_info = f"""
#             <b>Invoice No:</b> {data['billno']}<br/>
#             <b>Date:</b> {data['date']}<br/>
#             <b>Place of Supply:</b> {data.get('placeofsupply') or '-'}
#         """
#     else:  # quotation
#         header_info = f"""
#             <b>Quotation No:</b> {data['quotationno']}<br/>
#             <b>Date:</b> {data['date']}<br/>
#             <b>Subject:</b> {data['subject']}
#         """

#     header_table = [
#         [
#             Paragraph(
#                 f"""
#                 <b>{seller['company_name']}</b><br/>
#                 {seller['address']}, {seller['city']}<br/>
#                 GSTIN: {seller['gstin']} | PAN: {seller['pan']}<br/>
#                 State: {seller['state']} ({seller['statecode']})<br/>
#                 Mobile: {seller['mobile']}
#                 """,
#                 styles["Normal"],
#             ),
#             Paragraph(header_info, styles["Normal"]),
#         ]
#     ]
#     t = Table(header_table, colWidths=[300, 200])
#     t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
#     elements.append(t)
#     elements.append(Spacer(1, 12))

#     # --- Buyer Info ---
#     buyer_label = "Bill To:" if doc_type == "invoice" else "Quotation For:"
#     elements.append(Paragraph(f"<b>{buyer_label}</b>", styles["Bold"]))
#     elements.append(
#         Paragraph(
#             f"""
#             {buyer['name']}<br/>
#             {buyer['address']}, {buyer['city']}<br/>
#             GSTIN: {buyer['gstin'] or '-'}<br/>
#             State: {buyer['state']} ({buyer['statecode']})
#             """,
#             styles["Normal"],
#         )
#     )
#     elements.append(Spacer(1, 12))

#     # --- Product Table ---
#     details_key = "productdetails" if doc_type == "invoice" else "quotationdetails"
#     header_color = (
#         colors.HexColor("#4A90E2")
#         if doc_type == "invoice"
#         else colors.HexColor("#7B68EE")
#     )

#     product_data = [
#         [
#             "Description",
#             "HSN",
#             "Qty",
#             "Unit",
#             "Unit Price",
#             "CGST%",
#             "SGST%",
#             "IGST%",
#             "Total",
#         ]
#     ]

#     subtotal, gst_total = 0, 0
#     for p in data[details_key]:
#         item_price = float(p["unit_price"]) * p["product_quantity"]
#         subtotal += item_price
#         gst_total += float(p["single_item_total_gst"])
#         product_data.append(
#             [
#                 p["product_discription"],
#                 p.get("hsncode") or "-",
#                 p["product_quantity"],
#                 p.get("unit_type") or "-",
#                 f"{p['unit_price']}",
#                 f"{p['cgst']}%",
#                 f"{p['sgst']}%",
#                 f"{p['igst']}%",
#                 f"{p['single_item_total_amount_after_tax']}",
#             ]
#         )

#     product_table = Table(
#         product_data, repeatRows=1, colWidths=[120, 50, 40, 50, 60, 50, 50, 50, 80]
#     )
#     product_table.setStyle(
#         TableStyle(
#             [
#                 ("BACKGROUND", (0, 0), (-1, 0), header_color),
#                 ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
#                 ("ALIGN", (0, 0), (-1, -1), "CENTER"),
#                 ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
#             ]
#         )
#     )
#     elements.append(product_table)
#     elements.append(Spacer(1, 12))

#     # --- Summary ---
#     if doc_type == "invoice":
#         grand_total = subtotal + gst_total
#     else:  # quotation values come from API
#         grand_total = float(data["total_amount_after_gst"])
#         gst_total = float(data["total_gst_amount"])

#     summary_data = [
#         ["Subtotal", f"{subtotal:.2f}"],
#         ["GST Total", f"{gst_total:.2f}"],
#         ["Grand Total", f"{grand_total:.2f} INR"],
#     ]
#     summary_table = Table(summary_data, colWidths=[400, 120])
#     summary_table.setStyle(
#         TableStyle(
#             [
#                 ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
#                 ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
#                 ("LINEABOVE", (0, 0), (-1, 0), 0.5, colors.black),
#                 ("LINEABOVE", (0, -1), (-1, -1), 1, colors.black),
#             ]
#         )
#     )
#     elements.append(summary_table)
#     elements.append(Spacer(1, 20))

#     # --- Bank Details ---
#     elements.append(Paragraph("<b>Bank Details:</b>", styles["Bold"]))
#     bank_info = (
#         f"Bank: {seller.get('bank_name', '')} | "
#         f"A/c: {seller.get('bank_account', '')} | "
#         f"IFSC: {seller.get('bank_ifsc', '')} | "
#         f"SWIFT: {seller.get('swift_code', '')} "
#     )
#     elements.append(Paragraph(bank_info, styles["Normal"]))
#     elements.append(Spacer(1, 20))

#     # --- Terms & Conditions ---
#     elements.append(Paragraph("<b>Terms & Conditions:</b>", styles["Bold"]))
#     elements.append(Paragraph(data["tc"], styles["Normal"]))
#     elements.append(Spacer(1, 30))

#     # --- Signature Section ---
#     elements.append(Paragraph("For " + seller["company_name"], styles["RightAlign"]))
#     elements.append(Spacer(1, 20))
#     elements.append(Paragraph("Authorized Signatory", styles["RightAlign"]))

#     # Build PDF
#     doc.build(elements)

#     relative_path = os.path.relpath(full_path, settings.MEDIA_ROOT)
#     print(f"{doc_type.capitalize()} generated: {relative_path}")
#     return relative_path
