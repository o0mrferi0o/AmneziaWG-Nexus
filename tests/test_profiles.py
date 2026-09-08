from app.services import discover_profiles

VALID="""[Interface]\nPrivateKey = secret\nAddress = 10.0.0.2/24\n[Peer]\nPublicKey = public\nAllowedIPs = 0.0.0.0/0\nEndpoint = example.org:51820\n"""
def test_discovery_and_validation(tmp_path):
    (tmp_path/"good.conf").write_text(VALID); (tmp_path/"bad.conf").write_text("[Interface]\nAddress=x")
    profiles=discover_profiles(tmp_path)
    assert [p.name for p in profiles]==["bad","good"]
    assert profiles[1].endpoint=="example.org:51820" and not profiles[0].valid
