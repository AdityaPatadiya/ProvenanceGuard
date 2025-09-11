// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Provenance {
    event TemperatureBreachRecorded(string palletId, uint256 timestamp, uint256 temperature);

    function recordBreach(string memory _palletId, uint256 _temperature) public {
        emit TemperatureBreachRecorded(_palletId, block.timestamp, _temperature);
    }
}
