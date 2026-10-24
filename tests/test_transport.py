import unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/maimai-no-drink/scripts'))
from mcp_readonly import Client,NoRedirect,credentials
class TransportTests(unittest.TestCase):
 def test_write_tool_blocked_before_network(self):
  client=Client.__new__(Client)
  client.call=lambda *a: self.fail('Network should not be reached')
  with self.assertRaises(ValueError):client.tool('create-order',{})
 def test_redirect_blocked(self):
  with self.assertRaises(ValueError):NoRedirect().redirect_request(None,None,302,'',{},'https://example.com')
 def test_env_auth(self):
  with patch.dict('os.environ',{'MCD_MCP_TOKEN':'test-only-placeholder'}):self.assertEqual(credentials(),'Bearer test-only-placeholder')
 def test_mcp_tool_error_rejected(self):
  client=Client.__new__(Client);client.call=lambda *a:{'result':{'isError':True}}
  with self.assertRaises(ValueError):client.tool('calculate-price',{})
