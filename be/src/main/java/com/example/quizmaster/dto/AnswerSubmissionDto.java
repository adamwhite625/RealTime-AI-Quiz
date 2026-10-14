package com.example.quizmaster.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AnswerSubmissionDto {

    // 1. INCOMING: Request from the Player
    public static class Request {
        private Long playerId;
        private Long questionId;
        private Long selectedOptionId;

        // Default Constructor
        public Request() {
        }

        public Request(Long playerId, Long questionId, Long selectedOptionId) {
            this.playerId = playerId;
            this.questionId = questionId;
            this.selectedOptionId = selectedOptionId;
        }

        // Getters
        public Long getPlayerId() {
            return playerId;
        }

        public Long getQuestionId() {
            return questionId;
        }

        public Long getSelectedOptionId() {
            return selectedOptionId;
        }

        // Setters (needed for JSON deserialization)
        public void setPlayerId(Long playerId) {
            this.playerId = playerId;
        }

        public void setQuestionId(Long questionId) {
            this.questionId = questionId;
        }

        public void setSelectedOptionId(Long selectedOptionId) {
            this.selectedOptionId = selectedOptionId;
        }
    }

    // 2. OUTGOING (HTTP): Response back to the Player
    public static class Response {
        private String message;
        private int scoreAwarded;
        private int totalScore;
        private boolean isCorrect;

        public Response(String message, int scoreAwarded, int totalScore, boolean isCorrect) {
            this.message = message;
            this.scoreAwarded = scoreAwarded;
            this.totalScore = totalScore;
            this.isCorrect = isCorrect;
        }

        // Getters
        public String getMessage() {
            return message;
        }

        public int getScoreAwarded() {
            return scoreAwarded;
        }

        public int getTotalScore() {
            return totalScore;
        }

        @JsonProperty("isCorrect") // Explicit JSON mapping
        public boolean isCorrect() {
            return isCorrect;
        }

        // Setters (needed for JSON serialization)
        public void setMessage(String message) {
            this.message = message;
        }

        public void setScoreAwarded(int scoreAwarded) {
            this.scoreAwarded = scoreAwarded;
        }

        public void setTotalScore(int totalScore) {
            this.totalScore = totalScore;
        }

        public void setCorrect(boolean correct) {
            isCorrect = correct;
        }
    }

    // 3. OUTGOING (WebSocket): Update sent to the Host
    public static class HostUpdate {
        private String type; // e.g., "ANSWER_RECEIVED"
        private int answersCount; // How many players have answered so far

        public HostUpdate(String type, int answersCount) {
            this.type = type;
            this.answersCount = answersCount;
        }

        public String getType() {
            return type;
        }

        public int getAnswersCount() {
            return answersCount;
        }

        // Setters (needed for JSON serialization)
        public void setType(String type) {
            this.type = type;
        }

        public void setAnswersCount(int answersCount) {
            this.answersCount = answersCount;
        }
    }
}