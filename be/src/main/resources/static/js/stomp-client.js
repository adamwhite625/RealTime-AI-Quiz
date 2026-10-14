/* src/main/resources/static/js/stomp-client.js */

class GameStompClient {
    constructor() {
        this.stompClient = null;
    }

    connect(onConnectedCallback) {
        const socket = new SockJS('/ws');
        this.stompClient = Stomp.over(socket);
        this.stompClient.debug = null; // Disable debug logs

        this.stompClient.connect({}, (frame) => {
            console.log('✅ Connected to WebSocket');
            if (onConnectedCallback) onConnectedCallback(frame);
        }, (error) => {
            console.error('❌ WebSocket Error:', error);
            alert("Connection lost. Please refresh.");
        });
    }

    /**
     * Subscribe to public Game Events (Joins, Next Question, Game Over)
     * Used by BOTH Host and Players.
     */
    subscribeToSession(sessionId, onMessageCallback) {
        this._subscribe(`/topic/session/${sessionId}/players`, onMessageCallback);
    }

    /**
     * Subscribe to private Host Events (Answer Counts, Admin info)
     * Used by HOST ONLY.
     */
    subscribeToHost(sessionId, onMessageCallback) {
        this._subscribe(`/topic/session/${sessionId}/host`, onMessageCallback);
    }

    // Internal helper to avoid code duplication
    _subscribe(topic, callback) {
        if (!this.stompClient || !this.stompClient.connected) {
            console.error("Cannot subscribe: Client not connected.");
            return;
        }
        console.log(`📡 Subscribing to: ${topic}`);
        this.stompClient.subscribe(topic, (message) => {
            const payload = JSON.parse(message.body);
            callback(payload);
        });
    }

    disconnect() {
        if (this.stompClient) this.stompClient.disconnect();
    }
}

const gameSocket = new GameStompClient();