from neo4j import GraphDatabase
from app.core.config import get_settings

class Neo4jService:
    def __init__(self):
        self.settings = get_settings()
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(
                self.settings.NEO4J_URI,
                auth=(self.settings.NEO4J_USER, self.settings.NEO4J_PASSWORD)
            )
        except Exception as e:
            print(f"Failed to connect to Neo4j: {e}")

    def close(self):
        if self.driver:
            self.driver.close()

    def add_case_to_graph(self, case_data: dict):
        if not self.driver:
            return None
            
        hash_id = case_data["ingestion"]["hash_sha256"]
        subject = case_data["metadata"]["subject"]
        origin_ip = case_data["forensics"]["origin_ip"]
        
        # Safe extraction from AI analysis
        ai_analysis = case_data.get("ai_analysis", {}) or {}
        fraud_taxonomy = ai_analysis.get("fraud_taxonomy", "unknown")
        bec_subtype = ai_analysis.get("bec_subtype", "none")
        threat_actor_claimed = ai_analysis.get("threat_actor_claimed")
        
        # Extract sender domain
        from_header = case_data["metadata"]["from"]
        sender_domain = ""
        if from_header and "@" in from_header:
            sender_domain = from_header.split("@")[-1].strip(">")
            
        # Extract typosquat info if any
        is_lookalike = False
        typosquat = case_data["forensics"].get("typosquat", {})
        if typosquat and (typosquat.get("lookalike") or typosquat.get("impersonation")):
            is_lookalike = True

        geo_info = case_data["forensics"].get("geo_info", {})
        asn = geo_info.get("asn", "Unknown")
        country = geo_info.get("country", "Unknown")
        
        threat_intel = case_data["forensics"].get("threat_intel", {})
        is_tor = threat_intel.get("is_tor", False)

        with self.driver.session() as session:
            session.execute_write(
                self._create_nodes_and_edges, 
                hash_id, subject, fraud_taxonomy, bec_subtype,
                origin_ip, asn, country, is_tor,
                sender_domain, is_lookalike,
                threat_actor_claimed
            )
            
            # Check for repeat campaigns
            return session.execute_read(self._check_repeat_campaign, hash_id)

    @staticmethod
    def _create_nodes_and_edges(tx, hash_id, subject, fraud_taxonomy, bec_subtype,
                                origin_ip, asn, country, is_tor,
                                sender_domain, is_lookalike, threat_actor_claimed):
        # 1. Email Node
        tx.run(
            """
            MERGE (e:Email {hash: $hash_id})
            SET e.subject = $subject,
                e.fraud_taxonomy = $fraud_taxonomy,
                e.bec_subtype = $bec_subtype
            """,
            hash_id=hash_id, subject=subject, fraud_taxonomy=fraud_taxonomy, bec_subtype=bec_subtype
        )
        
        # 2. IP Node and Edge
        if origin_ip:
            tx.run(
                """
                MERGE (ip:IPAddress {address: $origin_ip})
                SET ip.asn = $asn,
                    ip.country = $country,
                    ip.is_tor = $is_tor
                WITH ip
                MATCH (e:Email {hash: $hash_id})
                MERGE (e)-[:ORIGINATED_FROM]->(ip)
                """,
                origin_ip=origin_ip, asn=asn, country=country, is_tor=is_tor, hash_id=hash_id
            )
            
        # 3. Domain Node and Edge
        if sender_domain:
            tx.run(
                """
                MERGE (d:Domain {name: $sender_domain})
                SET d.is_lookalike = $is_lookalike
                WITH d
                MATCH (e:Email {hash: $hash_id})
                MERGE (e)-[:CLAIMED_SENDER]->(d)
                """,
                sender_domain=sender_domain, is_lookalike=is_lookalike, hash_id=hash_id
            )
            
        # 4. Threat Actor Node and Edge
        if threat_actor_claimed:
            tx.run(
                """
                MERGE (t:ThreatActor {impersonated_entity: $threat_actor_claimed})
                WITH t
                MATCH (e:Email {hash: $hash_id})
                MERGE (e)-[:ATTRIBUTED_TO]->(t)
                """,
                threat_actor_claimed=threat_actor_claimed, hash_id=hash_id
            )

    @staticmethod
    def _check_repeat_campaign(tx, current_hash):
        query = """
        MATCH (new_email:Email {hash: $current_hash})-[:ORIGINATED_FROM]->(ip:IPAddress)
        MATCH (past_email:Email)-[:ORIGINATED_FROM]->(ip)
        WHERE past_email.hash <> new_email.hash
          AND past_email.fraud_taxonomy IN ['phishing', 'fraud-related']
        RETURN count(past_email) AS previous_malicious_campaigns, ip.address
        """
        result = tx.run(query, current_hash=current_hash)
        record = result.single()
        if record:
            return {
                "previous_malicious_campaigns": record["previous_malicious_campaigns"],
                "ip": record["ip.address"]
            }
        return {"previous_malicious_campaigns": 0, "ip": None}

neo4j_service = Neo4jService()
