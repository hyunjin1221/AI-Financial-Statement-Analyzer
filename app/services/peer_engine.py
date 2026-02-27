from concurrent.futures import ThreadPoolExecutor, as_completed
from statistics import median
from typing import Dict, List, Optional

from app.config import settings
from app.models.schemas import CompanyIdentity
from app.services.ratio_engine import compute_ratios
from app.services.xbrl_mapper import extract_latest_financials


RATIO_KEYS = [
    "current_ratio",
    "debt_to_equity",
    "net_margin",
    "roa",
    "roe",
    "operating_margin",
    "interest_coverage",
]


def aggregate_peer_ratio_medians(peer_ratios: List[Dict[str, Dict]]) -> Dict[str, Optional[float]]:
    buckets: Dict[str, List[float]] = {k: [] for k in RATIO_KEYS}
    for ratio_map in peer_ratios:
        for key in RATIO_KEYS:
            payload = ratio_map.get(key, {})
            if payload.get("quality") != "ok":
                continue
            value = payload.get("value")
            if isinstance(value, (int, float)):
                buckets[key].append(float(value))

    result: Dict[str, Optional[float]] = {}
    for key, values in buckets.items():
        result[key] = median(values) if values else None
    return result


def compare_company_to_peer(company_ratios: Dict[str, Dict], peer_medians: Dict[str, Optional[float]]) -> Dict[str, Dict]:
    comparison: Dict[str, Dict] = {}
    for key in RATIO_KEYS:
        company_payload = company_ratios.get(key, {})
        company_value = company_payload.get("value")
        peer_value = peer_medians.get(key)

        delta = None
        if isinstance(company_value, (int, float)) and isinstance(peer_value, (int, float)):
            delta = float(company_value) - float(peer_value)

        comparison[key] = {
            "company_value": company_value,
            "company_quality": company_payload.get("quality", "missing_data"),
            "peer_median": peer_value,
            "delta_vs_peer": delta,
        }
    return comparison


class PeerBenchmarkEngine:
    def __init__(self, sec_client) -> None:
        self.sec_client = sec_client

    @staticmethod
    def _normalize_cik(cik_int: int) -> str:
        return f"{int(cik_int):010d}"

    def find_same_sic_peers(
        self,
        target_sic: str,
        target_cik_int: int,
        max_peers: int = 10,
        max_scan: int = 120,
    ) -> List[CompanyIdentity]:
        peers: List[CompanyIdentity] = []
        mapping = self.sec_client.get_ticker_mapping()
        scanned = 0

        for row in mapping:
            candidate_cik = int(row.get("cik_str", 0))
            if candidate_cik == target_cik_int:
                continue
            if scanned >= max_scan or len(peers) >= max_peers:
                break
            scanned += 1

            try:
                submissions = self.sec_client.get_submissions(self._normalize_cik(candidate_cik))
            except Exception:  # noqa: BLE001
                continue

            if str(submissions.get("sic", "")) != str(target_sic):
                continue

            peers.append(
                CompanyIdentity(
                    ticker=str(row.get("ticker", "")).upper(),
                    cik_10=self._normalize_cik(candidate_cik),
                    cik_int=candidate_cik,
                    company_name=row.get("title"),
                )
            )
        return peers

    def build_peer_benchmark(self, peers: List[CompanyIdentity]) -> Dict:
        def _peer_ratio(peer: CompanyIdentity):
            try:
                facts = self.sec_client.get_company_facts(peer.cik_10)
                financials = extract_latest_financials(facts)
                return compute_ratios(financials)
            except Exception:  # noqa: BLE001
                return None

        peer_ratio_maps: List[Dict[str, Dict]] = []
        max_workers = max(1, min(settings.peer_max_workers, len(peers) or 1))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(_peer_ratio, peer) for peer in peers]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    peer_ratio_maps.append(result)

        peer_medians = aggregate_peer_ratio_medians(peer_ratio_maps)
        return {
            "peer_count_used": len(peer_ratio_maps),
            "peer_medians": peer_medians,
        }
