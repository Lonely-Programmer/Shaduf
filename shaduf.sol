pragma solidity ^0.6.0;


interface InterfaceContract {
    //function func(uint) external returns(uint);
   function bind(uint32 cid,address cAlice,address cBob,address cInter,uint16 cChannel1,uint16 cChannel2,address another_contract) external returns(uint);
   function bind_response() external returns(uint);
   function unbind(uint8 cqid,uint8 chan,uint48 amount,uint48 delta,uint32 vcq) external returns(uint);
   function unbind_response(uint8 cqid,uint8 chan,uint48 amount,uint48 delta,uint32 vcq) external returns(uint);
   function parse_check(uint8 bindChar,uint48 bindDelta) external returns(uint);
   function zreceive(uint48 amt) external returns(uint);

   function get_userA() external returns(address);
   function get_userB() external returns(address);
   function get_Inter() external returns(address);
   function get_bindStatus() external returns(uint8);
   function get_bindAmount() external returns(uint48);
   function get_bindDelta() external returns(uint48);
   function get_bindVersion() external returns(uint16);
}


contract work {

   address _zInterfaceAddress;
   InterfaceContract _zcontract;
   //address workInterfaceAddress;
   //Interface dogContract = DogInterface(workInterfaceAddress);
   //dogContract.contracts(_name);

   address _userA;    //Alice's address
   address _userB;    //Bob's address
   address _Inter;
   int8 _bind_response;

   uint8 _channelStatus;    //1 = openReq; 2 = open; 3 = notOpened;
   uint16 _channelID;    //ID of one channel
   uint16 _cChannelID;    //ID of another channel

   uint8 _bindChar;    //1 = trigger; 2 = triggered
   uint8 _bindTran;    //1 = send; 2 = receive
   uint8 _bindStatus;    //1 = bind; 2 = bindReq; 3 = unbindReq
   address _bindAddr;    //address of another channel

   //bind status in this round
   uint32 _bindID;    //ID of 2 channels
   uint48 _bindAmount;
   uint48 _bindDelta;
   uint32 _bindVersion;

   //status in this round
   uint48 _balA;    // Alice's balance
   uint48 _balB;    // Bob's balance
   uint48 _balD;
   uint48 _fund;    // total fund
   uint32 _state_version;    //state version

   uint _timeout;
   uint _offset;
   uint _response;    //1 = Alice, 2 = Bob, 4 = Inter
   uint _response2;    //1 = Alice, 2 = Bob


   //function zcall(address addr, uint value) public returns(uint){
   //     InterfaceContract interfaceContract = InterfaceContract(addr);
   //     return interfaceContract.func(value);
   // }

   // getting functions
   function get_userA() public returns(address){
      return _userA;
   }
   function get_userB() public returns(address){
      return _userB;
   }
   function get_Inter() public returns(address){
      return _Inter;
   }
   function get_bindStatus() public returns(uint8){
      return _bindStatus;
   }
   function get_bindAmount() public returns(uint48){
      return _bindAmount;
   }
   function get_bindDelta() public returns(uint48){
      return _bindDelta;
   }
   function get_bindVersion() public returns(uint32){
      return _bindVersion;
   }

   function func(uint n, uint[] memory z) public returns(uint){
      uint[] memory value = new uint[](10);
   }

   function open(uint16 id,address Alice,address Bob,uint48 cash) public returns(uint){ // invoke channel opening
      _channelID = id;
      _userA = Alice;
      _userB = Bob;
      _channelStatus = 1;
      _balA = cash;
      _timeout = now + 1 minutes;
      _bindStatus = 0;
      _offset = 0;
      //emit
   }

   function open_response(uint48 cash) public returns(uint){ // respond channel opening
      if(msg.sender != _userB || _channelStatus != 1 || now > timeout) {
         _balB = cash;
         _fund = _balA + _balB;
         _channelStatus = 2;
         //emit
      }
   }

   function open_timeout() public returns(uint) { // time out when opening
      if(msg.sender == _userA && _channelStatus == 1 && now > timeout) {
         //send
         //emit
      }
   }

   function bind(uint32 cid,address cAlice,address cBob,address cInter,uint16 cChannel1,uint16 cChannel2,address another_contract) public returns(uint){ // invoke channel binding
      if(_bindStatus != 0 || (_bindStatus == 2 && now > _timeout) {
         return 2;
      }
      if(uint32(cChannel1) * 65536 + uint32(cChannel2) != cid) {
         return 3;
      }
      if(cChannel1 >= cChannel2) {
         return 4;
      }
      if(_channelID == cChannel2) {
         _cChannelID = cChannel1;
         _bindAddr = msg.sender;
      }
      else {
         _cChannelID = cChannel2;
         _bindAddr = msg.sender;
      }
      if(cInter != _userA && cInter != _userB) {
         return 5;
      }

      _zInterfaceAddress = another_contract;
      _zcontract = InterfaceContract(another_contract);

      //?
      //msg.sender.call(keccak256());
      //call
      //call
      _bindTran = 0;
      _bindDelta = 0;
      _bindAmount = 0;
      _bindVersion = 0;
      //

      if(_channelID == cChannel1) {    //trigger
         if(msg.sender != cInter) {
            return 8;
         }
         //
         _bindChar = 1;
         _timeout = now + 1 minutes;
         _bindStatus = 2;
         _response &= 3;
         return _zcontract.bind(cid,cAlice,cBob,cInter,cChannel1,cChannel2,address(this)) + 100;
      }
      else if(_channelID == cChannel2) {
         _bindChar = 2;
         _bindStatus = 2;
         _timeout = now + 1 minutes;
         return 20;
      }
      return 30;
   }

   function bind_response() public returns(uint){ // respond bind
      if(_bindStatus != 2 || now > timeout) {
         return 2;
      }
      if(_bindChar == 1) {
         if(msg.sender != _userA && msg.sender != _userB) {
            return 3;
         }
         if(msg.sender == _userA) {
            _response -= 1;
         }
         else{
            _response -= 2;
         }
         if(_response == 0) {
            _bindStatus = 3;
         }
         _zcontract.bind_response();
      }
      else {
         if(msg.sender != _zInterfaceAddress) {
            return 4;
         }
         if(_zcontract.get_bindStatus() != 2) {
            return 5;
         }
         _bindStatus = 3;
      }
   }

   function unbind(uint8 cqid,uint8 chan,uint48 amount,uint48 delta,uint32 vcq) public returns(uint){ // invoke channel unbinding
      if(cqid==1 || true) {
         amount += delta;
         delta == amount;
      }
      //return 1;

      if(_bindStatus != 3) {
         if(_channelStatus != 0 || _channelStatus != 1) {

         }
         _channelStatus = 2;
         _timeout = 100;
         _bindAmount = 2;
         _bindDelta = 3;
         _bindVersion = 4;
         return 2;
      }

      if(_bindChar == 1) {
         if(cqid != _bindID || chan == cqid) {
            return 3;
         }
         //sign
         if(msg.sender != _userA && msg.sender != _userB && msg.sender != _Inter) {
            return 4;
         }
         _bindVersion = vcq;
         _bindDelta = delta;
         _bindAmount = amount;

         if(msg.sender == _userA) {
            _response = 6;
         }
         else if(msg.sender == _userB) {
            _response = 5;
         }
         else if(msg.sender == _Inter) {
            _response = 3;
         }
         _bindStatus = 4;

         _timeout = now + 1 minutes;
         //check
      }
      else if(_bindChar == 2) {
         //sender
         if(msg.sender != _bindAddr) {
            return 8;
         }
         //invoke[]
         _bindVersion = 2;
         _bindDelta = 2;
         _bindAmount = 2;
         _bindStatus = 0;
         if(_bindTran == 1) {
            _zcontract.zreceive(delta);
         }
      }

   }

   function parse_check(uint8 bindChar,uint48 bindDelta) public returns(uint) { // parse data
      if(bindChar == 1 && bindDelta < 0 || bindChar == 2 && bindDelta > 0) {
         if(!(bindDelta > -_fund && bindDelta < _fund)) {
            return 2;
         }
         _bindTran = 1;
      }
      if(bindChar == 1 && bindDelta > 0 || bindChar == 2 && bindDelta < 0) {
         if(!(bindDelta > -fund && bindDelta < fund)) {
            return 3;
         }
         _bindTran = 2;
      }
   }

   function unbind_response(uint8 cqid,uint8 chan,uint48 amount,uint48 delta,uint32 vcq) public returns(uint){ // respond channel unbinding
      if(_bindStatus != 4 || _bindChar != 2 || now > timeout) {
         return 2;
      }
      if(!(msg.sender == _userA && _response2 == 1 || msg.sender == _userB && _response2 == 2)) {
         return 3;
      }
      if(cqid != _bindID || chan == cqid) {
         return 4;
      }
      //sign
      if(vcq > _bindVersion) { // update bind
         _bindDelta = delta;
         _bindAmount = amount;
         parse_check(1,1);
      }

      _response -= 2;
      if(_response == 0) {
         _bindStatus = 0;
         _zcontract.unbind(cqid,chan,amount,delta,vcq);
         if(_bindTran == 1) {
            _fund -= _bindDelta;
            _zcontract.zreceive(delta);
         }
      }
   }

   function unbind_timeout() public returns(uint) { // time out when unbinding
      if(_bindStatus != 5 || _bindTran != 1|| now > timeout) {
         return 2;
      }
      _bindStatus = 0;
      _zcontract.unbind(1,2,3,4,5);
      if(_bindTran == 2) {
         _fund -= _bindDelta;
         _zcontract.zreceive(1);
      }
   }

   function zreceive(uint48 amt) public returns(uint) {
      if(_bindTran != 2) {
         return 2;
      }
      if(msg.sender != _bindAddr) {
         return 3;
      }
      _fund += amt;
      //emit
   }

   function close(uint48 ba,uint48 bb,uint16 vs,uint32 cid,uint32 vcq) public returns(uint) { // invoke channel closing
      if(msg.sender != _userA && msg.sender != _userB) {
         return 2;
      }
      if(vs != 0) {
         //sign
      }
      _state_version = vs;
      _bindID = cid;
      _bindVersion = vcq;
      _balA = ba;
      _balB = bb;
      if(msg.sender == _userA) {
         _response2 = 1;
      }
      else {
         _response2 = 2;
      }
      _timeout = now + 3 minutes;
      _channelStatus = 6;
      //emit
   }

   function close_response(uint48 bA,uint48 bB,uint16 vs,uint32 cid,uint32 vcq) public returns(uint){ // respond  channel closing
      if(_channelStatus != 6 || now > time) {
         return 2;
      }
      //
      //sign
      if(vs > _state_version) {
         _state_version = vs;
         _bindID = cid;
         _bindVersion = vcq;
         _balA = bA;
         _balB = bB;
      }
      if(_bindStatus == 0) {
         if(_bindID == _bindID && _bindVersion == _bindVersion - 1) {
            _balD += _bindAmount;
         }
         //send
         //send
         //emit
      }
   }

   function close_timeout() public returns(uint) { // time out when channel closing
      if(_channelStatus != 6 || now > time) {
         return 2;
      }
      if(_bindStatus != 0) {
         return 3;
      }
      //send
      //send
      //emit
   }

   function bind_update(uint48 amt,uint48 delta,uint32 cv,bytes memory sig) public returns(uint)  { // update bind
      _bindAmount = amt;
      _bindDelta = delta;
      _bindVersion = cv;
      //sign
      //bytes memory b;
      //b = new bytes(6+6+4);
      //assembly { mstore(add(b, 32), amt) }
      //assembly { mstore(add(b, 80), delta) }
      //assembly { mstore(add(b, 128), cv) }
      //return verify_sgn(b,sig,msg.sender);
   }

   function state_update(uint48 ba,uint48 bb,uint48 amt,uint48 delta) public returns(uint) { // update state
      _balA = ba; // update balance
      _balB = bb;
      _state_version += 1;

      _bindAmount = amt; // update bind
      _bindDelta = delta;
      _bindVersion += 1;
   }

   function v1(uint8 a,uint8 b,uint48 c,uint48 d,bytes memory sig) public returns(uint) {
      return verify_sgn(abi.encodePacked(a,b,c,d),sig,_userA);
   }

   function v2(uint8 a,uint8 b,uint48 c,uint48 d,uint32 e,bytes memory sig) public returns(uint) {
      return verify_sgn(abi.encodePacked(a,b,c,d,e),sig,_userA);
   }

   function verify_sgn(bytes memory data,bytes memory sig,address ad) public returns(uint) {   // verify signature
      bytes32 data_hash = keccak256(data);
      address input_addr = recover(data_hash,sig);
      if(input_addr != ad) {
         return 0;
      }
      return 1;
   }

   function recover(bytes32 hash, bytes memory sig) public pure returns (address) {
      bytes32 r;
      bytes32 s;
      uint8 v;

      //Check the signature length
      if (sig.length != 65) {
         return (address(0));
      }

      // Divide the signature in r, s and v variables
      assembly {
         r := mload(add(sig, 32))
         s := mload(add(sig, 64))
         v := byte(0, mload(add(sig, 96)))
      }

      // Version of signature should be 27 or 28, but 0 and 1 are also possible versions
      if (v < 27) {
         v += 27;
      }

      // If the version is correct return the signer address
      if (v != 27 && v != 28) {
         return (address(0));
      }
      else {
         return ecrecover(hash, v, r, s);
      }
   }

   function zcheck(address ad) public returns(uint) { // check whether the contract has the same code as this one
      bytes memory i_code;
      bytes memory o_code;
      uint size_i;
      uint size_o;

      assembly {
         size_i := codesize()
         size_o := extcodesize(ad)
      }
      i_code = new bytes(size_i);
      o_code = new bytes(size_o);
      assembly {
         i_code := mload(0x40)
         mstore(0x40, add(i_code, and(add(add(size_i, 0x20), 0x1f), not(0x1f))))
         mstore(i_code, size_i)
         extcodecopy(ad, add(i_code, 0x20), 0, size_i)

         o_code := mload(0x40)
         mstore(0x40, add(o_code, and(add(add(size_o, 0x20), 0x1f), not(0x1f))))
         mstore(o_code, size_o)
         extcodecopy(ad, add(o_code, 0x20), 0, size_o)
      }
      if(keccak256(i_code) == keccak256(o_code)) {
         return 1;
      }
      return 0;
   }
}