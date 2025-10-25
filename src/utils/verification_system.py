"""
Verification System - QR Codes, Document Hashing, Verification IDs
Implements security features for paystub verification
"""
import hashlib
import uuid
import qrcode
from io import BytesIO
import base64
from datetime import datetime

class VerificationSystem:
    """
    Handle paystub verification, QR codes, and document integrity
    """
    
    BASE_VERIFICATION_URL = "https://verify.saurellius.com/paystub/"
    
    @staticmethod
    def generate_verification_id():
        """
        Generate unique verification ID for paystub
        Format: SAUR-YYYY-XXXXXXXX
        """
        year = datetime.now().year
        unique_id = str(uuid.uuid4()).replace('-', '').upper()[:8]
        return f"SAUR-{year}-{unique_id}"
    
    @staticmethod
    def calculate_document_hash(pdf_content):
        """
        Calculate SHA-256 hash of PDF document
        Used for tamper detection
        """
        if isinstance(pdf_content, str):
            pdf_content = pdf_content.encode('utf-8')
        
        sha256_hash = hashlib.sha256(pdf_content).hexdigest()
        return sha256_hash
    
    @staticmethod
    def generate_qr_code(verification_id, paystub_data):
        """
        Generate QR code for paystub verification
        QR code contains verification URL and basic paystub info
        """
        # Create verification URL
        verification_url = f"{VerificationSystem.BASE_VERIFICATION_URL}{verification_id}"
        
        # Create QR code data (JSON-like string)
        qr_data = {
            'url': verification_url,
            'id': verification_id,
            'employee_name': paystub_data.get('employee_name', ''),
            'pay_date': paystub_data.get('pay_date', ''),
            'gross_pay': paystub_data.get('gross_pay', ''),
            'net_pay': paystub_data.get('net_pay', ''),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Convert to string
        import json
        qr_string = json.dumps(qr_data)
        
        # Generate QR code image
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for embedding
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        return {
            'qr_code_data': qr_string,
            'qr_code_image_base64': img_base64,
            'verification_url': verification_url
        }
    
    @staticmethod
    def create_verification_package(paystub, pdf_content):
        """
        Create complete verification package for a paystub
        Returns all verification data needed
        """
        # Generate verification ID
        verification_id = VerificationSystem.generate_verification_id()
        
        # Calculate document hash
        document_hash = VerificationSystem.calculate_document_hash(pdf_content)
        
        # Prepare paystub data for QR code
        paystub_data = {
            'employee_name': f"{paystub.employee.first_name} {paystub.employee.last_name}",
            'pay_date': paystub.pay_date.isoformat(),
            'gross_pay': str(paystub.gross_pay),
            'net_pay': str(paystub.net_pay),
            'paystub_number': paystub.paystub_number
        }
        
        # Generate QR code
        qr_data = VerificationSystem.generate_qr_code(verification_id, paystub_data)
        
        return {
            'verification_id': verification_id,
            'document_hash': document_hash,
            'qr_code_data': qr_data['qr_code_data'],
            'qr_code_image_base64': qr_data['qr_code_image_base64'],
            'verification_url': qr_data['verification_url'],
            'created_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def verify_document_integrity(pdf_content, stored_hash):
        """
        Verify document hasn't been tampered with
        """
        current_hash = VerificationSystem.calculate_document_hash(pdf_content)
        return current_hash == stored_hash
    
    @staticmethod
    def verify_paystub(verification_id):
        """
        Verify a paystub by verification ID
        This would be called by the public verification page
        """
        from src.models.paystub import Paystub
        
        paystub = Paystub.query.filter_by(verification_id=verification_id).first()
        
        if not paystub:
            return {
                'valid': False,
                'error': 'Paystub not found'
            }
        
        if paystub.is_void:
            return {
                'valid': False,
                'error': 'This paystub has been voided',
                'void_date': paystub.void_date.isoformat() if paystub.void_date else None,
                'void_reason': paystub.void_reason
            }
        
        # Return verification data (sanitized)
        return {
            'valid': True,
            'verification_id': paystub.verification_id,
            'employee_name': f"{paystub.employee.first_name} {paystub.employee.last_name}",
            'company_name': paystub.company.name if paystub.company else 'N/A',
            'pay_date': paystub.pay_date.isoformat(),
            'gross_pay': float(paystub.gross_pay),
            'net_pay': float(paystub.net_pay),
            'paystub_number': paystub.paystub_number,
            'created_at': paystub.created_at.isoformat(),
            'document_hash': paystub.document_hash
        }
    
    @staticmethod
    def generate_verification_badge(paystub):
        """
        Generate HTML badge for verified paystub
        """
        badge_html = f"""
        <div class="verification-badge">
            <div class="badge-icon">
                <i class="fas fa-shield-check"></i>
            </div>
            <div class="badge-content">
                <div class="badge-title">Verified Paystub</div>
                <div class="badge-id">{paystub.verification_id}</div>
                <div class="badge-date">Issued: {paystub.pay_date.strftime('%B %d, %Y')}</div>
            </div>
        </div>
        """
        return badge_html
    
    @staticmethod
    def create_verification_email(paystub, recipient_email):
        """
        Create verification email content
        """
        verification_url = f"{VerificationSystem.BASE_VERIFICATION_URL}{paystub.verification_id}"
        
        email_content = {
            'subject': f'Paystub Verification - {paystub.verification_id}',
            'to': recipient_email,
            'html': f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: linear-gradient(135deg, #7C3AED 0%, #3B82F6 100%); padding: 30px; text-align: center;">
                    <h1 style="color: white; margin: 0;">Saurellius Paystub Verification</h1>
                </div>
                <div style="padding: 30px; background: #f9fafb;">
                    <p>A paystub has been generated and is ready for verification.</p>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3>Paystub Details</h3>
                        <p><strong>Verification ID:</strong> {paystub.verification_id}</p>
                        <p><strong>Employee:</strong> {paystub.employee.first_name} {paystub.employee.last_name}</p>
                        <p><strong>Pay Date:</strong> {paystub.pay_date.strftime('%B %d, %Y')}</p>
                        <p><strong>Net Pay:</strong> ${paystub.net_pay:,.2f}</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" 
                           style="background: #7C3AED; color: white; padding: 15px 30px; 
                                  text-decoration: none; border-radius: 8px; display: inline-block;">
                            Verify Paystub
                        </a>
                    </div>
                    
                    <p style="color: #6b7280; font-size: 14px;">
                        Or copy and paste this URL into your browser:<br>
                        <a href="{verification_url}">{verification_url}</a>
                    </p>
                </div>
                <div style="background: #1f2937; color: #9ca3af; padding: 20px; text-align: center; font-size: 12px;">
                    <p>This is an automated message from Saurellius Platform.</p>
                    <p>&copy; 2025 Saurellius. All rights reserved.</p>
                </div>
            </body>
            </html>
            """
        }
        
        return email_content

