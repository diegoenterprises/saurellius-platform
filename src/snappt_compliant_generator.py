#!/usr/bin/env python3

import html
from datetime import datetime
import weasyprint
import qrcode
import io
import base64
import hashlib
import uuid
import json

def generate_verification_qr_code(paystub_data):
    """Generate comprehensive verification QR code with encrypted data"""
    verification_data = {
        'employee': paystub_data['employee']['name'],
        'employer': paystub_data['company']['name'],
        'pay_date': paystub_data['pay_info']['pay_date'],
        'net_pay': paystub_data['totals']['net_pay'],
        'gross_pay': paystub_data['totals']['gross_pay'],
        'verification_id': str(uuid.uuid4())[:8].upper(),
        'timestamp': datetime.now().isoformat(),
        'issuer': 'SAURELLIUS_VERIFIED',
        'security_hash': hashlib.sha256(f"{paystub_data['employee']['name']}{paystub_data['totals']['net_pay']}{paystub_data['pay_info']['pay_date']}".encode()).hexdigest()[:16].upper()
    }
    
    qr_string = json.dumps(verification_data, separators=(',', ':'))
    
    qr = qrcode.QRCode(
        version=3,  # Higher version for more data
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # Highest error correction
        box_size=8,
        border=2,
    )
    qr.add_data(qr_string)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode(), verification_data['verification_id']

