// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract AgentRegistry {
    struct AgentInput {
        string name;
        string claimedModel;
        string provider;
        string version;
        string capabilities;
        string endpoint;
        string modelCardUrl;
    }

    struct Agent {
        string name;
        string claimedModel;
        string provider;
        string version;
        string capabilities;
        string endpoint;
        string modelCardUrl;
        bool active;
    }

    mapping(address => Agent) private agents;
    mapping(address => bool) public registered;

    event AgentRegistered(address indexed owner, string name, string claimedModel);
    event AgentProfileUpdated(address indexed owner);

    function register(AgentInput calldata input) external {
        require(!registered[msg.sender], "Agent already registered");
        require(bytes(input.name).length > 0, "Name is required");
        require(bytes(input.claimedModel).length > 0, "Claimed model is required");

        agents[msg.sender] = Agent({
            name: input.name,
            claimedModel: input.claimedModel,
            provider: input.provider,
            version: input.version,
            capabilities: input.capabilities,
            endpoint: input.endpoint,
            modelCardUrl: input.modelCardUrl,
            active: true
        });
        registered[msg.sender] = true;
        emit AgentRegistered(msg.sender, input.name, input.claimedModel);
    }

    function updateProfile(
        string calldata capabilities,
        string calldata endpoint,
        string calldata modelCardUrl
    ) external {
        require(registered[msg.sender], "Agent not registered");
        Agent storage agent = agents[msg.sender];
        agent.capabilities = capabilities;
        agent.endpoint = endpoint;
        agent.modelCardUrl = modelCardUrl;
        emit AgentProfileUpdated(msg.sender);
    }

    function getAgent(address owner) external view returns (Agent memory) {
        require(registered[owner], "Agent not found");
        return agents[owner];
    }
}