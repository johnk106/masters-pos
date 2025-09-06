import requests
import base64
import json
from datetime import datetime
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from .models import MpesaTransaction
from .ngrok_service import get_ngrok_callback_url, ensure_ngrok_tunnel
import logging
from .models import Invoice

logger = logging.getLogger(__name__)

class MpesaService:
    """
    Service class for handling M-Pesa STK Push transactions using Daraja API
    """
    
    def __init__(self):
        # M-Pesa API credentials - these should be in settings
        self.consumer_key = getattr(settings, 'MPESA_CONSUMER_KEY', '')
        self.consumer_secret = getattr(settings, 'MPESA_CONSUMER_SECRET', '')
        self.business_shortcode = getattr(settings, 'MPESA_BUSINESS_SHORTCODE', '174379')  # Sandbox default
        self.passkey = getattr(settings, 'MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')  # Sandbox default
        self.environment = getattr(settings, 'MPESA_ENVIRONMENT', 'sandbox')  # 'sandbox' or 'production'
        
        # API URLs
        if self.environment == 'production':
            self.auth_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
            self.stk_push_url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
        else:
            self.auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
            self.stk_push_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    
    def get_access_token(self):
        """
        Get access token from M-Pesa API
        Returns a tuple: (token, reason)
        reason is None on success, or 'network'/'auth'/'unknown' on failure
        """
        try:
            # Create basic auth string
            auth_string = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
            
            headers = {
                'Authorization': f'Basic {auth_string}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(self.auth_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result.get('access_token'), None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting M-Pesa access token: {str(e)}")
            return None, 'network'
        except Exception as e:
            logger.error(f"Error getting M-Pesa access token: {str(e)}")
            return None, 'unknown'
    
    def generate_password(self):
        """
        Generate password for STK Push request
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_string = f"{self.business_shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_string.encode()).decode()
        return password, timestamp
    

    
    def initiate_stk_push(self, phone_number, amount, account_reference, transaction_desc, callback_url=None):
        """
        Initiate STK Push payment
        
        Args:
            phone_number (str): Customer phone number (format: 254xxxxxxxxx)
            amount (Decimal): Amount to be paid
            account_reference (str): Account reference for the transaction
            transaction_desc (str): Transaction description
            callback_url (str): URL to receive payment notification
            
        Returns:
            dict: Response from M-Pesa API
        """
        try:
            # Ensure ngrok tunnel is running and get callback URL
            CALLBACK_PATH = "/dashboard/sales/mpesa-callback/"

            if not callback_url:
                # Use the system’s configured base URL
                base_url = getattr(settings, "BASE_URL", None)

                if not base_url:
                    return {
                        'success': False,
                        'message': 'Missing BASE_URL configuration – M-Pesa payments unavailable. Please contact support.',
                        'error_code': 'CONFIG_ERROR',
                        'reason': 'base_url_not_set'
                    }

                # Build full callback URL
                callback_url = f"{base_url.rstrip('/')}{CALLBACK_PATH}"
            
            logger.info(f"Using callback URL: {callback_url}")
            
            # Get access token
            access_token, token_reason = self.get_access_token()
            if not access_token:
                # Differentiate network vs unknown
                if token_reason == 'network':
                    return {'success': False, 'message': 'System is offline — cannot reach M-Pesa. Check internet connection.', 'error_code': 'NETWORK_OFFLINE', 'reason': 'network'}
                return {'success': False, 'message': 'Failed to get access token', 'error_code': 'AUTH_FAILED', 'reason': token_reason or 'unknown'}
            
            # Generate password and timestamp
            password, timestamp = self.generate_password()
            
            # Format phone number (ensure it starts with 254)
            if phone_number.startswith('0'):
                phone_number = '254' + phone_number[1:]
            elif phone_number.startswith('+254'):
                phone_number = phone_number[1:]
            elif not phone_number.startswith('254'):
                phone_number = '254' + phone_number
            
            # Prepare request payload
            payload = {
                "BusinessShortCode": self.business_shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": int(amount),
                "PartyA": phone_number,
                "PartyB": self.business_shortcode,
                "PhoneNumber": phone_number,
                "CallBackURL": callback_url,
                "AccountReference": account_reference,
                "TransactionDesc": transaction_desc
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Make STK Push request
            try:
                response = requests.post(self.stk_push_url, json=payload, headers=headers, timeout=15)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error during STK Push: {str(e)}")
                return {'success': False, 'message': 'System is offline — cannot reach M-Pesa. Check internet connection.', 'error_code': 'NETWORK_OFFLINE', 'reason': 'network'}
            
            result = response.json()
            
            # Create transaction record
            if result.get('ResponseCode') == '0':
                mpesa_transaction = MpesaTransaction.objects.create(
                    phone_number=phone_number,
                    amount=amount,
                    merchant_request_id=result.get('MerchantRequestID', ''),
                    checkout_request_id=result.get('CheckoutRequestID', ''),
                    status=MpesaTransaction.Status.PENDING,
                    response_code=result.get('ResponseCode'),
                    response_description=result.get('ResponseDescription'),
                    customer_message=result.get('CustomerMessage')
                )
                
                return {
                    'success': True,
                    'message': result.get('CustomerMessage', 'Payment request sent successfully'),
                    'checkout_request_id': result.get('CheckoutRequestID'),
                    'merchant_request_id': result.get('MerchantRequestID'),
                    'transaction_id': mpesa_transaction.id
                }
            else:
                return {
                    'success': False,
                    'message': result.get('ResponseDescription', 'Payment request failed'),
                    'error_code': result.get('ResponseCode'),
                    'reason': 'unknown'
                }
                
        except Exception as e:
            logger.error(f"M-Pesa STK Push error: {str(e)}")
            return {'success': False, 'message': f'Error: {str(e)}', 'reason': 'unknown'}
    
    def handle_callback(self, callback_data):
        """
        Handle M-Pesa payment callback
        
        Args:
            callback_data (dict): Callback data from M-Pesa
            
        Returns:
            bool: True if callback processed successfully
        """
        from django.db import transaction, IntegrityError
        try:
            # Log incoming payload briefly
            logger.info(f"M-Pesa callback received: keys={list(callback_data.keys())}")
            stk_callback = callback_data.get('Body', {}).get('stkCallback', {})
            
            checkout_request_id = stk_callback.get('CheckoutRequestID')
            merchant_request_id = stk_callback.get('MerchantRequestID')
            result_code = stk_callback.get('ResultCode')
            result_desc = stk_callback.get('ResultDesc')
            
            if not checkout_request_id and not merchant_request_id:
                logger.error("Callback missing transaction identifiers")
                return False
            
            # Idempotent fetch of existing transaction
            try:
                txn_qs = MpesaTransaction.objects
                if checkout_request_id:
                    txn_qs = txn_qs.filter(checkout_request_id=checkout_request_id)
                elif merchant_request_id:
                    txn_qs = txn_qs.filter(merchant_request_id=merchant_request_id)
                transaction_obj = txn_qs.select_for_update().get()
            except MpesaTransaction.DoesNotExist:
                logger.error(f"M-Pesa transaction not found for callback. checkout_request_id={checkout_request_id}, merchant_request_id={merchant_request_id}")
                return False
            
            # Early duplicate guard: if we already applied this payment to invoice, do not re-apply
            if transaction_obj.applied_to_invoice:
                logger.info(f"Duplicate callback ignored (already applied). checkout_request_id={transaction_obj.checkout_request_id}")
                # Still ensure status reflects success if payload is successful
                if result_code == 0 and transaction_obj.status != MpesaTransaction.Status.SUCCESSFUL:
                    transaction_obj.status = MpesaTransaction.Status.SUCCESSFUL
                    transaction_obj.save(update_fields=['status'])
                return True
            
            with transaction.atomic():
                # Update transaction status
                if result_code == 0:
                    transaction_obj.status = MpesaTransaction.Status.SUCCESSFUL
                else:
                    transaction_obj.status = MpesaTransaction.Status.FAILED
                    # Mark associated order as failed if M-Pesa payment fails
                    if transaction_obj.order:
                        order = transaction_obj.order
                        order.status = order.Status.FAILED
                        order.save(update_fields=['status'])
                
                # Extract fields and make timestamp aware
                callback_metadata = stk_callback.get('CallbackMetadata', {})
                items = callback_metadata.get('Item', [])
                paid_amount = None
                receipt = None
                txn_dt = None
                for item in items:
                    name = item.get('Name')
                    val = item.get('Value')
                    if name == 'MpesaReceiptNumber':
                        receipt = val
                        transaction_obj.mpesa_receipt_number = receipt
                    elif name == 'TransactionDate':
                        ts = str(val)
                        if len(ts) == 14:
                            naive = datetime.strptime(ts, '%Y%m%d%H%M%S')
                            # Make timezone aware
                            if timezone.is_naive(naive):
                                txn_dt = timezone.make_aware(naive, timezone.get_current_timezone())
                            else:
                                txn_dt = naive
                    elif name in ('Amount', 'amount'):
                        try:
                            paid_amount = Decimal(str(val))
                        except Exception:
                            paid_amount = None
                if not txn_dt:
                    txn_dt = timezone.now()
                transaction_obj.transaction_date = txn_dt
                
                # Apply payment to order and existing invoice once
                if result_code == 0 and transaction_obj.order:
                    order = transaction_obj.order
                    if paid_amount is None:
                        paid_amount = transaction_obj.amount
                    
                    # Apply to order
                    order.paid_amount = (order.paid_amount or Decimal('0.00')) + (paid_amount or Decimal('0.00'))
                    order.update_totals()  # also updates payment_status and due
                    
                    # Update existing invoice amounts (no duplicate invoice creation)
                    try:
                        from .services.order_service import InvoiceManager
                        invoice_no = f"INV-{order.reference}"
                        invoice = Invoice.objects.filter(invoice_no=invoice_no).first()
                        if not invoice:
                            # If invoice somehow missing (unexpected), create safely via get_or_create pattern
                            invoice = Invoice.objects.filter(customer=order.customer, invoice_no=invoice_no).first()
                            if not invoice:
                                # Use a savepoint to avoid breaking the outer atomic in rare race
                                try:
                                    with transaction.atomic():
                                        invoice = Invoice.objects.create(
                                            invoice_no=invoice_no,
                                            customer=order.customer,
                                            due_date=timezone.now().date(),
                                            amount=order.grand_total,
                                            amount_paid=order.paid_amount,
                                            amount_due=max(order.grand_total - order.paid_amount, Decimal('0.00')),
                                            status=Invoice.Status.PAID if order.paid_amount >= order.grand_total else Invoice.Status.OPEN
                                        )
                                except IntegrityError:
                                    # Another process created it; fetch existing
                                    invoice = Invoice.objects.filter(invoice_no=invoice_no).first()
                        if invoice:
                            # Align invoice with order and recompute using model utility
                            invoice.amount_paid = order.paid_amount
                            invoice.update_amounts()
                            logger.info(f"Applied payment to Invoice {invoice.invoice_no}: paid={invoice.amount_paid}, due={invoice.amount_due}")
                    except Exception as inv_err:
                        logger.warning(f"Invoice update warning: {inv_err}")
                    
                    transaction_obj.applied_to_invoice = True
                    transaction_obj.applied_amount = paid_amount or Decimal('0.00')
                
                transaction_obj.response_code = str(result_code)
                transaction_obj.response_description = result_desc
                save_fields = ['status', 'mpesa_receipt_number', 'transaction_date', 'response_code', 'response_description', 'applied_to_invoice', 'applied_amount']
                transaction_obj.save(update_fields=save_fields)
            
            logger.info(f"M-Pesa callback processed OK: checkout_request_id={transaction_obj.checkout_request_id}, order_id={transaction_obj.order_id}, applied={transaction_obj.applied_to_invoice}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing M-Pesa callback: {str(e)}", exc_info=True)
            return False
    
    def check_transaction_status(self, checkout_request_id):
        """
        Check the status of a transaction
        
        Args:
            checkout_request_id (str): Checkout request ID
            
        Returns:
            dict: Transaction status information
        """
        try:
            transaction = MpesaTransaction.objects.get(
                checkout_request_id=checkout_request_id
            )
            
            result = {
                'success': True,
                'status': transaction.status,
                'amount': str(transaction.amount),
                'phone_number': transaction.phone_number,
                'mpesa_receipt_number': transaction.mpesa_receipt_number,
                'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                'created_at': transaction.created_at.isoformat()
            }
            
            # Add order details if transaction is linked to an order
            if transaction.order:
                order = transaction.order
                result['order'] = {
                    'id': order.id,
                    'reference': order.reference,
                    'grand_total': str(order.grand_total),
                    'paid_amount': str(order.paid_amount),
                    'due_amount': str(order.due_amount),
                    'payment_status': order.payment_status,
                    'order_status': order.status,
                    'customer_name': order.customer.name if order.customer else 'Walk-in Customer'
                }
            
            return result
            
        except MpesaTransaction.DoesNotExist:
            return {'success': False, 'message': 'Transaction not found'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    def mark_timeout_transactions_as_failed(self, timeout_minutes=5):
        """
        Mark M-Pesa transactions as failed if they haven't received a callback 
        within the specified timeout period.
        
        Args:
            timeout_minutes (int): Minutes after which pending transactions are considered failed
        """
        from django.utils import timezone
        from datetime import timedelta
        
        timeout_threshold = timezone.now() - timedelta(minutes=timeout_minutes)
        
        # Find pending transactions older than timeout threshold
        timeout_transactions = MpesaTransaction.objects.filter(
            status=MpesaTransaction.Status.PENDING,
            created_at__lt=timeout_threshold
        )
        
        for transaction in timeout_transactions:
            transaction.status = MpesaTransaction.Status.FAILED
            transaction.response_description = f"Transaction timed out after {timeout_minutes} minutes"
            transaction.save(update_fields=['status', 'response_description'])
            
            # Mark associated order as failed if it exists
            if transaction.order and transaction.order.status not in [transaction.order.Status.FAILED, transaction.order.Status.CANCELED]:
                transaction.order.status = transaction.order.Status.FAILED
                transaction.order.save(update_fields=['status'])
                
                logger.info(f"Marked timed-out M-Pesa transaction {transaction.checkout_request_id} and order {transaction.order.reference} as failed")
        
        return timeout_transactions.count()