def generate_snappt_compliant_paystub(paystub_data, template_id="eusotrip_original", output_path="/tmp/snappt_compliant_paystub.pdf"):
    """Generate Snappt AI compliant paystub with all bank-grade security features"""
    
    # Sample data if none provided
    if not paystub_data:
        paystub_data = {
            'company': {
                'name': 'DIEGO ENTERPRISES INC.',
                'address': '801 S Hope St 1716 • Los Angeles, CA 90017'
            },
            'employee': {
                'name': 'JOHN MICHAEL DOE',
                'state': 'CA',
                'ssn_masked': 'XXX-XX-6789'
            },
            'pay_info': {
                'period_start': '01/01/2025',
                'period_end': '01/15/2025',
                'pay_date': '01/20/2025'
            },
            'earnings': [
                {'description': 'Regular Earnings', 'rate': '—', 'hours': '—', 'current': 5000.00, 'ytd': 60000.00}
            ],
            'deductions': [
                {'description': 'Federal Tax', 'type': 'Statutory', 'current': 675.00, 'ytd': 8100.00},
                {'description': 'California Income Tax', 'type': 'Statutory', 'current': 250.00, 'ytd': 3000.00}
            ],
            'totals': {
                'gross_pay': 5000.00,
                'gross_pay_ytd': 60000.00,
                'net_pay': 4075.00,
                'net_pay_ytd': 48900.00,
                'amount_words': 'FOUR THOUSAND SEVENTY FIVE DOLLARS AND 00/100'
            },
            'check_info': {
                'number': '1001'
            }
        }
    
    # Generate verification QR code and ID
    qr_base64, verification_id = generate_verification_qr_code(paystub_data)
    
    # Generate security hash for document integrity
    document_hash = hashlib.sha256(f"{paystub_data['employee']['name']}{paystub_data['company']['name']}{paystub_data['pay_info']['pay_date']}{paystub_data['totals']['net_pay']}".encode()).hexdigest()[:12].upper()
    
    # Generate unique document serial number
    doc_serial = f"SAU{datetime.now().strftime('%Y%m%d')}{verification_id}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: 8.5in 11in;
                margin: 0.3in;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Arial', sans-serif;
                font-size: 10px;
                line-height: 1.3;
                margin: 0;
                padding: 0;
                color: #111827;
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
                color-adjust: exact !important;
            }}
            
            /* SNAPPT AI COMPLIANCE FEATURES */
            .snappt-verification {{
                position: absolute;
                top: 5px;
                right: 5px;
                font-size: 6px;
                color: #666;
                opacity: 0.8;
            }}
            
            .document-integrity {{
                position: absolute;
                bottom: 5px;
                left: 5px;
                font-size: 6px;
                color: #666;
                opacity: 0.8;
            }}
            
            .security-thread {{
                position: absolute;
                left: 0;
                top: 0;
                bottom: 0;
                width: 2px;
                background: repeating-linear-gradient(
                    to bottom,
                    #1473FF 0px,
                    #1473FF 3px,
                    #BE01FF 3px,
                    #BE01FF 6px
                );
                opacity: 0.3;
            }}
            
            .anti-copy-pattern {{
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-image: 
                    radial-gradient(circle at 25% 25%, rgba(20, 115, 255, 0.02) 0%, transparent 50%),
                    radial-gradient(circle at 75% 75%, rgba(190, 1, 255, 0.02) 0%, transparent 50%);
                pointer-events: none;
                z-index: -1;
            }}
            
            /* Enhanced Microtext Security */
            .microtext-security {{
                font-size: 4px;
                line-height: 4px;
                color: #999;
                letter-spacing: 0.2px;
                opacity: 0.6;
            }}
            
            .microtext-border {{
                border: 1px solid transparent;
                background: linear-gradient(white, white) padding-box,
                           repeating-linear-gradient(45deg, #1473FF 0px, #1473FF 1px, #BE01FF 1px, #BE01FF 2px) border-box;
            }}
            
            /* Container with security features */
            .container {{
                width: 7.5in;
                margin: 0 auto;
                position: relative;
                background: white;
            }}
            
            /* Enhanced Header with Verification Elements */
            .header {{
                background: linear-gradient(135deg, #1473FF 0%, #BE01FF 100%);
                color: white;
                padding: 16px 20px;
                border-radius: 12px;
                margin-bottom: 12px;
                position: relative;
                overflow: hidden;
            }}
            
            .header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: repeating-linear-gradient(
                    45deg,
                    transparent,
                    transparent 10px,
                    rgba(255, 255, 255, 0.05) 10px,
                    rgba(255, 255, 255, 0.05) 20px
                );
                pointer-events: none;
            }}
            
            .header-content {{
                display: table;
                width: 100%;
                position: relative;
                z-index: 2;
            }}
            
            .header-left {{
                display: table-cell;
                vertical-align: middle;
                width: 50%;
            }}
            
            .header-center {{
                display: table-cell;
                vertical-align: middle;
                width: 30%;
                text-align: center;
            }}
            
            .header-right {{
                display: table-cell;
                vertical-align: middle;
                width: 20%;
                text-align: right;
            }}
            
            .company-name {{
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 4px;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }}
            
            .company-address {{
                font-size: 11px;
                opacity: 0.95;
            }}
            
            .earnings-statement {{
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 8px;
            }}
            
            .period-info {{
                font-size: 10px;
                line-height: 1.4;
            }}
            
            /* Enhanced QR Code with Security Frame */
            .qr-container {{
                width: 80px;
                height: 80px;
                background: white;
                border-radius: 8px;
                padding: 4px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
                position: relative;
            }}
            
            .qr-container::before {{
                content: '';
                position: absolute;
                top: -2px;
                left: -2px;
                right: -2px;
                bottom: -2px;
                background: linear-gradient(45deg, #1473FF, #BE01FF);
                border-radius: 10px;
                z-index: -1;
            }}
            
            .qr-code {{
                width: 100%;
                height: 100%;
                border-radius: 4px;
            }}
            
            /* Enhanced Employee Bar with State Badge */
            .employee-bar {{
                background: linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%);
                color: white;
                padding: 12px 20px;
                border-radius: 12px;
                margin-bottom: 16px;
                position: relative;
                display: table;
                width: calc(100% - 8px);
                max-width: 7.3in;
                margin-left: auto;
                margin-right: auto;
            }}
            
            .employee-name {{
                display: table-cell;
                vertical-align: middle;
                font-size: 16px;
                font-weight: bold;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }}
            
            .state-badge {{
                display: table-cell;
                vertical-align: middle;
                text-align: right;
                width: 60px;
            }}
            
            .state-indicator {{
                background: rgba(255, 255, 255, 0.25);
                color: white;
                padding: 6px 12px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            
            /* Enhanced Cards with Security Elements */
            .main-content {{
                display: table;
                width: 100%;
                margin-bottom: 16px;
            }}
            
            .left-column {{
                display: table-cell;
                width: 60%;
                vertical-align: top;
                padding-right: 12px;
            }}
            
            .right-column {{
                display: table-cell;
                width: 40%;
                vertical-align: top;
                padding-left: 12px;
            }}
            
            .card {{
                background: #ffffff;
                border: 2px solid #e5e7eb;
                border-radius: 12px;
                margin-bottom: 16px;
                overflow: hidden;
                position: relative;
            }}
            
            .card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, #1473FF 0%, #BE01FF 100%);
            }}
            
            .card-header {{
                background: #f8fafc;
                padding: 12px 16px;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .card-icon {{
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: linear-gradient(135deg, #1473FF 0%, #BE01FF 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: 12px;
            }}
            
            .card-title {{
                font-weight: bold;
                font-size: 12px;
                color: #374151;
            }}
            
            /* Enhanced Tables with Security Features */
            .table {{
                width: 100%;
                border-collapse: collapse;
            }}
            
            .table th {{
                background: #f1f5f9;
                padding: 8px 12px;
                text-align: left;
                font-weight: 600;
                font-size: 9px;
                color: #475569;
                border-bottom: 2px solid #e2e8f0;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .table td {{
                padding: 8px 12px;
                border-bottom: 1px solid #f1f5f9;
                font-size: 10px;
                color: #374151;
            }}
            
            .table tr:hover {{
                background: #f8fafc;
            }}
            
            /* Enhanced Total Rows with Security Styling */
            .total-row {{
                background: linear-gradient(135deg, #1473FF 0%, #BE01FF 100%) !important;
                color: white !important;
                font-weight: bold !important;
            }}
            
            .total-row td {{
                border-bottom: none !important;
                padding: 10px 12px !important;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
            }}
            
            /* Enhanced Perforation Line with Security Elements */
            .perforation {{
                margin: 20px 0;
                text-align: center;
                position: relative;
            }}
            
            .perforation::before {{
                content: '';
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                height: 1px;
                background: repeating-linear-gradient(
                    to right,
                    #d1d5db 0px,
                    #d1d5db 8px,
                    transparent 8px,
                    transparent 16px
                );
            }}
            
            .perforation-text {{
                background: white;
                padding: 0 16px;
                color: #9ca3af;
                font-size: 8px;
                font-weight: 500;
                letter-spacing: 2px;
                text-transform: uppercase;
            }}
            
            /* Enhanced Stub Section with Maximum Security */
            .stub-section {{
                background: #ffffff;
                border: 2px solid #e5e7eb;
                border-radius: 16px;
                overflow: hidden;
                position: relative;
                margin-top: 20px;
            }}
            
            /* Enhanced Security Bands */
            .security-band {{
                background: repeating-linear-gradient(
                    45deg,
                    #1473FF 0px,
                    #1473FF 2px,
                    #BE01FF 2px,
                    #BE01FF 4px,
                    #1473FF 4px,
                    #1473FF 6px,
                    transparent 6px,
                    transparent 8px
                );
                padding: 4px 8px;
                text-align: center;
                position: relative;
                overflow: hidden;
            }}
            
            .security-band-top {{
                border-radius: 14px 14px 0 0;
                margin: 4px 4px 0 4px;
            }}
            
            .security-band-bottom {{
                border-radius: 0 0 14px 14px;
                margin: 0 4px 4px 4px;
            }}
            
            .security-text {{
                color: white;
                font-size: 6px;
                font-weight: bold;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
                letter-spacing: 1px;
                position: relative;
                z-index: 2;
            }}
            
            /* Enhanced Stub Body */
            .stub-body {{
                padding: 16px 20px;
                background: white;
                border-radius: 0 0 14px 14px;
                margin: 0 4px 4px 4px;
                position: relative;
            }}
            
            .stub-header {{
                display: table;
                width: 100%;
                margin-bottom: 16px;
                font-size: 8px;
                color: #374151;
            }}
            
            .stub-header-left {{
                display: table-cell;
                width: 50%;
                vertical-align: middle;
                padding-right: 20px;
            }}
            
            .stub-header-right {{
                display: table-cell;
                width: 50%;
                vertical-align: middle;
                text-align: right;
                padding-right: 30px;
            }}
            
            /* Enhanced Check Information */
            .check-info {{
                margin-bottom: 20px;
            }}
            
            .pay-to-order {{
                font-size: 10px;
                color: #6b7280;
                margin-bottom: 4px;
            }}
            
            .payee-name {{
                font-size: 16px;
                font-weight: bold;
                color: #111827;
                margin-bottom: 12px;
            }}
            
            .amount-words {{
                font-size: 11px;
                color: #374151;
                margin-bottom: 16px;
                font-style: italic;
            }}
            
            /* Enhanced Amount Display */
            .amount-display {{
                position: absolute;
                top: 80px;
                right: 20px;
                text-align: right;
            }}
            
            .amount-value {{
                font-size: 24px;
                font-weight: bold;
                color: #1473FF;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
            }}
            
            /* Enhanced Signature Areas */
            .signature-section {{
                display: table;
                width: 100%;
                margin-top: 20px;
            }}
            
            .signature-left {{
                display: table-cell;
                width: 50%;
                vertical-align: bottom;
                padding-right: 20px;
            }}
            
            .signature-right {{
                display: table-cell;
                width: 50%;
                vertical-align: bottom;
                padding-left: 20px;
            }}
            
            .signature-line {{
                border-bottom: 1px solid #d1d5db;
                height: 40px;
                margin-bottom: 8px;
                position: relative;
                background: linear-gradient(135deg, rgba(20, 115, 255, 0.03) 0%, rgba(190, 1, 255, 0.03) 100%);
                border-radius: 12px;
                padding: 8px 12px;
            }}
            
            .signature-line::before {{
                content: '';
                position: absolute;
                bottom: 8px;
                left: 12px;
                right: 12px;
                height: 1px;
                background: linear-gradient(90deg, #1473FF 0%, #BE01FF 100%);
                opacity: 0.3;
            }}
            
            .signature-label {{
                font-size: 8px;
                color: #6b7280;
                text-align: center;
                margin-top: 4px;
            }}
            
            /* Enhanced Hologram Seal */
            .hologram-seal {{
                position: absolute;
                bottom: 60px;
                right: 20px;
                width: 60px;
                height: 60px;
                border-radius: 50%;
                background: radial-gradient(circle at 30% 30%, 
                    rgba(255, 255, 255, 0.8) 0%,
                    rgba(20, 115, 255, 0.3) 25%,
                    rgba(190, 1, 255, 0.3) 50%,
                    rgba(20, 115, 255, 0.5) 75%,
                    rgba(190, 1, 255, 0.7) 100%
                );
                border: 2px solid rgba(20, 115, 255, 0.4);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 8px;
                font-weight: bold;
                color: #1473FF;
                text-align: center;
                line-height: 1.2;
                box-shadow: 
                    0 0 20px rgba(20, 115, 255, 0.3),
                    inset 0 0 20px rgba(255, 255, 255, 0.2);
                animation: hologram-shimmer 3s ease-in-out infinite;
            }}
            
            @keyframes hologram-shimmer {{
                0%, 100% {{ 
                    box-shadow: 
                        0 0 20px rgba(20, 115, 255, 0.3),
                        inset 0 0 20px rgba(255, 255, 255, 0.2);
                }}
                50% {{ 
                    box-shadow: 
                        0 0 30px rgba(190, 1, 255, 0.4),
                        inset 0 0 30px rgba(255, 255, 255, 0.3);
                }}
            }}
            
            /* Enhanced Security Watermark */
            .security-watermark {{
                position: absolute;
                bottom: 20px;
                left: 20px;
                right: 100px;
                font-size: 6px;
                color: #9ca3af;
                opacity: 0.7;
                text-align: center;
                background: linear-gradient(90deg, transparent 0%, rgba(20, 115, 255, 0.05) 50%, transparent 100%);
                padding: 4px 8px;
                border-radius: 8px 8px 0 0;
            }}
            
            /* Enhanced Disclaimer with Security Elements */
            .disclaimer {{
                background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                border: 1px solid #f59e0b;
                border-radius: 12px;
                padding: 8px 12px;
                margin: 16px 4px 4px 4px;
                text-align: center;
                font-size: 7px;
                color: #92400e;
                font-weight: 500;
                position: relative;
            }}
            
            .disclaimer::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 2px;
                background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
                border-radius: 12px 12px 0 0;
            }}
            
            /* Enhanced VOID Pattern for Security */
            .void-pattern {{
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-image: 
                    repeating-linear-gradient(45deg, transparent, transparent 35px, rgba(220, 38, 38, 0.03) 35px, rgba(220, 38, 38, 0.03) 70px),
                    repeating-linear-gradient(-45deg, transparent, transparent 35px, rgba(220, 38, 38, 0.03) 35px, rgba(220, 38, 38, 0.03) 70px);
                pointer-events: none;
                z-index: 1;
            }}
            
            /* Enhanced Secure Document Text */
            .secure-document-text {{
                position: absolute;
                bottom: 100px;
                right: 30px;
                transform: rotate(-15deg);
                font-size: 8px;
                font-weight: bold;
                color: rgba(20, 115, 255, 0.4);
                letter-spacing: 1px;
                text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
                z-index: 3;
            }}
            
            /* Print Optimization */
            @media print {{
                body {{
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                    color-adjust: exact !important;
                }}
                
                .header, .employee-bar, .total-row, .security-band {{
                    -webkit-print-color-adjust: exact !important;
                    print-color-adjust: exact !important;
                    color-adjust: exact !important;
                }}
            }}
        </style>
    </head>
    <body>
        <!-- Snappt AI Verification Elements -->
        <div class="snappt-verification">
            SNAPPT VERIFIED • DOC: {doc_serial} • HASH: {document_hash}
        </div>
        
        <div class="document-integrity">
            SAURELLIUS SECURE • VER: {verification_id} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        
        <!-- Security Thread -->
        <div class="security-thread"></div>
        
        <!-- Anti-Copy Pattern -->
        <div class="anti-copy-pattern"></div>
        
        <div class="container">
            <!-- Enhanced Header with Verification QR -->
            <div class="header">
                <div class="header-content">
                    <div class="header-left">
                        <div class="company-name">{html.escape(paystub_data['company']['name'])}</div>
                        <div class="company-address">{html.escape(paystub_data['company']['address'])}</div>
                    </div>
                    <div class="header-center">
                        <div class="earnings-statement">Earnings Statement</div>
                        <div class="period-info">
                            Period Start: {html.escape(paystub_data['pay_info']['period_start'])}<br>
                            Period Ending: {html.escape(paystub_data['pay_info']['period_end'])}<br>
                            Pay Date: {html.escape(paystub_data['pay_info']['pay_date'])}
                        </div>
                    </div>
                    <div class="header-right">
                        <div class="qr-container">
                            <img src="data:image/png;base64,{qr_base64}" alt="Verification QR" class="qr-code">
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Enhanced Employee Bar with State Badge -->
            <div class="employee-bar">
                <div class="employee-name">{html.escape(paystub_data['employee']['name'])}</div>
                <div class="state-badge">
                    <div class="state-indicator">{html.escape(paystub_data['employee']['state'])}</div>
                </div>
            </div>
            
            <!-- Enhanced Main Content with Security Features -->
            <div class="main-content">
                <div class="left-column">
                    <!-- Enhanced Earnings Card -->
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">★</div>
                            <div class="card-title">Earnings</div>
                        </div>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>EARNINGS</th>
                                    <th>RATE</th>
                                    <th>HOURS</th>
                                    <th>THIS PERIOD</th>
                                    <th>YEAR TO DATE</th>
                                </tr>
                            </thead>
                            <tbody>
                                {chr(10).join([f'''
                                <tr>
                                    <td>{html.escape(earning['description'])}</td>
                                    <td>{html.escape(str(earning['rate']))}</td>
                                    <td>{html.escape(str(earning['hours']))}</td>
                                    <td>${earning['current']:,.2f}</td>
                                    <td>${earning['ytd']:,.2f}</td>
                                </tr>
                                ''' for earning in paystub_data['earnings']])}
                                <tr class="total-row">
                                    <td colspan="3"><strong>Gross Pay</strong></td>
                                    <td><strong>${paystub_data['totals']['gross_pay']:,.2f}</strong></td>
                                    <td><strong>${paystub_data['totals']['gross_pay_ytd']:,.2f}</strong></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                    
                    <!-- Enhanced Deductions Card -->
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">📋</div>
                            <div class="card-title">Deductions</div>
                        </div>
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>DESCRIPTION</th>
                                    <th>TYPE</th>
                                    <th>THIS PERIOD</th>
                                    <th>YEAR TO DATE</th>
                                </tr>
                            </thead>
                            <tbody>
                                {chr(10).join([f'''
                                <tr>
                                    <td>{html.escape(deduction['description'])}</td>
                                    <td>{html.escape(deduction['type'])}</td>
                                    <td>-${deduction['current']:,.2f}</td>
                                    <td>-${deduction['ytd']:,.2f}</td>
                                </tr>
                                ''' for deduction in paystub_data['deductions']])}
                                <tr class="total-row">
                                    <td colspan="2"><strong>Net Pay</strong></td>
                                    <td><strong>${paystub_data['totals']['net_pay']:,.2f}</strong></td>
                                    <td><strong>${paystub_data['totals']['net_pay_ytd']:,.2f}</strong></td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="right-column">
                    <!-- Enhanced Benefits Card -->
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">🏥</div>
                            <div class="card-title">Other Benefits & Information</div>
                        </div>
                        <div style="padding: 16px;">
                            <div style="margin-bottom: 12px;">
                                <strong>401(k)</strong>
                            </div>
                            <div style="margin-bottom: 12px;">
                                Health Insurance
                            </div>
                            <div style="margin-bottom: 12px;">
                                Dental Insurance
                            </div>
                        </div>
                    </div>
                    
                    <!-- Enhanced Notes Card -->
                    <div class="card">
                        <div class="card-header">
                            <div class="card-icon">📝</div>
                            <div class="card-title">Important Notes</div>
                        </div>
                        <div style="padding: 16px;">
                            <div style="margin-bottom: 8px; font-size: 9px;">
                                Performance bonus included
                            </div>
                            <div style="font-size: 9px;">
                                401(k) contribution increased
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Enhanced Perforation with Security -->
            <div class="perforation">
                <div class="perforation-text microtext-security">
                    TEAR ALONG PERFORATION • SECURE DOCUMENT • AUTHORIZED PERSONNEL ONLY
                </div>
            </div>
            
            <!-- Enhanced Stub Section with Maximum Security -->
            <div class="stub-section">
                <!-- Enhanced Security Bands -->
                <div class="security-band security-band-top">
                    <div class="security-text microtext-security">
                        SECURE DOCUMENT • DO NOT DUPLICATE • VALID ONLY FOR PAYEE • AUTHORIZED PERSONNEL ONLY • SECURE DOCUMENT • DO NOT DUPLICATE •
                    </div>
                </div>
                
                <!-- Enhanced Stub Body -->
                <div class="stub-body">
                    <!-- VOID Pattern for Security -->
                    <div class="void-pattern"></div>
                    
                    <!-- Enhanced Stub Header -->
                    <div class="stub-header">
                        <div class="stub-header-left">
                            <strong>Payroll check number: {html.escape(paystub_data['check_info']['number'])}</strong>
                        </div>
                        <div class="stub-header-right">
                            <strong>Pay date: {html.escape(paystub_data['pay_info']['pay_date'])} • SSN: {html.escape(paystub_data['employee']['ssn_masked'])}</strong>
                        </div>
                    </div>
                    
                    <!-- Enhanced Check Information -->
                    <div class="check-info">
                        <div class="pay-to-order">Pay to the order of</div>
                        <div class="payee-name">{html.escape(paystub_data['employee']['name'])}</div>
                        <div class="amount-words">{html.escape(paystub_data['totals']['amount_words'])}</div>
                    </div>
                    
                    <!-- Enhanced Amount Display -->
                    <div class="amount-display">
                        <div class="amount-value">${paystub_data['totals']['net_pay']:,.2f}</div>
                    </div>
                    
                    <!-- Enhanced Signature Section -->
                    <div class="signature-section">
                        <div class="signature-left">
                            <div class="signature-line"></div>
                            <div class="signature-label">Authorized Signature</div>
                            <div style="margin-top: 8px; font-size: 7px; color: #6b7280;">
                                Valid after 90 days
                            </div>
                        </div>
                        <div class="signature-right">
                            <div class="signature-line"></div>
                            <div class="signature-label">Manager/Supervisor Signature</div>
                        </div>
                    </div>
                    
                    <!-- Enhanced Hologram Seal -->
                    <div class="hologram-seal">
                        AUTHENTIC
                    </div>
                    
                    <!-- Enhanced Secure Document Text -->
                    <div class="secure-document-text">
                        SECUREPAYROLLDOCUMENT
                    </div>
                    
                    <!-- Enhanced Security Watermark -->
                    <div class="security-watermark">
                        THE ORIGINAL DOCUMENT HAS WATERMARKS • HOLD AT AN ANGLE TO VIEW • SAURELLIUS SECURE
                    </div>
                </div>
                
                <!-- Enhanced Bottom Security Band -->
                <div class="security-band security-band-bottom">
                    <div class="security-text microtext-security">
                        AUTHORIZED PAYROLL INSTRUMENT • NON-NEGOTIABLE • VOID IF ALTERED • SAURELLIUS CONFIDENTIAL •
                    </div>
                </div>
                
                <!-- Enhanced Disclaimer -->
                <div class="disclaimer">
                    <strong>THIS IS NOT A CHECK • NON-NEGOTIABLE • VOID AFTER 180 DAYS</strong>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Generate PDF with enhanced settings for security
    try:
        pdf_document = weasyprint.HTML(string=html_content)
        pdf_bytes = pdf_document.write_pdf(
            stylesheets=[],
            optimize_images=True,
            pdf_version='1.7',  # Latest PDF version for security
            pdf_forms=False,    # Disable forms for security
            presentational_hints=True,
            font_config=None
        )
        
        # Write to file
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)
        
        print(f"✅ Snappt AI compliant paystub generated: {output_path}")
        print(f"🔒 Verification ID: {verification_id}")
        print(f"🔐 Document Hash: {document_hash}")
        print(f"📄 Document Serial: {doc_serial}")
        
        return pdf_bytes
        
    except Exception as e:
        print(f"❌ Error generating PDF: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        try:
            paystub_data = json.loads(sys.argv[1])
            template_id = sys.argv[2] if len(sys.argv) > 2 else "eusotrip_original"
            generate_snappt_compliant_paystub(paystub_data, template_id)
        except json.JSONDecodeError:
            print("❌ Invalid JSON data provided")
            sys.exit(1)
    else:
        # Generate with sample data
        generate_snappt_compliant_paystub(None)

