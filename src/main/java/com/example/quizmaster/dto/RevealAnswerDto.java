package com.example.quizmaster.dto;

import java.util.List;

public class RevealAnswerDto {
    private String type = "REVEAL_ANSWER";
    private Long correctOptionId;
    private List<LeaderboardEntryDto> leaderboard;

    public RevealAnswerDto(Long correctOptionId, List<LeaderboardEntryDto> leaderboard) {
        this.correctOptionId = correctOptionId;
        this.leaderboard = leaderboard;
    }

    // Getters and Setters
    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public Long getCorrectOptionId() {
        return correctOptionId;
    }

    public void setCorrectOptionId(Long correctOptionId) {
        this.correctOptionId = correctOptionId;
    }

    public List<LeaderboardEntryDto> getLeaderboard() {
        return leaderboard;
    }

    public void setLeaderboard(List<LeaderboardEntryDto> leaderboard) {
        this.leaderboard = leaderboard;
    }
}
