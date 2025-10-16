const MPLib = (() => {
    // --- Overall State ---
    const BORG_LOBBY_ID = 'borg-lobby';
    let config = {};

    // --- Peer Connection State ---
    let peer = null;
    let localPeerId = null;
    let isHost = false;
    const lobbyConnection = new Map();
    const directConnections = new Map();

    // --- Callbacks & Config ---
    const defaultConfig = {
        debugLevel: 0,
        onStatusUpdate: (msg, type) => console.log(`[MPLib] ${msg}`),
        onError: (type, err) => console.error(`[MPLib] Error (${type}):`, err),
        onConnectionChange: (count) => {},
        onRoomDataReceived: (peerId, data) => {},
    };

    // --- Crypto Logic ---
    const SHARED_SECRET = 'a-very-secret-key-that-should-be-exchanged-securely';

    function encrypt(text) {
        return CryptoJS.AES.encrypt(text, SHARED_SECRET).toString();
    }

    function decrypt(ciphertext) {
        const bytes = CryptoJS.AES.decrypt(ciphertext, SHARED_SECRET);
        return bytes.toString(CryptoJS.enc.Utf8);
    }

    function logMessage(message, type = 'info') {
        config.onStatusUpdate(message, type);
    }

    // --- Initialization ---
    function initialize(options = {}) {
        config = { ...defaultConfig, ...options };
        logMessage("Initializing MPLib...", 'info');
        tryToBecomeHost();
    }

    function tryToBecomeHost() {
        logMessage(`Attempting to become the lobby host: ${BORG_LOBBY_ID}`, 'info');
        peer = new Peer(BORG_LOBBY_ID, { debug: config.debugLevel });

        peer.on('open', id => {
            isHost = true;
            localPeerId = id;
            logMessage(`Lobby Host`, 'status');
            config.onStatusUpdate(`Successfully became the lobby host with ID: ${id}`, 'info');
            setupHostListeners();
        });

        peer.on('error', err => {
            if (err.type === 'unavailable-id') {
                logMessage(`Lobby host already exists. Connecting as a client...`, 'info');
                peer.destroy();
                connectAsClient();
            } else {
                config.onError('peer-error', err);
            }
        });
    }

    function connectAsClient() {
        peer = new Peer({ debug: config.debugLevel });
        isHost = false;

        peer.on('open', id => {
            localPeerId = id;
            config.onStatusUpdate(`Peer ID assigned: ${id}.`, 'info');
            connectToLobby();
        });

        peer.on('error', (err) => {
            config.onError('peer-error', err);
        });
    }

    function setupHostListeners() {
        logMessage('Lobby is online. Waiting for direct connections...', 'info');
        peer.on('connection', handleIncomingDirectConnection);
    }

    function connectToLobby() {
        logMessage(`Attempting to connect to lobby peer: ${BORG_LOBBY_ID}`, 'info');
        const conn = peer.connect(BORG_LOBBY_ID, { reliable: true });
        lobbyConnection.set(BORG_LOBBY_ID, conn);

        conn.on('open', () => {
            logMessage(`Connected to lobby`, 'status');
        });

        conn.on('data', data => {
            logMessage(`Discovery data from lobby: ${data.type}`, 'info');
            if (data.type === 'welcome') {
                data.peers.forEach(peerId => connectToPeer(peerId));
            } else if (data.type === 'peer-connect') {
                connectToPeer(data.peerId);
            }
        });

        conn.on('close', () => {
            logMessage('Connection to lobby closed.', 'warn');
            lobbyConnection.delete(BORG_LOBBY_ID);
        });
    }

    function handleIncomingDirectConnection(conn) {
        logMessage(`Incoming direct connection from ${conn.peer}`, 'info');
        if (!directConnections.has(conn.peer)) {
            directConnections.set(conn.peer, conn);
            config.onConnectionChange(directConnections.size);
            conn.on('data', (data) => {
                if (data.type === 'encrypted-message') {
                    try {
                        const decryptedPayload = decrypt(data.payload);
                        const message = JSON.parse(decryptedPayload);

                        if (message.type === 'ping') {
                            logMessage(`Received ping from ${conn.peer}. Sending pong.`, 'info');
                            sendDirectToRoomPeer(conn.peer, { type: 'pong', id: message.id, from: localPeerId });
                            return;
                        }
                        if (message.type === 'pong') {
                             window.dispatchEvent(new CustomEvent('pong', { detail: message }));
                             return;
                        }
                        if (message.type === 'round-robin') {
                            logMessage(`Received round-robin message, step ${message.current_step}`, 'info');
                            message.signatures.push(localPeerId);
                            message.current_step++;
                            const nextPeer = message.route[message.current_step];
                            if (nextPeer) {
                                logMessage(`Forwarding round-robin to ${nextPeer}`, 'info');
                                sendDirectToRoomPeer(nextPeer, message);
                            }
                            return;
                        }
                        config.onRoomDataReceived(conn.peer, message);
                    } catch (e) {
                        logMessage(`Failed to decrypt message from ${conn.peer}: ${e.message}`, 'error');
                    }
                } else {
                    config.onRoomDataReceived(conn.peer, data);
                }
            });
            conn.on('close', () => {
                logMessage(`Direct connection with ${conn.peer} closed.`, 'warn');
                directConnections.delete(conn.peer);
                config.onConnectionChange(directConnections.size);
            });
        }
    }

    function connectToPeer(peerId) {
        if (peerId === localPeerId || directConnections.has(peerId)) {
            return;
        }
        logMessage(`Establishing direct connection to peer: ${peerId}`, 'info');
        const conn = peer.connect(peerId, { reliable: true });

        conn.on('open', () => {
            logMessage(`Direct connection to ${peerId} established.`, 'info');
            handleIncomingDirectConnection(conn);
        });

        conn.on('error', (err) => {
            config.onError('direct-connection', err);
        });
    }

    function broadcastToRoom(data) {
        if (directConnections.size === 0) {
            logMessage('No direct connections available to broadcast.', 'warn');
            return;
        }
        logMessage(`Broadcasting data to ${directConnections.size} peers.`, 'info');
        for (const connection of directConnections.values()) {
            if (connection.open) {
                connection.send(data);
            }
        }
    }

    function sendCodeToEvolvePeer(sourceCode) {
        logMessage('Sending source code to a peer for IPFS pinning...', 'info');
        const data = { type: 'pin-request', payload: sourceCode };
        broadcastToRoom(data);
    }

    function sendDirectToRoomPeer(peerId, data) {
        const conn = directConnections.get(peerId);
        if (conn && conn.open) {
            const encryptedData = encrypt(JSON.stringify(data));
            conn.send({ type: 'encrypted-message', payload: encryptedData });
        } else {
            logMessage(`Could not send direct message to ${peerId}, no connection found.`, 'error');
        }
    }

    return {
        initialize,
        encrypt,
        decrypt,
        sendCodeToEvolvePeer,
        broadcastToRoom,
        sendDirectToRoomPeer,
        getLocalPeerId: () => localPeerId,
        isHost: () => isHost,
        getConnectionCount: () => directConnections.size,
        getDirectConnections: () => Array.from(directConnections.keys()),
    };
})();