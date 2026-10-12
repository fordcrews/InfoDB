"""SNMP client for ARP table walks and testing."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

from pysnmp.hlapi.asyncio import (
    CommunityData,
    ContextData,
    ObjectIdentity,
    ObjectType,
    SnmpEngine,
    UdpTransportTarget,
    UsmUserData,
    getCmd,
    walkCmd,
    usmAesCfb128Protocol,
    usmDESPrivProtocol,
    usmHMACMD5AuthProtocol,
    usmHMACSHAAuthProtocol,
)

ARP_PHYS_OID = "1.3.6.1.2.1.4.22.1.2"
ARP_NET_OID = "1.3.6.1.2.1.4.22.1.3"

AUTH_PROTOCOLS = {
    "MD5": usmHMACMD5AuthProtocol,
    "SHA": usmHMACSHAAuthProtocol,
}

PRIV_PROTOCOLS = {
    "DES": usmDESPrivProtocol,
    "AES": usmAesCfb128Protocol,
}


@dataclass
class SnmpCredentials:
    version: str
    community: str | None = None
    username: str | None = None
    auth_protocol: str | None = None
    auth_password: str | None = None
    priv_protocol: str | None = None
    priv_password: str | None = None


@dataclass
class ArpEntry:
    mac_address: str
    ip_address: str


def _normalize_mac(raw: str) -> str:
    cleaned = raw.replace("0x", "").replace(":", "").replace(" ", "").strip()
    if len(cleaned) == 12:
        return ":".join(cleaned[i : i + 2] for i in range(0, 12, 2)).lower()
    return raw.lower()


def _normalize_ip(raw: str) -> str:
    return raw.strip()


def _build_user_data(creds: SnmpCredentials) -> CommunityData | UsmUserData:
    if creds.version == "v2c":
        return CommunityData(creds.community or "public", mpModel=1)

    auth_proto = AUTH_PROTOCOLS.get((creds.auth_protocol or "SHA").upper())
    priv_proto = PRIV_PROTOCOLS.get((creds.priv_protocol or "AES").upper()) if creds.priv_protocol else None

    if priv_proto and creds.priv_password:
        return UsmUserData(
            creds.username or "",
            creds.auth_password,
            creds.priv_password,
            authProtocol=auth_proto,
            privProtocol=priv_proto,
        )
    return UsmUserData(
        creds.username or "",
        creds.auth_password,
        authProtocol=auth_proto,
    )


async def _walk_column(host: str, creds: SnmpCredentials, oid: str) -> dict[str, str]:
    engine = SnmpEngine()
    user_data = _build_user_data(creds)
    transport = UdpTransportTarget((host, 161), timeout=5.0, retries=2)
    context = ContextData()

    logger.info(f"Starting SNMP walk on {host} for OID {oid}")

    results: dict[str, str] = {}
    try:
        async for (
            error_indication,
            error_status,
            _error_index,
            var_binds,
        ) in walkCmd(
            engine,
            user_data,
            transport,
            context,
            ObjectType(ObjectIdentity(oid)),
            lexicographicMode=False,
        ):
            if error_indication:
                raise RuntimeError(str(error_indication))
            if error_status:
                raise RuntimeError(str(error_status))

            for oid_val, value in var_binds:
                oid_str = str(oid_val)
                if not oid_str.startswith(oid):
                    logger.info(f"Walk for {oid} on {host} finished with {len(results)} results")
                    return results
                suffix = oid_str[len(oid) :].lstrip(".")
                results[suffix] = str(value)
    except Exception as e:
        logger.exception(f"Error during walk {oid} on {host}: {e}")
        raise

    logger.info(f"Walk for {oid} on {host} finished with {len(results)} results")
    return results


async def walk_arp_table(host: str, creds: SnmpCredentials) -> list[ArpEntry]:
    logger.info(f"Starting full ARP table walk on {host}")
    phys = await _walk_column(host, creds, ARP_PHYS_OID)
    nets = await _walk_column(host, creds, ARP_NET_OID)
    logger.info(f"ARP walk complete on {host}, phys={len(phys)}, nets={len(nets)}")

    entries: list[ArpEntry] = []
    for suffix, mac_raw in phys.items():
        ip_raw = nets.get(suffix)
        if not ip_raw or ip_raw in ("0.0.0.0", ""):
            continue
        mac = _normalize_mac(mac_raw)
        if mac in ("00:00:00:00:00:00", ""):
            continue
        entries.append(ArpEntry(mac_address=mac, ip_address=_normalize_ip(ip_raw)))

    return entries


async def test_snmp(host: str, creds: SnmpCredentials) -> dict:
    """Test SNMP connectivity by fetching sysDescr.0"""
    engine = SnmpEngine()
    user_data = _build_user_data(creds)
    transport = UdpTransportTarget((host, 161), timeout=5, retries=1)
    context = ContextData()

    try:
        errorIndication, errorStatus, errorIndex, varBinds = await getCmd(
            engine,
            user_data,
            transport,
            context,
            ObjectType(ObjectIdentity("1.3.6.1.2.1.1.1.0")),
        )

        if errorIndication:
            return {"success": False, "error": str(errorIndication)}
        if errorStatus:
            return {"success": False, "error": f"Error status {errorStatus}"}

        for oid, val in varBinds:
            return {
                "success": True,
                "sys_descr": str(val),
                "message": "SNMP connection successful"
            }

        return {"success": True, "message": "Connected but no sysDescr"}
    except Exception as e:
        return {"success": False, "error": str(e)}
