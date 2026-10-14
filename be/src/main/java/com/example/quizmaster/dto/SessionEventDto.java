package com.example.quizmaster.dto;

import java.time.LocalDateTime;

public class SessionEventDto {

    private String type; // e.g., "GAME_STARTED", "GAME_ENDED"
    private String sessionId;
    private String timestamp;

    // Default constructor for serialization
    public SessionEventDto() {
    }

    public SessionEventDto(String type, String sessionId) {
        this.type = type;
        this.sessionId = sessionId;
        this.timestamp = LocalDateTime.now().toString();
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getSessionId() {
        return sessionId;
    }

    public void setSessionId(String sessionId) {
        this.sessionId = sessionId;
    }

    public String getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(String timestamp) {
        this.timestamp = timestamp;
    }
}