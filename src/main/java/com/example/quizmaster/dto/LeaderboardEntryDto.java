package com.example.quizmaster.dto;

public class LeaderboardEntryDto {
    private String nickname;
    private int score;

    public LeaderboardEntryDto(String nickname, int score) {
        this.nickname = nickname;
        this.score = score;
    }

    // Getters and Setters
    public String getNickname() {
        return nickname;
    }

    public void setNickname(String nickname) {
        this.nickname = nickname;
    }

    public int getScore() {
        return score;
    }

    public void setScore(int score) {
        this.score = score;
    }
}
