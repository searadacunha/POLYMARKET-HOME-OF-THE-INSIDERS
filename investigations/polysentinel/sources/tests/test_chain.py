"""Synthetic ABI fixtures, not evidence of detector accuracy."""
import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from polysentinel.chain import ORDER_V1, ORDER_V2, TRANSFER, decode_order, reconcile, registry, transfers, inspect_receipt
from polysentinel.db import Store
ROOT=Path(__file__).resolve().parents[1]
WALLET='0x'+'1'*40
OTHER='0x'+'2'*40
TX='0x'+'a'*64
BLOCK='0x'+'b'*64

def topic(address): return '0x'+'0'*24+address[2:]
def words(values): return '0x'+''.join(f'{v:064x}' for v in values)
def order(contract,version='v2',token=100,maker=WALLET,taker=OTHER,side=0,size=20_000_000,cash=10_000_000):
    values=([0,token,cash,size,100] if side==0 else [token,0,size,cash,100]) if version=='v1' else [side,token,cash if side==0 else size,size if side==0 else cash,100,0,0]
    return {'address':contract,'topics':[ORDER_V1 if version=='v1' else ORDER_V2,'0x'+'3'*64,topic(maker),topic(taker)],'data':words(values),'blockNumber':'0x64','blockHash':BLOCK,'transactionHash':TX,'logIndex':'0x1','removed':False}

class DecodeTests(unittest.TestCase):
    def setUp(self): self.contracts=registry(ROOT)
    def test_five_exchanges_both_sides_and_fee_assets(self):
        for c in self.contracts['exchanges']:
            for side in (0,1):
                fill=decode_order(order(c['address'],c['abi_version'],side=side),self.contracts)
                self.assertEqual(fill['side'],'BUY' if side==0 else 'SELL')
                self.assertEqual(fill['size'],20)
                self.assertEqual(fill['price'],.5)
                self.assertEqual(fill['token_id'],'100')
                self.assertEqual(fill['fee_asset'],'100' if c['abi_version']=='v1' and side==0 else 'collateral')
    def test_complementary_buy_taker_is_not_sell(self):
        c=self.contracts['exchanges'][2]['address']
        first=decode_order(order(c,token=101,maker=OTHER,taker=WALLET,cash=9_000_000),self.contracts)
        second=decode_order(order(c,token=100,maker=WALLET,taker=c,cash=11_000_000),self.contracts)
        trade=dict(wallet=WALLET,token_id='100',side='BUY',size=20,price=.55)
        self.assertEqual(reconcile(trade,[first])['status'],'unmatched')
        self.assertEqual(reconcile(trade,[first,second])['status'],'matched')
        trade['side']='SELL'
        self.assertEqual(reconcile(trade,[first,second])['status'],'unmatched')
    def test_fragmented_parent_order(self):
        c=self.contracts['exchanges'][2]['address']
        a=decode_order(order(c,size=10_000_000,cash=5_000_000),self.contracts)
        b=copy.deepcopy(a);b['log_index']=2
        result=reconcile(dict(wallet=WALLET,token_id='100',side='BUY',size=20,price=.5),[a,b])
        self.assertEqual(result['status'],'matched')
        self.assertEqual(len(result['order_hashes']),1)
    def test_abi_mismatch_and_truncation_rejected(self):
        c=self.contracts['exchanges'][2]['address']
        log=order(c);log['data']=log['data'][:-2]
        with self.assertRaises(ValueError):decode_order(log,self.contracts)
        log=order(c);log['topics'][0]=ORDER_V1
        with self.assertRaises(ValueError):decode_order(log,self.contracts)
    def test_infrastructure_edge_has_no_ownership(self):
        source=self.contracts['infrastructure'][3]['address']
        log={'address':self.contracts['fungible_tokens'][0]['address'],'topics':[TRANSFER,topic(source),topic(WALLET)],'data':words([1_000_000]),'blockNumber':'0x64','blockHash':BLOCK,'transactionHash':TX,'logIndex':'0x2'}
        edge=transfers({'logs':[log],'transactionHash':TX,'blockHash':BLOCK},WALLET,self.contracts)[0]
        self.assertTrue(edge['infrastructure'])
        self.assertFalse(edge['common_control_inferred'])
        self.assertEqual(edge['amount'],1)

    def test_removed_or_inconsistent_transfer_refused(self):
        log={'address':self.contracts['fungible_tokens'][0]['address'],'topics':[TRANSFER,topic(OTHER),topic(WALLET)],'data':words([1_000_000]),'blockNumber':'0x64','blockHash':BLOCK,'transactionHash':TX,'logIndex':'0x2'}
        receipt={'logs':[log],'transactionHash':TX,'blockHash':BLOCK}
        for field,value in [('removed',True),('transactionHash','0x'+'c'*64),('blockHash','0x'+'d'*64)]:
            altered=copy.deepcopy(receipt);altered['logs'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):transfers(altered,WALLET,self.contracts)

class FakeRPC:
    def __init__(self,receipt,canonical=BLOCK,head=1000):self.receipt,self.canonical,self.head=receipt,canonical,head
    async def request(self,url,method='POST',json_body=None):
        name=json_body['method']
        values={'eth_chainId':'0x89','eth_blockNumber':hex(self.head),'eth_getTransactionReceipt':self.receipt,'eth_getBlockByNumber':{'hash':self.canonical,'timestamp':'0x3e8'}}
        return SimpleNamespace(body={'result':values[name]},evidence_id=name)

class ReceiptTests(unittest.IsolatedAsyncioTestCase):
    async def test_confirmations_reorg_and_historical_proof_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);contracts=registry(ROOT)
            log=order(contracts['exchanges'][2]['address'])
            receipt={'transactionHash':TX,'blockNumber':'0x64','blockHash':BLOCK,'status':'0x1','from':OTHER,'logs':[log]}
            cfg={'root':str(ROOT),'rpc_urls':['https://test.invalid'],'confirmations':128}
            a=await inspect_receipt(store,FakeRPC(receipt,head=110),cfg,TX,WALLET)
            self.assertEqual(a['status'],'pending_confirmations')
            a=await inspect_receipt(store,FakeRPC(receipt),cfg,TX,WALLET)
            self.assertEqual(a['status'],'confirmed')
            a=await inspect_receipt(store,FakeRPC(receipt,canonical='0x'+'c'*64),cfg,TX,WALLET)
            self.assertEqual(a['status'],'reorganized')
            self.assertEqual(store.conn.execute("SELECT COUNT(*) FROM history WHERE kind='receipt'").fetchone()[0],3)
            store.close()
