v2_pool_abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "getReserves",
        "outputs": [{
	    "internalType": "uint112",
	    "name": "_reserve0",
	    "type": "uint112"
        }, {
	    "internalType": "uint112",
	    "name": "_reserve1",
	    "type": "uint112"
        }, {
	    "internalType": "uint32",
	    "name": "_blockTimestampLast",
	    "type": "uint32"
        }],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    },  {
	"constant": True,
	"inputs": [],
	"name": "totalSupply",
	"outputs": [{
		"internalType": "uint256",
		"name": "",
		"type": "uint256"
	}],
	"payable": False,
	"stateMutability": "view",
	"type": "function"
    },
     {
        "constant": True,
        "inputs": [{
	    "name": "_owner",
	    "type": "address"
        }],
        "name": "balanceOf",
        "outputs": [{
	    "name": "balance",
	    "type": "uint256"
        }],
        "payable": False,
        "type": "function"
    }
]
