"""Verify the cache overlay actually visible to Agda, then exec the pinned checker."""
import hashlib,json,os,sys
from pathlib import Path
from compression import zstd

r=json.loads(Path(sys.argv[1]).read_text())
p=Path(r['overlay_target']);raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()==r['new_interface_sha256']
assert raw[:24].hex()==r['original_header_hex']
assert hashlib.sha256(zstd.decompress(raw[24:])).hexdigest()==r['decoded_payload_sha256']
assert hashlib.sha256(Path(r['checker_argv'][0]).read_bytes()).hexdigest()==r['checker_binary_sha256']
os.execv(r['checker_argv'][0],r['checker_argv'])
