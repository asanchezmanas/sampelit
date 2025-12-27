# integration/webhooks/signatures.py

"""
Módulo de firmas HMAC para webhooks.
Proporciona generación y verificación de firmas para asegurar
la autenticidad de los payloads de webhook.
"""

import hmac
import hashlib
import secrets
import time
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# Constantes
SECRET_LENGTH = 32  # bytes
SIGNATURE_ALGORITHM = "sha256"
TIMESTAMP_TOLERANCE = 300  # 5 minutos máximo de diferencia


def generate_secret() -> str:
    """
    Generar un secret aleatorio para un webhook.
    
    Returns:
        Secret en formato "whsec_" + 32 bytes hex
        
    Example:
        >>> secret = generate_secret()
        >>> secret.startswith("whsec_")
        True
        >>> len(secret)
        70  # "whsec_" (6) + 64 hex chars
    """
    random_bytes = secrets.token_hex(SECRET_LENGTH)
    return f"whsec_{random_bytes}"


def sign_payload(payload: bytes, secret: str, timestamp: Optional[int] = None) -> Tuple[str, int]:
    """
    Firmar un payload con HMAC-SHA256.
    
    La firma se genera sobre: "{timestamp}.{payload}"
    Esto previene replay attacks al vincular la firma con el momento.
    
    Args:
        payload: Bytes del payload JSON
        secret: Secret del webhook (con o sin prefijo "whsec_")
        timestamp: Unix timestamp (default: ahora)
    
    Returns:
        Tuple[signature, timestamp]
        
    Example:
        >>> payload = b'{"event": "test"}'
        >>> signature, ts = sign_payload(payload, "whsec_abc123")
        >>> signature.startswith("sha256=")
        True
    """
    # Usar timestamp actual si no se provee
    if timestamp is None:
        timestamp = int(time.time())
    
    # Limpiar prefijo del secret si existe
    clean_secret = secret.replace("whsec_", "")
    
    # Crear mensaje a firmar: timestamp.payload
    message = f"{timestamp}.{payload.decode('utf-8')}"
    
    # Generar firma HMAC-SHA256
    signature = hmac.new(
        clean_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return f"{SIGNATURE_ALGORITHM}={signature}", timestamp


def verify_signature(
    payload: bytes,
    signature: str,
    secret: str,
    timestamp: str,
    tolerance: int = TIMESTAMP_TOLERANCE
) -> bool:
    """
    Verificar la firma de un payload de webhook.
    
    Útil para que los receptores de webhooks validen la autenticidad.
    
    Args:
        payload: Bytes del payload recibido
        signature: Firma recibida en header X-Samplit-Signature
        secret: Secret del webhook
        timestamp: Timestamp recibido en header X-Samplit-Timestamp
        tolerance: Tolerancia en segundos para el timestamp
    
    Returns:
        True si la firma es válida y el timestamp está dentro de tolerancia
        
    Example:
        >>> payload = b'{"event": "test"}'
        >>> sig, ts = sign_payload(payload, "whsec_abc123")
        >>> verify_signature(payload, sig, "whsec_abc123", str(ts))
        True
    """
    try:
        # Verificar timestamp (prevenir replay attacks)
        ts = int(timestamp)
        current_time = int(time.time())
        
        if abs(current_time - ts) > tolerance:
            logger.warning(f"Webhook signature rejected: timestamp too old ({current_time - ts}s)")
            return False
        
        # Regenerar firma esperada
        expected_signature, _ = sign_payload(payload, secret, ts)
        
        # Comparación segura (timing-safe)
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if not is_valid:
            logger.warning("Webhook signature mismatch")
        
        return is_valid
        
    except (ValueError, TypeError) as e:
        logger.error(f"Webhook signature verification error: {e}")
        return False


def get_signature_headers(payload: bytes, secret: str) -> dict:
    """
    Generar todos los headers de firma para un webhook.
    
    Args:
        payload: Bytes del payload JSON
        secret: Secret del webhook
    
    Returns:
        Dict con headers listos para añadir al request
        
    Example:
        >>> headers = get_signature_headers(b'{"test": true}', "whsec_abc")
        >>> "X-Samplit-Signature" in headers
        True
    """
    signature, timestamp = sign_payload(payload, secret)
    
    return {
        "X-Samplit-Signature": signature,
        "X-Samplit-Timestamp": str(timestamp),
    }


# ═══════════════════════════════════════════════════════════════════════════
# CÓDIGO DE EJEMPLO PARA RECEPTORES
# ═══════════════════════════════════════════════════════════════════════════

VERIFICATION_EXAMPLE_PYTHON = '''
# Python example for verifying Samplit webhook signatures

import hmac
import hashlib
import time

def verify_samplit_webhook(payload: bytes, headers: dict, secret: str) -> bool:
    """
    Verify a webhook signature from Samplit.
    
    Args:
        payload: Raw request body as bytes
        headers: Request headers dict
        secret: Your webhook secret (starts with whsec_)
    
    Returns:
        True if signature is valid
    """
    signature = headers.get("X-Samplit-Signature", "")
    timestamp = headers.get("X-Samplit-Timestamp", "")
    
    # Check timestamp (reject if > 5 minutes old)
    try:
        ts = int(timestamp)
        if abs(time.time() - ts) > 300:
            return False
    except ValueError:
        return False
    
    # Generate expected signature
    clean_secret = secret.replace("whsec_", "")
    message = f"{timestamp}.{payload.decode('utf-8')}"
    expected = "sha256=" + hmac.new(
        clean_secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)


# Usage in Flask:
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    if not verify_samplit_webhook(
        request.data,
        request.headers,
        os.environ["SAMPLIT_WEBHOOK_SECRET"]
    ):
        return "Invalid signature", 401
    
    event = request.json
    # Process event...
    return "OK", 200
'''

VERIFICATION_EXAMPLE_NODE = '''
// Node.js example for verifying Samplit webhook signatures

const crypto = require('crypto');

function verifySamplitWebhook(payload, headers, secret) {
    const signature = headers['x-samplit-signature'] || '';
    const timestamp = headers['x-samplit-timestamp'] || '';
    
    // Check timestamp (reject if > 5 minutes old)
    const ts = parseInt(timestamp, 10);
    if (isNaN(ts) || Math.abs(Date.now() / 1000 - ts) > 300) {
        return false;
    }
    
    // Generate expected signature
    const cleanSecret = secret.replace('whsec_', '');
    const message = `${timestamp}.${payload}`;
    const expected = 'sha256=' + crypto
        .createHmac('sha256', cleanSecret)
        .update(message)
        .digest('hex');
    
    return crypto.timingSafeEqual(
        Buffer.from(expected),
        Buffer.from(signature)
    );
}

// Usage in Express:
app.post('/webhook', express.raw({type: 'application/json'}), (req, res) => {
    if (!verifySamplitWebhook(
        req.body.toString(),
        req.headers,
        process.env.SAMPLIT_WEBHOOK_SECRET
    )) {
        return res.status(401).send('Invalid signature');
    }
    
    const event = JSON.parse(req.body);
    // Process event...
    res.send('OK');
});
'''
