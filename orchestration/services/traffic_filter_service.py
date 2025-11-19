# orchestration/services/traffic_filter_service.py

import ipaddress
from typing import Optional, Dict, List
from dataclasses import dataclass

@dataclass
class ExclusionResult:
    should_exclude: bool
    reason: Optional[str] = None

class TrafficFilterService:
    """
    Servicio para filtrar tráfico interno
    """
    
    def __init__(self, db):
        self.db = db
    
    async def should_exclude_traffic(
        self,
        user_id: str,  # Owner del experimento
        visitor_ip: str,
        headers: Dict[str, str],
        user_identifier: str,
        session_id: str
    ) -> ExclusionResult:
        """
        Verifica si el tráfico debe ser excluido
        
        Returns:
            ExclusionResult con should_exclude=True y razón si debe excluirse
        """
        
        # Obtener reglas del usuario
        rules = await self.get_exclusion_rules(user_id)
        
        # Check 1: IP
        for rule in rules:
            if rule['rule_type'] == 'ip' and rule['enabled']:
                if self._ip_matches(visitor_ip, rule['rule_value']):
                    return ExclusionResult(
                        should_exclude=True,
                        reason=f"IP matched: {rule['rule_value']}"
                    )
        
        # Check 2: Cookie/Header (tracker manda X-Samplit-Internal)
        if headers.get('X-Samplit-Internal') == 'true':
            return ExclusionResult(
                should_exclude=True,
                reason="Internal cookie/flag detected"
            )
        
        # Check 3: Email (si el user_identifier es email y está en la lista)
        for rule in rules:
            if rule['rule_type'] == 'email' and rule['enabled']:
                if user_identifier == rule['rule_value']:
                    return ExclusionResult(
                        should_exclude=True,
                        reason=f"Email matched: {rule['rule_value']}"
                    )
        
        # Check 4: User Agent (bots, crawlers)
        user_agent = headers.get('User-Agent', '').lower()
        if self._is_bot(user_agent):
            return ExclusionResult(
                should_exclude=True,
                reason=f"Bot detected: {user_agent[:50]}"
            )
        
        # No excluir
        return ExclusionResult(should_exclude=False)
    
    def _ip_matches(self, visitor_ip: str, rule_value: str) -> bool:
        """
        Verifica si IP coincide con regla
        
        Soporta:
        - IP exacta: "192.168.1.1"
        - CIDR: "192.168.1.0/24"
        - Rango: "192.168.1.1-192.168.1.50"
        """
        try:
            visitor = ipaddress.ip_address(visitor_ip)
            
            # CIDR notation
            if '/' in rule_value:
                network = ipaddress.ip_network(rule_value, strict=False)
                return visitor in network
            
            # Rango
            elif '-' in rule_value:
                start, end = rule_value.split('-')
                start_ip = ipaddress.ip_address(start.strip())
                end_ip = ipaddress.ip_address(end.strip())
                return start_ip <= visitor <= end_ip
            
            # IP exacta
            else:
                rule_ip = ipaddress.ip_address(rule_value)
                return visitor == rule_ip
        
        except ValueError:
            return False
    
    def _is_bot(self, user_agent: str) -> bool:
        """Detectar bots comunes"""
        bot_signatures = [
            'bot', 'crawler', 'spider', 'scraper', 
            'googlebot', 'bingbot', 'facebookexternalhit',
            'slackbot', 'telegrambot', 'whatsapp',
            'curl', 'wget', 'python-requests'
        ]
        return any(sig in user_agent for sig in bot_signatures)
    
    async def get_exclusion_rules(self, user_id: str) -> List[Dict]:
        """Obtener reglas de exclusión del usuario"""
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT rule_type, rule_value, enabled, description
                FROM traffic_exclusion_rules
                WHERE user_id = $1 AND enabled = true
                ORDER BY created_at DESC
                """,
                user_id
            )
        return [dict(row) for row in rows]
    
    async def log_excluded_session(
        self,
        experiment_id: str,
        user_identifier: str,
        session_id: str,
        reason: str
    ):
        """Registrar sesión excluida para debugging"""
        async with self.db.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO excluded_sessions 
                (experiment_id, user_identifier, session_id, exclusion_reason)
                VALUES ($1, $2, $3, $4)
                """,
                experiment_id, user_identifier, session_id, reason
            )
