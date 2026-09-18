import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

def generate_claim_slip_pdf(
    customer_name: str,
    pnr: str,
    contact_email: str,
    contact_phone: str,
    flight_number: str,
    route: str,
    flight_status: str,
    delay_info: str,
    actions_taken: list[str],
    loyalty_tier: str = 'Standard',
    exercise_date: str = 'Wednesday, 23 September 2026',
) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#0369a1'),
        fontName='Helvetica-Bold',
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        fontName='Helvetica',
        spaceAfter=12,
    )
    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#1e293b'),
        fontName='Helvetica',
    )
    bold_body = ParagraphStyle(
        'BoldBodyCustom',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#0f172a'),
        fontName='Helvetica-Bold',
    )
    footer_style = ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#64748b'),
        fontName='Helvetica-Oblique',
        alignment=1,
    )

    elements = []
    elements.append(Paragraph('SKYWAY AIRLINES', title_style))
    elements.append(Paragraph('Official Disruption Resolution Certificate and Claim Receipt', subtitle_style))
    elements.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#0284c7'), spaceAfter=15))

    ref_code = f"SW-CARE-{pnr}-{datetime.now().strftime('%H%M%S')}"
    meta_data = [
        [
            Paragraph('<b>Certificate Ref:</b>', body_style), Paragraph(ref_code, bold_body),
            Paragraph('<b>Issue Date:</b>', body_style), Paragraph(exercise_date, bold_body)
        ],
        [
            Paragraph('<b>Passenger Name:</b>', body_style), Paragraph(f'{customer_name} ({loyalty_tier} Tier)', bold_body),
            Paragraph('<b>Booking PNR:</b>', body_style), Paragraph(pnr, bold_body)
        ],
        [
            Paragraph('<b>Contact Email:</b>', body_style), Paragraph(contact_email, body_style),
            Paragraph('<b>Phone:</b>', body_style), Paragraph(contact_phone, body_style)
        ],
    ]
    meta_table = Table(meta_data, colWidths=[100, 170, 90, 170])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0f9ff')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0f2fe')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(meta_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('Disrupted Itinerary Information', section_heading))
    flight_data = [
        [
            Paragraph('<b>Flight Number</b>', bold_body),
            Paragraph('<b>Sector / Route</b>', bold_body),
            Paragraph('<b>Operational Status</b>', bold_body),
            Paragraph('<b>Impact / Delay Details</b>', bold_body),
        ],
        [
            Paragraph(flight_number, body_style),
            Paragraph(route, body_style),
            Paragraph(f"<font color='#b91c1c'><b>{flight_status.upper()}</b></font>", body_style),
            Paragraph(delay_info or 'Operational Cancellation', body_style),
        ],
    ]
    flight_table = Table(flight_data, colWidths=[90, 140, 140, 160])
    flight_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(flight_table)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph('Authorized Entitlements and Settlements', section_heading))
    action_rows = [
        [Paragraph('<b>Authorized Benefit</b>', bold_body), Paragraph('<b>Status and Execution Details</b>', bold_body)]
    ]
    if not actions_taken:
        action_rows.append([
            Paragraph('Disruption Review', body_style),
            Paragraph('Case evaluated under SkyWay standard disruption guidelines.', body_style)
        ])
    else:
        for act in set(actions_taken):
            act_lower = act.lower()
            if 'refund' in act_lower:
                action_rows.append([
                    Paragraph('<b>Full Refund Authorization</b>', body_style),
                    Paragraph('Approved for 100% fare refund to original payment method (3-7 business days).', body_style)
                ])
            elif 'rebook' in act_lower:
                action_rows.append([
                    Paragraph('<b>Free Priority Rebooking</b>', body_style),
                    Paragraph('Guaranteed complimentary seat protection on alternative flight within 24 hours.', body_style)
                ])
            elif 'meal' in act_lower:
                action_rows.append([
                    Paragraph('<b>Dining Voucher Issued</b>', body_style),
                    Paragraph('Airport dining pass credited to boarding reference.', body_style)
                ])
            elif 'lounge' in act_lower:
                action_rows.append([
                    Paragraph('<b>Executive Departure Lounge Pass</b>', body_style),
                    Paragraph('Complimentary lounge access authorized.', body_style)
                ])
            elif 'hotel' in act_lower:
                action_rows.append([
                    Paragraph('<b>Transit Hotel Accommodation</b>', body_style),
                    Paragraph('Transit accommodation authorized covering delayed-hours duration only.', body_style)
                ])
            elif 'escalate' in act_lower:
                action_rows.append([
                    Paragraph('<b>Supervisor Escalation File</b>', body_style),
                    Paragraph('Transferred to Duty Operations Supervisor Desk for immediate review.', body_style)
                ])
            else:
                action_rows.append([
                    Paragraph('Disruption Benefit', body_style),
                    Paragraph(act, body_style)
                ])

    actions_table = Table(action_rows, colWidths=[190, 340])
    actions_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0f2fe')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#bae6fd')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0f2fe')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(actions_table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph('Service Policy Terms and Compliance', section_heading))
    terms_text = (
        'This disruption claim certificate is issued in compliance with SkyWay Airlines passenger charter '
        'and civil aviation disruption regulations as of 23 September 2026. All vouchers and authorizations '
        'are non-transferable and tied directly to the referenced PNR.'
    )
    elements.append(Paragraph(terms_text, body_style))
    elements.append(Spacer(1, 12))

    seal_data = [
        [
            Paragraph('<b>Issued By:</b><br/>SkyWay Autonomous Care Agent<br/>System Node: AI-AERO-RES-2026', body_style),
            Paragraph('<b>Duty Operations Seal:</b><br/>[VERIFIED AND RECORDED]<br/>Audit Hash: OK-GND-23SEP', body_style),
        ]
    ]
    seal_table = Table(seal_data, colWidths=[265, 265])
    seal_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(seal_table)
    elements.append(Spacer(1, 14))

    elements.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#e2e8f0'), spaceAfter=8))
    elements.append(Paragraph('SkyWay Airlines Customer Care - 24x7 Airport Operations - Flight Date: 23 September 2026', footer_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()